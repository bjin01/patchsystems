#!/usr/bin/python
from xmlrpc.client import ServerProxy, DateTime
import yaml
import os
import argparse,  getpass,  textwrap,  json, time, sys
from collections import defaultdict
from datetime import datetime
from copy import deepcopy

class Password(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        if values is None:
            values = getpass.getpass()
        setattr(namespace, self.dest, values)

parser = argparse.ArgumentParser()
#parser.add_argument("-v", "--verbosity", action="count", default=0)
parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
This scripts queries job status by passing jobstatus json formatted file with jobid and serverid. 
Sample command:
              python3.6 jobstatus.py -c /root/suma_config.yaml -f ./jobs.json -o /var/log/jobstatus_list.log\n \
Check Job status of the systems. The output will be shown in terminal and written to a local file 'jobstatus_list.log' ''')) 

parser.add_argument("-c", "--config", help="enter the config file name that contains login information e.g. /root/suma_config.yaml",  required=False)
parser.add_argument("-f", "--jsonfile", help="Enter the json file name inluding path. e.g. ~/user/joblist.json ",  required=True)
parser.add_argument("-o", "--output_file", help="Enter the output file name inluding path. e.g. /var/log/jobstatus_list.log ",  required=False)
args = parser.parse_args()


nested_dict = lambda: defaultdict(nested_dict)
jobsdict = nested_dict
jobsdict = {}
status_update_dict = {}
now = datetime.now()
earliest_occurrence = DateTime(now)
dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
final_status = {}


def get_login(path):
    
    if path == "":
        path = os.path.join(os.environ["HOME"], "suma_config.yaml")
    with open(path) as f:
        login = yaml.load_all(f, Loader=yaml.FullLoader)
        for a in login:
            login = a

    return login

def login_suma(login):
    MANAGER_LOGIN = login['suma_user']
    MANAGER_PASSWORD = login['suma_password']
    SUMA = "http://" + login['suma_user'] + ":" + login['suma_password'] + "@" + login['suma_host'] + "/rpc/api"
    with ServerProxy(SUMA) as session_client:
        session_key = session_client.auth.login(MANAGER_LOGIN, MANAGER_PASSWORD)
    return session_client, session_key

def suma_logout(session, key):
    session.auth.logout(key)
    return

def write_status(job_status_list):

    for z in job_status_list:
        #print(z)
        print_srv_name = '{0: <30}'.format(z['server_name'])
        final_status[z['server_name']] = {}
        for i,  j in z.items():
            if 'jobs' in i:
                final_status[z['server_name']]['type'] = i
                
                for a in j:
                    for x, y in a.items():
                        final_status[z['server_name']]['jobid'] =  x
                        final_status[z['server_name']]['status'] = y
                        #print(x, y)
                        if final_status[z['server_name']]['status'] == "failed":
                            print_j_status = '\033[91m{0: >10}\033[00m'.format(final_status[z['server_name']]['status'])
                        if final_status[z['server_name']]['status'] == "completed":
                            print_j_status = '\033[94m{0: >10}\033[00m'.format(final_status[z['server_name']]['status'])
                        if final_status[z['server_name']]['status'] == "in_progress":
                            print_j_status = '\033[93m{0: >10}\033[00m'.format(final_status[z['server_name']]['status'])
                        print_jobid = '{0: <10}'.format(final_status[z['server_name']]['jobid'])

                        print("%s %s %s %s" %(print_srv_name, print_jobid, final_status[z['server_name']]['type'], print_j_status))

                        if args.output_file:
                            with open(args.output_file, "a") as write_file:
                                write_file.write(print_srv_name + '\t' + final_status[z['server_name']]['type'] + '\t' + y + '\t' +  print_j_status + '\n')

def get_status(jobid, serverid):
    #print("jobid: {}, serverid: {}".format(jobid, serverid))
    status = "unknown"
    progress_list = session.schedule.listInProgressSystems(key, int(jobid))
    for a in progress_list:
        if a['server_id'] == serverid:
            return "in_progress"
    completed_list = session.schedule.listCompletedSystems(key, int(jobid))
    for a in completed_list:
        if a['server_id'] == serverid:
            return "completed"
    failed_list = session.schedule.listFailedSystems(key, int(jobid))
    for a in failed_list:
        if a['server_id'] == serverid:
            return "failed"
    
    return status



""" def trigger_reboot(serverid):
    needRebootSystems = session.system.listSuggestedReboot(key)
    #print("Checking if system need reboot via api.")
    reboot_jobid = 0
    
    for a in needRebootSystems:
        if a['id'] == serverid:
            if "needReboot_jobs" not in copy_jobstatus_dict[a['name']]:
                try:
                    reboot_jobid = session.system.scheduleReboot(key, serverid, earliest_occurrence)
                except:
                    print("uups, creating a reboot job failed.")
                if reboot_jobid != 0:
                    temp_dict = { 'needReboot_jobs': { reboot_jobid: 'pending' } }
                    copy_jobstatus_dict[a['name']].update(temp_dict)
                    json_write(copy_jobstatus_dict)
                    #jobstatus_dict[a['name']]['Reboot_jobs'].update(reboot_jobid = 'pending')
                    print("A reboot job: %s \tfor %s has been created." %(str(reboot_jobid), a['name']))
                break
    return reboot_jobid """

def json_write(mydict):
        with open("joblist.json", "w") as write_file:
            json.dump(mydict, write_file,  indent=4)

def main_loop():
    while 1:
        if args.output_file:
            with open(args.output_file, "w") as write_file:
                write_file.write('Job Output: \t ' + dt_string + '\n')

        with open(args.jsonfile, "r") as r_file:
            jobstatus_dict = json.load(r_file)

        print("\n\033[96mJob Status:\033[00m")
        print('{0: <30}'.format('System Name') + '{0: <10}'.format('JobID') + '{0: >15}'.format('Job Status' ))
        print('-----------------------------------------------------------------------------------------')
        if args.output_file:
            with open(args.output_file, "a") as write_file:
                write_file.write("\nPatch Job Status:\n")
        
        job_status_list = []
        for k, v in jobstatus_dict.items():
            #print(k, v)
            job_status_per_node = {}
            jobid_list = []
            jobstatus = None
            job_status_per_node["server_name"] = k
            #print("v[serverid]: {}".format(v["serverid"]))
            job_status_per_node["serverid"] = v["serverid"]
            for a,  b in v.items():
                if 'jobs' in a:
                    job_status_per_node[a] = []
                    for jobid, jobstatus in b.items():
                        jobid_status = {}
                        jobstatus = get_status(jobid, job_status_per_node["serverid"])
                        jobid_status[str(jobid)] = jobstatus
                        job_status_per_node[a].append(jobid_status)
            job_status_list.append(job_status_per_node)
        
        write_status(job_status_list)

        
        if args.output_file:
            print("You can find the job status log in {}".format(args.output_file))
        
        time.sleep(5)

if __name__ == '__main__':
    if args.config:
        suma_data = get_login(args.config)
        session, key = login_suma(suma_data)
        print("SUMA Login successful.")
    else:
        conf_file = "/root/suma_config.yaml"
        suma_data = get_login(conf_file)
        session, key = login_suma(suma_data)
        print("SUMA Login successful.")
    try:
        with open(args.jsonfile, "r") as r_file:
            jobstatus_dict = json.load(r_file)

        copy_jobstatus_dict = deepcopy(jobstatus_dict)
        main_loop()
    except KeyboardInterrupt:
        suma_logout(session, key)
        print >> sys.stderr, '\nExiting by user request.\n'
        sys.exit(0)