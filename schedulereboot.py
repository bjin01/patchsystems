#!/usr/bin/python
import xmlrpclib,  argparse,  getpass,  textwrap,  sys,  time
from datetime import datetime,  timedelta

class Password(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        if values is None:
            values = getpass.getpass()

        setattr(namespace, self.dest, values)

parser = argparse.ArgumentParser()
#parser.add_argument("-v", "--verbosity", action="count", default=0)
parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
This scripts runs service pack migration for given base channel. 

Sample command:

              python schedulereboot.py -s bjsuma.bo2go.home -u bjin -p suse1234 -g DEV-SLES12SP3 \n \

If -x is not specified the SP Migration is always a dryRun.
Check Job status of the system if dryrun was successful before run the above command with -x specified. ''')) 
parser.add_argument("-x", "--patch-it", action="store_true")
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
today = datetime.today()
nowlater = datetime.now() + timedelta(hours=2)
nowlater1 = datetime.now() + timedelta(hours=3)
isonowlater = nowlater.isoformat()
isonowlater1 = nowlater1.isoformat()
dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y_%H:%M:%S")
print('Current Timestamp : ', timestampStr)
earliest_occurrence = xmlrpclib.DateTime(nowlater)
print(earliest_occurrence)
#jobtime = dateutil.parser.parse(earliest_occurrence)
allgroups = session_client.systemgroup.listAllGroups(session_key)
mycount = 0
for a in allgroups:
    print("Group name: %s\t with %s systems." %(a['name'],  str(a['system_count'])))

y = 1 
while y:
    print ('Reboot scheduling is running for 2 hours and constantly checking for systems which need reboots and schedule it upon patch job status..')
    dt = datetime.now() + timedelta(hours=2)
    dt = dt.replace(minute=10)

    while datetime.now() < dt:
        print('Script will end at %s' %(dt))
        time.sleep(600)
    if args.group_name:
        try:
            systemlist = session_client.systemgroup.listActiveSystemsInGroup(session_key, args.group_name)
            print("system group %s found!" %(args.group_name))
            for e in systemlist:
                systemevents = session_client.system.listSystemEvents(session_key, e)
                print("number of systemevents is: %s" %(len(systemevents)))
                for r in systemevents:
                    print(r['created_date'])
                    if r['created_date'] > isonowlater1:
                        if r['failed_count'] != 0 or r['successful_count'] != 0:
                            mycount = mycount + r['failed_count'] + r['successful_count']
                        else:
                            mycount = 200000000
                if mycount >= len(systemevents):
                    rebootjob = session_client.system.scheduleReboot(session_key, e,  earliest_occurrence)
                    print("A reboot job with id %s has been scheduled for %s" %(rebootjob, e))
                else:
                    print("No system is qualified for a reboot!")
        except:
            print("something went wrong. The groupname could not be validated.")
    else:
        sys.exit(1)
    
    if datetime.now() >= dt:
        y = 0

        





            
