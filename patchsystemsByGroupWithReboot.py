#!/usr/bin/python
import xmlrpclib,  argparse,  getpass,  textwrap
from datetime import datetime,  timedelta
#from array import *

class Password(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        if values is None:
            values = getpass.getpass()
        setattr(namespace, self.dest, values)

parser = argparse.ArgumentParser()
#parser.add_argument("-v", "--verbosity", action="count", default=0)
parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
This scripts schedules patch deployment jobs for given group's systems' in given hours from now on. A reboot will be scheduled as well. 
Sample command:
              python patchsystemsByGroupWithReboot.py -s bjsuma.bo2go.home -u bjin -p suse1234 -g testgroup -o 2 \n \
Check Job status of the system. ''')) 
parser.add_argument("-x", "--patch-it", action="store_true")
parser.add_argument("-s", "--server", help="Enter your suse manager host address e.g. myserver.abd.domain",  default='localhost',  required=True)
parser.add_argument("-u", "--username", help="Enter your suse manager loginid e.g. admin ", default='admin',  required=True)
parser.add_argument('-p', action=Password, nargs='?', dest='password', help='Enter your password',  required=True)
parser.add_argument("-g", "--group_name", help="Enter a valid groupname. e.g. DEV-SLES12SP3 ",  required=True)
parser.add_argument("-o", "--in_hours", help="in how many hours should the job be started. e.g. 2 ",  required=True)
args = parser.parse_args()

MANAGER_URL = "http://"+ args.server+"/rpc/api"
MANAGER_LOGIN = args.username
MANAGER_PASSWORD = args.password

session_client = xmlrpclib.Server(MANAGER_URL, verbose=0)
session_key = session_client.auth.login(MANAGER_LOGIN, MANAGER_PASSWORD)
nowlater = datetime.now() + timedelta(hours=int(args.in_hours))
earliest_occurrence = xmlrpclib.DateTime(nowlater)
allgroups = session_client.systemgroup.listAllGroups(session_key)

joblist = []
joblist_reboot = []
def scheduleReboot(serverid):
    reboottime = datetime.now() + timedelta(hours=int(args.in_hours)+1)
    earliest_occurrence_reboot = xmlrpclib.DateTime(reboottime)
    reboot_jobid = session_client.system.scheduleReboot(session_key, serverid,  earliest_occurrence_reboot)
    joblist_reboot.append(reboot_jobid)

if args.group_name:
    for a in allgroups:
        if a['name'] == args.group_name:
            print("Targeting group name: %s with %s systems." %(a['name'],  str(a['system_count'])))
            grpfound = 'true'
            break
    try:
        activesystemlist = session_client.systemgroup.listActiveSystemsInGroup(session_key, args.group_name)
        print("activesystemlist is: %s" %(activesystemlist))
    except:
        print("uups something went wrong. We could not find the active systems in the given group name. Maybe the group is empty.")
        
    for e in activesystemlist:
        system_erratalist = []
        
        print(" e is %s:" %(e))
        erratalist = session_client.system.getRelevantErrata(session_key, e)
        for s in erratalist:    
            system_erratalist.append(s['id'])
        try:    
            system_actionid = session_client.system.scheduleApplyErrata(session_key, e,  system_erratalist,  earliest_occurrence)
            scheduleReboot(e)
            #time.sleep(3)
            joblist += system_actionid
            print("Job ID %s for %s has been created" %(str(system_actionid),  (str(e))))
        except:
            print("uups something went wrong. We could not create scheduleApplyErrata for %s." %(str(e)))
            print("one possible reason is the targeted systems already have pending patch and reboot jobs scheduled.")
    
print("job list is: %s" %(joblist))
print("Job list for reboots is: %s" %(joblist_reboot))
session_client.auth.logout(session_key)




            
