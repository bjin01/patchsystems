#!/usr/bin/python
import xmlrpclib,  argparse,  getpass,  textwrap,  sys
from datetime import datetime
from array import array

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
dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y_%H:%M:%S")
print('Current Timestamp : ', timestampStr)
 
earliest_occurrence = xmlrpclib.DateTime(today)

allgroups = session_client.systemgroup.listAllGroups(session_key)
for a in allgroups:
    print("Group name: %s\t with %s systems." %(a['name'],  str(a['system_count'])))

if args.group_name:
    try:
        systemlist = session_client.systemgroup.listActiveSystemsInGroup(session_key, args.group_name)
        chain_label = args.group_name + "_" + timestampStr
        systemactionid = session_client.actionchain.createChain(session_key, chain_label)           
        print("system group %s found!" %(args.group_name))
        print("A action chain with id %s has been created." %(str(systemactionid)))
    except:
        print("something went wrong. The groupname could not be validated.")
else:
    sys.exit(1)

for s in systemlist:
    print(s)
    packagelist = session_client.system.listLatestUpgradablePackages(session_key, s)
    print("total number of upgradable packages are: ",  len(packagelist))
    #for p in packagelist:
        #print(p)
    #print("system name: %s" %(str(systemlist['server_id'])))

finalpatches = array("i")

for e in systemlist:
    print("serverid is: %s" %(str(e)))
    erratalist = session_client.system.getRelevantErrata(session_key, e)
    systemdetails = session_client.system.listActiveSystemsDetails(session_key, e)
    
    #print(erratalist)
    for r in erratalist:
        try:
            actionid = session_client.actionchain.addErrataUpdate(session_key, s,  r['id'],  chain_label)
        except:
            print()
    try:
        actionid = session_client.actionchain.addSystemReboot(session_key, e,  chain_label)
    except:
        print()

            
