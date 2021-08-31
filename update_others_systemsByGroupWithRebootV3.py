#!/usr/bin/python
import xmlrpclib,  argparse,  getpass,  textwrap,  json, sys
from datetime import datetime,  timedelta
from collections import defaultdict
#from array import *

class Password(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        if values is None:
            values = getpass.getpass()
        setattr(namespace, self.dest, values)

parser = argparse.ArgumentParser()
reboot_parser = argparse.ArgumentParser()
#parser.add_argument("-v", "--verbosity", action="count", default=0)
parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
This scripts schedules patch deployment jobs for given group's systems' in given hours from now on. A reboot will be scheduled as well. 
Sample command: \
patch active systems from group in 2 hours from now, without reboot, for NON-Enterprise-Linux systems only. \
              python update_others_systemsByGroupWithRebootV3.py -s bjsuma.bo2go.home -u bjin -p suse1234 -g test2 -o 2 -no-r \n \

patch active systems from group in 2 hours from now, with reboot at specified date time, for NON-Enterprise-Linux systems only.\
              python update_ubuntu_systemsByGroupWithRebootV3.py -s bjsuma.bo2go.home -u bjin -p suse1234 -g test2 -o 2 -r -sr '15:30 20-09-2020'  \n \
Check Job status of the system. ''')) 

parser.add_argument("-s", "--server", help="Enter your suse manager host address e.g. myserver.abd.domain",  default='localhost',  required=True)
parser.add_argument("-u", "--username", help="Enter your suse manager loginid e.g. admin ", default='admin',  required=True)
parser.add_argument('-p', action=Password, nargs='?', dest='password', help='Enter your password',  required=True)
parser.add_argument("-g", "--group_name", help="Enter a valid groupname. e.g. DEV-SLES12SP3 ",  required=True)
parser.add_argument("-o", "--in_hours", help="in how many hours should the job be started. e.g. 2 ",  required=False)
parser.add_argument("-sr", "--schedule_reboot", help="when it should reboot in format 15:30 20-04-1970",  required=False)
# parser.add_argument("-r", "--reboot", help="if this optional argument is provided then a reboot jobs schedules \
#     for one hour later then patch jobs will be scheduled as well.", default=False, required=True)

reboot_parser = parser.add_mutually_exclusive_group(required=True)
reboot_parser.add_argument("-r", '--reboot', dest='reboot', action='store_true')
reboot_parser.add_argument("-no-r", '--no-reboot', dest='reboot', action='store_false')
parser.set_defaults(reboot=False)
args = parser.parse_args()


MANAGER_URL = "http://"+ args.server+"/rpc/api"
MANAGER_LOGIN = args.username
MANAGER_PASSWORD = args.password

#This is a new reboot request to allow reboot in given hours OR given exact time schedule.
#But if both params provide than we exit as this can not be handled at same time.


session_client = xmlrpclib.Server(MANAGER_URL, verbose=0)
session_key = session_client.auth.login(MANAGER_LOGIN, MANAGER_PASSWORD)

if args.in_hours:
    nowlater = datetime.now() + timedelta(hours=int(args.in_hours))
else:
    nowlater = datetime.now()
earliest_occurrence = xmlrpclib.DateTime(nowlater)
allgroups = session_client.systemgroup.listAllGroups(session_key)

joblist = []
joblist_reboot = []
nested_dict = lambda: defaultdict(nested_dict)
jobsdict = nested_dict
jobsdict = {}
error1 = 0


def scheduleReboot(serverid,  servername):
    if args.in_hours and not args.schedule_reboot:
        reboottime = datetime.now() + timedelta(hours=int(args.in_hours)+1)
    elif args.schedule_reboot and args.in_hours :
        reboottime = datetime.strptime(args.schedule_reboot, "%H:%M %d-%m-%Y")
    else:
        reboottime = datetime.now() + timedelta(minutes=10)

    earliest_occurrence_reboot = xmlrpclib.DateTime(reboottime)
    reboot_jobid = session_client.system.scheduleReboot(session_key, serverid, earliest_occurrence_reboot)
    try: 
        if reboot_jobid:
            system_name = session_client.system.getName(session_key, serverid)
            print("Reboot Job ID %s for %s %s has been created" %(str(reboot_jobid),  (str(serverid)), system_name['name']))
            jobsdict[servername]['Reboot_jobs']  = {}
            jobsdict[servername]['serverid'] = serverid
            jobsdict[servername]['Reboot_jobs'][reboot_jobid] = 'pending'

    except NameError:
        print("No reboot job created.")
        sys.exit(1)
    
    
def json_write(mydict):
        with open("joblist.json", "w") as write_file:
            json.dump(mydict, write_file,  indent=4)

def update_others(session_key, e, system_updatelist, earliest_occurrence):
    updatelist = session_client.system.listLatestUpgradablePackages(session_key, e)
    if not updatelist:
        system_name = session_client.system.getName(session_key, e)
        print("All good. No Updates needed:\t %s" %(system_name['name']))
        sys.exit(0)
        
    for s in updatelist:
        system_updatelist.append(s['to_package_id'])
    if system_updatelist:        
        system_actionid = session_client.system.schedulePackageInstall(session_key, e, system_updatelist, earliest_occurrence)
        del system_updatelist
        system_name = session_client.system.getName(session_key, e)
        jobsdict[system_name['name']]={}
        jobsdict[system_name['name']]['Patch_jobs']  = {}
        jobsdict[system_name['name']]['serverid']= e
    
        jobsdict[system_name['name']]['Patch_jobs'][system_actionid] =  'pending'
        print("Job ID %s for %s %s has been created" %(str(system_actionid),  (str(e)), system_name['name']))
        if args.reboot:
            scheduleReboot(e,  system_name['name'])
    else:
        print("No package to update.")   
        sys.exit(0)

if args.group_name:
    grpfound = 'false'
    for a in allgroups:
        
        if a['name'] == args.group_name:
            print("Targeting systems in group: %s with %s systems." %(a['name'],  str(a['system_count'])))
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
        system_updatelist = []
        update_others(session_key, e, system_updatelist, earliest_occurrence)

if error1 != 1:
    json_write(jobsdict)
session_client.auth.logout(session_key)




            
