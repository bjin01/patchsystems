#!/usr/bin/python
import xmlrpclib,  argparse,  getpass,  textwrap,  json, sys
import os
import yaml
from datetime import datetime,  timedelta
from collections import defaultdict
#from array import *

def read_config(conf_file):
    if os.path.isfile(conf_file):
        with open(conf_file) as c_file:
            parsed_yaml_file = yaml.load(c_file, Loader=yaml.FullLoader)
        return parsed_yaml_file

class Password(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        if values is None:
            values = getpass.getpass()
        setattr(namespace, self.dest, values)

parser = argparse.ArgumentParser()

parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
This scripts schedules patch deployment jobs for given group's systems' in given hours from now on. A reboot will be scheduled as well. 
Sample command:
              ./reboot.py -c sumaconf.yaml -f joblist_patches.json -o joblist_reboot.json
              ''')) 
parser.add_argument("-c", "--config", help="Enter your suse manager host login config file name", required=True)
parser.add_argument("-f", "--file_name", help="Enter a valid job file name. e.g. myjoboutput.txt ",  required=True)
parser.add_argument("-o", "--output_file", help="Enter a file name to store reboot job outputs. e.g. rebootjobs.txt ",  required=True)

args = parser.parse_args()

suma_conf = {}
if args.config:
    suma_conf = read_config(args.config)
    
    MANAGER_URL = "http://"+ suma_conf["server"] +"/rpc/api"
    MANAGER_LOGIN = suma_conf["user"]
    MANAGER_PASSWORD = suma_conf["password"]
else:
    print("No suma config file provided.")
    sys.exit(1)


session_client = xmlrpclib.Server(MANAGER_URL, verbose=0)
session_key = session_client.auth.login(MANAGER_LOGIN, MANAGER_PASSWORD)

nowlater = datetime.now() + timedelta(hours=int(1))
earliest_occurrence = xmlrpclib.DateTime(nowlater)

data = []
nested_dict = lambda: defaultdict(nested_dict)
jobsdict = nested_dict
jobsdict = {}
all_jobs = []
jobsoutput = []

def json_write(mydict, outputfile):
        with open(outputfile, "w") as write_file:
            json.dump(mydict, write_file,  indent=4)

def read_jsonfile(f):
    data = []
    if os.path.isfile(f):
        with open(f) as json_file:
            try:
                data = json.load(json_file)
                return data
            except ValueError as err:
                print("no json object found: %s" % err)
                return data
    else:
        return data

def check_patch_status(serverid, patchid):
    if str(serverid) != "" and str(patchid) != "":
        output_completed = session_client.schedule.listCompletedSystems(session_key, patchid)
        for i in output_completed:
            if i['server_id'] == serverid:
                status = "completed"
                return status
        
        output_failed = session_client.schedule.listFailedSystems(session_key, patchid)
        for i in output_failed:
            if i['server_id'] == serverid:
                status = "failed"
                return status       

        output_pending = session_client.schedule.listInProgressSystems(session_key, patchid)
        for i in output_pending:
            if i['server_id'] == serverid:
                status = "pending"
                return status  


def schedule_reboot(serverid):
    if str(serverid) != "":
           reboot_jobid = session_client.system.scheduleReboot(session_key, serverid,  earliest_occurrence)

    if reboot_jobid:
        jobs = {}
        system_name = session_client.system.getName(session_key, serverid)
        print("Reboot Job ID %s for %s %s has been created" %(str(reboot_jobid),  (str(serverid)), system_name['name']))
        jobs[system_name['name']] = {}
        jobs[system_name['name']]['serverid'] = serverid
        jobs[system_name['name']]['Reboot_jobs'] = reboot_jobid
        jobs[system_name['name']]['time'] = nowlater.strftime("%d/%m/%Y, %H:%M:%S")
        return jobs
    else:
        print("No reboot id found. Exit with error.")
        sys.exit(1)
    
def check_reboot_already(reboot_job_file, serverid):
    if os.path.isfile(reboot_job_file) and str(serverid) != "":
        reboot_data = read_jsonfile(reboot_job_file)
        #print("reboot_data %s" % reboot_data)
        if len(reboot_data) != 0:
            for i in reboot_data:
                for _, b in i.items():
                    if isinstance(b, dict):
                        #print("lets see b %s" % b)
                        if b["serverid"] == serverid:
                            #print("match reboot serverid found")
                            return 1
                       
                         


if args.file_name and os.path.isfile(args.file_name):
   
    data = read_jsonfile(args.file_name)
else:
    print("ops, you didn't provider file name that contains job information from the minions. Or the file is empty. Exit with error")
    sys.exit(1)

if len(data) != 0:
    for a, b in data.items():
        if isinstance(b, dict):
            if str(b["serverid"]) != "" and str(b["Patch_jobs"]) != "":
                #print("%s: %s %s" %(b["serverid"], b["Patch_jobs"], b["time"]))
                status = check_patch_status(b["serverid"], b["Patch_jobs"])
                print("patch status: %s" % status)
                if status == "completed":
                    if args.output_file:
                        #print("serverid to search for reboot or not %s" %b["serverid"])
                        already_rebooted = check_reboot_already(args.output_file, b["serverid"])
                        #print("already_rebooted %s" % already_rebooted)
                        if already_rebooted == None or already_rebooted == 0:
                            jobsoutput = schedule_reboot(b["serverid"])
                            all_jobs.append(jobsoutput)
                        else:
                            print("%s is being rebooted or already rebooted." % a)

if len(all_jobs) != 0:
    if args.output_file:
        if all_jobs:
            json_write(all_jobs, args.output_file)
    else:
        print("No output file provided.")
        sys.exit(1)