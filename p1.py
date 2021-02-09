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

parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
This scripts schedules patch deployment jobs for given group's systems' in given hours from now on. A reboot will be scheduled as well. 
Sample command:
              python patchsystemsByGroupWithReboot.py -s bjsuma.bo2go.home -u bjin -p suse1234 -g testgroup
              ''')) 
parser.add_argument("-s", "--server", help="Enter your suse manager host address e.g. myserver.abd.domain",  default='localhost',  required=True)
parser.add_argument("-u", "--username", help="Enter your suse manager loginid e.g. admin ", default='admin',  required=True)
parser.add_argument('-p', action=Password, nargs='?', dest='password', help='Enter your password',  required=True)
parser.add_argument("-g", "--group_name", help="Enter a valid groupname. e.g. DEV-SLES12SP3 ",  required=True)

args = parser.parse_args()

MANAGER_URL = "http://"+ args.server+"/rpc/api"
MANAGER_LOGIN = args.username
MANAGER_PASSWORD = args.password


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




            
