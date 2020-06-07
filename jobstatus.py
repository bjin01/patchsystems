#!/usr/bin/python
import xmlrpclib,  argparse,  getpass,  textwrap,  json, time, sys
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
              python jobstatus.py -s bjsuma.bo2go.home -u bjin -p suse1234 -f ./joblist.json -o /var/log/jobstatus_list.log\n \
Check Job status of the systems. The output will be shown in terminal and written to a local file 'jobstatus_list.log' ''')) 

parser.add_argument("-s", "--server", help="Enter your suse manager host address e.g. myserver.abd.domain",  default='localhost',  required=True)
parser.add_argument("-u", "--username", help="Enter your suse manager loginid e.g. admin ", default='admin',  required=True)
parser.add_argument('-p', action=Password, nargs='?', dest='password', help='Enter your password',  required=True)
parser.add_argument("-f", "--jsonfile", help="Enter the json file name inluding path. e.g. ~/user/joblist.json ",  required=True)
parser.add_argument("-o", "--output_file", help="Enter the output file name inluding path. e.g. /var/log/jobstatus_list.log ",  required=False)
args = parser.parse_args()

MANAGER_URL = "http://"+ args.server+"/rpc/api"
MANAGER_LOGIN = args.username
MANAGER_PASSWORD = args.password
session_client = xmlrpclib.Server(MANAGER_URL, verbose=0)
session_key = session_client.auth.login(MANAGER_LOGIN, MANAGER_PASSWORD)
nested_dict = lambda: defaultdict(nested_dict)
jobsdict = nested_dict
jobsdict = {}
status_update_dict = {}
now = datetime.now()
earliest_occurrence = xmlrpclib.DateTime(now)
dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
final_status = {}
        
def write_status():
    #print(tabulate([status_update_dict], headers=['Server_Name', 'Job_Type',  'JobID',  'Status']))
    print_srv_name = '{0: <30}'.format(status_update_dict['servername'])
    for i,  j in status_update_dict.iteritems():
            if i == 'servername':
                srv_name = str(j)
            if i == 'JobID':
                jobid = j 
            if i == 'Job_Status':
                j_status = j
            if i == 'Job_Type':
                j_type = j
    final_status[srv_name] = {}
    final_status[srv_name]['type'] =  j_type
    final_status[srv_name]['jobid'] =  jobid
    final_status[srv_name]['status'] = j_status
    if final_status[srv_name]['status'] == "failed":
        print_j_status = '\033[91m{0: >10}\033[00m'.format(final_status[srv_name]['status'])
    if final_status[srv_name]['status'] == "completed":
        print_j_status = '\033[94m{0: >10}\033[00m'.format(final_status[srv_name]['status'])
    if final_status[srv_name]['status'] == "in_Progress":
        print_j_status = '\033[93m{0: >10}\033[00m'.format(final_status[srv_name]['status'])
    print_jobid = '{0: <10}'.format(final_status[srv_name]['jobid'])
    print("%s %s %s "  %(print_srv_name, print_jobid, print_j_status))
    if args.output_file:
        with open(args.output_file, "a") as write_file:
            write_file.write(print_srv_name + '\t' + j_type + '\t' + jobid + '\t' +  j_status + '\n')

def inprogress(jobid, serverid,  job_type):
    progress_list = session_client.schedule.listInProgressSystems(session_key, jobid)
    for a in progress_list:
        if a['server_id'] == serverid:
            status_update_dict['servername'] = a['server_name']
            status_update_dict['JobID'] = str(jobid)
            status_update_dict['Job_Status'] = 'in_Progress'
            status_update_dict['Job_Type'] = job_type
            write_status()
            return 1
            break
    return 0

def completed(jobid, serverid,  job_type):
    completed_list = session_client.schedule.listCompletedSystems(session_key, jobid)
    for a in completed_list:
        if a['server_id'] == serverid:
            status_update_dict['servername'] = a['server_name']
            status_update_dict['JobID'] = str(jobid)
            status_update_dict['Job_Status'] = 'completed'
            status_update_dict['Job_Type'] = job_type
            if "Patch_jobs" in job_type:
                trigger_reboot(serverid)
            write_status()
            return 1
            break
    return 0

def failed(jobid, serverid,  job_type):
    failed_list = session_client.schedule.listFailedSystems(session_key, jobid)
    for a in failed_list:
        if a['server_id'] == serverid:
            status_update_dict['servername'] = a['server_name']
            status_update_dict['JobID'] = str(jobid)
            status_update_dict['Job_Status'] = 'failed'
            status_update_dict['Job_Type'] = job_type
            write_status()
            return 1
            break
    return 0

def trigger_reboot(serverid):
    needRebootSystems = session_client.system.listSuggestedReboot(session_key)
    #print("Checking if system need reboot via api.")
    reboot_jobid = 0
    
    for a in needRebootSystems:
        if a['id'] == serverid:
            if "needReboot_jobs" not in copy_jobstatus_dict[a['name']]:
                try:
                    reboot_jobid = session_client.system.scheduleReboot(session_key, serverid, earliest_occurrence)
                except:
                    print("uups, creating a reboot job failed.")
                if reboot_jobid != 0:
                    temp_dict = { 'needReboot_jobs': { reboot_jobid: 'pending' } }
                    copy_jobstatus_dict[a['name']].update(temp_dict)
                    json_write(copy_jobstatus_dict)
                    #jobstatus_dict[a['name']]['Reboot_jobs'].update(reboot_jobid = 'pending')
                    print("A reboot job: %s \tfor %s has been created." %(str(reboot_jobid), a['name']))
                break
    return reboot_jobid

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

        copy_jobstatus_dict = deepcopy(jobstatus_dict)

        print("\n\033[96mPatch Job Status:\033[00m")
        print('{0: <30}'.format('System Name') + '{0: <10}'.format('JobID') + '{0: >15}'.format('Job Status' ))
        print('-----------------------------------------------------------------------------------------')
        if args.output_file:
            with open(args.output_file, "a") as write_file:
                write_file.write("\nPatch Job Status:\n")
        for k, v in jobstatus_dict.iteritems():
        
            for a,  b in v.iteritems():
                if a == 'serverid':
                        server_id = b
                if a == 'Patch_jobs':
                    for jobid,  jobstatus in b.iteritems():
                        completed_return = completed(int(jobid), int(server_id),  a)
                        #if completed_return == 0:
                        failed_return = failed(int(jobid), int(server_id),  a)
                        #if failed_return == 0:
                        progress_return = inprogress(int(jobid), int(server_id),  a)

        print("\n\033[96mScheduled Reboot Job Status:\033[00m")
        print('{0: <30}'.format('System Name') + '{0: <10}'.format('JobID') + '{0: >15}'.format('Job Status' ))
        print('-----------------------------------------------------------------------------------------')
        if args.output_file:
            with open(args.output_file, "a") as write_file:
                write_file.write("\n\nReboot Job Status:\n")
        for k, v in jobstatus_dict.iteritems():
        
            for a,  b in v.iteritems():
                if a == 'serverid':
                        server_id = b
                if a == 'Reboot_jobs':
                    for jobid,  jobstatus in b.iteritems():
                        completed_return = completed(int(jobid), int(server_id),  a)
                        if completed_return == 0:
                                failed_return = failed(int(jobid), int(server_id),  a)
                        if failed_return == 0:
                                progress_return = inprogress(int(jobid), int(server_id),  a)

        print("\n\033[96mAuto Reboot (kernel updates) Job Status:\033[00m")
        print('{0: <30}'.format('System Name') + '{0: <10}'.format('JobID') + '{0: >15}'.format('Job Status' ))
        print('-----------------------------------------------------------------------------------------')
        if args.output_file:
            with open(args.output_file, "a") as write_file:
                write_file.write("\n\nauto Reboot Job Status:\n")
        for k, v in jobstatus_dict.iteritems():
        
            for a,  b in v.iteritems():
                if a == 'serverid':
                        server_id = b
                if a == 'needReboot_jobs':
                    for jobid,  jobstatus in b.iteritems():
                        completed_return = completed(int(jobid), int(server_id),  a)
                        if completed_return == 0:
                                failed_return = failed(int(jobid), int(server_id),  a)
                        if failed_return == 0:
                                progress_return = inprogress(int(jobid), int(server_id),  a)

        if args.output_file:
            print("You can find the job status log in {}".format(args.output_file))
        
        time.sleep(5)

if __name__ == '__main__':
    try:
        with open(args.jsonfile, "r") as r_file:
            jobstatus_dict = json.load(r_file)

        copy_jobstatus_dict = deepcopy(jobstatus_dict)
        main_loop()
    except KeyboardInterrupt:
        session_client.auth.logout(session_key)
        print >> sys.stderr, '\nExiting by user request.\n'
        sys.exit(0)



            
