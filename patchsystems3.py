#!/usr/bin/python
import xmlrpclib,  argparse,  getpass,  textwrap,  sys,  subprocess,  shlex
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
This scripts runs service pack migration for given base channel. 

Sample command:

              python patchsystems.py -s bjsuma.bo2go.home -u bjin -p suse1234 -g DEV-SLES12SP3 \n \

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
isonowlater = nowlater.isoformat()
dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y_%H:%M:%S")
#print('Current Timestamp : ', timestampStr)
 
earliest_occurrence = xmlrpclib.DateTime(nowlater)

allgroups = session_client.systemgroup.listAllGroups(session_key)
finalpatches = []
        
for a in allgroups:
    if a['name'] == args.group_name:
        print("Targeting group name: %s\t with %s systems." %(a['name'],  str(a['system_count'])))

if args.group_name:
    try:
        systemlist = session_client.systemgroup.listActiveSystemsInGroup(session_key, args.group_name)
        chain_label = args.group_name + "_" + timestampStr
        #systemactionid = session_client.actionchain.createChain(session_key, chain_label)
        print("system group %s found!" %(args.group_name))
        for e in systemlist:
            erratalist = session_client.system.getRelevantErrata(session_key, e)
            
            for r in erratalist:
                #print(str(r['id']))
                finalpatches.append(r['id'])
                #actionid = session_client.systemgroup.scheduleApplyErrataToActive(session_key, args.group_name, r['id'])
    except:
        print("something went wrong. The groupname could not be validated.")
else:
    sys.exit(1)
patch_set = set(finalpatches)
print("Total number of patches to be applied: %s" %(len(patch_set)))
patch_list = list(patch_set)
#print(patch_list)

for p in patch_list:
    try:
        actionid = session_client.systemgroup.scheduleApplyErrataToActive(session_key, args.group_name, p,  earliest_occurrence)
    except:
        continue
        
params = "python schedulereboot.py " +" -s " + args.server + " -u " + args.username + " -p " + args.password + " -g " + args.group_name
myargs = shlex.split(params)
#print(myargs)
subprocess.Popen(myargs)





            
