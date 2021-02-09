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
              ./patch.py -c sumaconf.yaml -g testgroup
              ''')) 
parser.add_argument("-c", "--config", help="Enter your suse manager host login config file name", required=True)
parser.add_argument("-g", "--group_name", help="Enter a valid groupname. e.g. DEV-SLES15SP2 ",  required=True)

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

#nowlater = datetime.now() + timedelta(hours=int(1))
nowlater = datetime.now()
earliest_occurrence = xmlrpclib.DateTime(nowlater)
allgroups = session_client.systemgroup.listAllGroups(session_key)

joblist = []
joblist_reboot = []
nested_dict = lambda: defaultdict(nested_dict)
jobsdict = nested_dict
jobsdict = {}
error1 = 0
    
def json_write(mydict):
        with open("joblist_patches.json", "w") as write_file:
            json.dump(mydict, write_file,  indent=4)

if args.group_name:
    grpfound = 'false'
    for a in allgroups:
        
        if a['name'] == args.group_name:
            print("Targeting group name: %s with %s systems." %(a['name'],  str(a['system_count'])))
            grpfound = 'true'
            try:
                activesystemlist = session_client.systemgroup.listActiveSystemsInGroup(session_key, args.group_name)
                print("activesystemlist is: %s" %(activesystemlist))
            except:
                error1 = 1
                print("uups something went wrong. We could not find the active systems in the given group name. Maybe the group is empty.")
            break
    
    if grpfound == 'false':
        print("sorry we could not find the group you provided. Check if it exists or case-sensitive name correctness.")
        sys.exit(1)
    
    
    for e in activesystemlist:
        system_erratalist = []
        erratalist = session_client.system.getRelevantErrata(session_key, e)
        if len(erratalist) == 0:
            system_name = session_client.system.getName(session_key, e)
            print("All good. No patch needed:\t %s" %(system_name['name']))
            continue
            
        for s in erratalist:    
            system_erratalist.append(s['id'])
            
        try:
            system_actionid = session_client.system.scheduleApplyErrata(session_key, e,  system_erratalist,  earliest_occurrence)
        except:
            system_name = session_client.system.getName(session_key, e)
            print("\tCreating patch Job for %s failed. Maybe another job for this system is already scheduled." %(system_name['name']))
            continue  


        del system_erratalist
        system_name = session_client.system.getName(session_key, e)
        jobsdict[system_name['name']]={}
        jobsdict[system_name['name']]['Patch_jobs']  = {}
        jobsdict[system_name['name']]['serverid']= e
        jobsdict[system_name['name']]['time'] = nowlater.strftime("%d/%m/%Y, %H:%M:%S")

        for s in system_actionid: 
            jobsdict[system_name['name']]['Patch_jobs'] = s
            print("Job ID %s for %s %s has been created" %(str(system_actionid),  (str(e)), system_name['name']))
            

if error1 != 1:
    json_write(jobsdict)
session_client.auth.logout(session_key)




            
