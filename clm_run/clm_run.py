#!/usr/bin/python
import xmlrpclib,  argparse,  getpass,  textwrap, time
from datetime import datetime

class Password(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        if values is None:
            values = getpass.getpass()

        setattr(namespace, self.dest, values)

parser = argparse.ArgumentParser()
parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
This scripts helps to manage content lifecycle management projects. 
Sample command:
              python clm_run.py -s bjsuma.bo2go.home -u bjin -p suse1234 --listProject
              python clm_run.py -s bjsuma.bo2go.home -u bjin -p suse1234 --listEnvironment --projLabel myprojlabel
              python clm_run.py -s bjsuma.bo2go.home -u bjin -p suse1234 --build --projLabel myprojlabel \n \
              python clm_run.py -s bjsuma.bo2go.home -u bjin -p suse1234 --promote --projLabel myprojlabel --envLabel teststage  \n \
              python clm_run.py -s bjsuma.bo2go.home -u bjin -p suse1234 --check_status --projLabel myprojlabel --envLabel teststage  \n \
The script can build project, update and promote stages or environments.
Check taskomatic logs in order to monitor the status of the build and promote tasks e.g. # tail -f /var/log/rhn/rhn_taskomatic_daemon.log. '''))

parser.add_argument("--listProject", action="store_true")
parser.add_argument("--listEnvironment", action="store_true")
parser.add_argument("--check_status", action="store_true")
parser.add_argument("--build", action="store_true")
parser.add_argument("--promote", action="store_true")
parser.add_argument("-s", "--server", help="Enter your suse manager host address e.g. myserver.abd.domain",  default='localhost',  required=True)
parser.add_argument("-u", "--username", help="Enter your suse manager loginid e.g. admin ", default='admin',  required=True)
parser.add_argument('-p', action=Password, nargs='?', dest='password', help='Enter your password',  required=True)
parser.add_argument("--projname", help="Enter the desired project name. e.g. myproject",  required=False)
parser.add_argument("--projLabel", help="Enter the project label. e.g. mytest",  required=False)
parser.add_argument("--envLabel", help="Enter the environment label. e.g. dev",  required=False)
args = parser.parse_args()

MANAGER_URL = "http://"+ args.server+"/rpc/api"
MANAGER_LOGIN = args.username
MANAGER_PASSWORD = args.password
client = xmlrpclib.Server(MANAGER_URL, verbose=0)
key = client.auth.login(MANAGER_LOGIN, MANAGER_PASSWORD)
today = datetime.today()
earliest_occurrence = xmlrpclib.DateTime(today)

status_text = ['built', 'building',  'generating_repodata']
tasko_text = 'Check taskomatic logs in order to monitor the status of the build and promote tasks e.g. # tail -f /var/log/rhn/rhn_taskomatic_daemon.log.'

def printzip(dict_object):
    for i in dict_object:
        keys = i.keys()
        val = i.values()
        print("Item---------------------------------------------")
        for k in keys:
            print ("{:<20}".format(k)), 
        print("\n")
        for v in val:
            print ("{:<20}".format(v)), 
        print("\n")
        print("----------------------------------------------------")
    return

def listproject(key):
    projlist = client.contentmanagement.listProjects(key)
    if projlist:
        printzip(projlist)
        return True
    else:
        print("no projects found")
        return False

def listEnvironment(key, projectLabel):
    envlist = client.contentmanagement.listProjectEnvironments(key, projectLabel)
    if envlist:
        printzip(envlist)
        return True
    else:
        print("no projectEnvironments found")
        return False

def check_env_status(key,  projLabel,  *args):
    if not args:
        envLabel = ''
    else:
        for a in args:
            envLabel = a
    if envLabel == '':
        lookup_proj_return = client.contentmanagement.lookupProject(key, projLabel)
        for k,  v in lookup_proj_return.items():
            if k in 'firstEnvironment':
                envLabel = v
        try:
            lookupenv = client.contentmanagement.lookupEnvironment(key, projLabel,  envLabel)
            for k,  v in lookupenv.items():
                #print("lets see k %s, v is: %s" %(k, v))
                if k == "status":
                    for s in status_text:
                        if s in v:
                            print("%s: %s is %s" %(projLabel, envLabel, s))
                            break
        except Exception as ex:
            print("not found %s" %ex)
            print("check_env_status failed. Exit with error")
            exit(1)
    else:
        try:
            lookupenv = client.contentmanagement.lookupEnvironment(key, projLabel,  envLabel)
            print("%s: %s is %s" %(projLabel, envLabel, lookupenv['status']))
        except Exception as ex:
            print("not found %s" %ex)
            print("check_env_status failed. Exit with error")
            exit(1)
    return
        
def buildproject(key,  projLabel):
    buildresult = client.contentmanagement.buildProject(key, projLabel)
    if buildresult == 1:
            print("Build %s task: Successful"  %(projLabel))
            print("sleep 5 seconds")
            time.sleep(5)
            check_env_status(key, projLabel)
            print(tasko_text)
    else:
            print("Build failed. Exit with error.")
            exit(1)    
    return buildresult

def promoteenvironment(key,  projLabel,  envLabel):
    try:
        nextenvironment = client.contentmanagement.listProjectEnvironments(key, projLabel)
    except Exception as ex:
        print("not found %s" %ex)
        print("lookup project and environment label failed. exit.")
        exit(1)
    
    for i in nextenvironment:
        if i['label'] == envLabel:
            nextLabel = i['nextEnvironmentLabel']
            check_env_status(key,  projLabel, nextLabel)
            break
   
    try:
        promote_result = client.contentmanagement.promoteProject(key, projLabel,  envLabel)
        if promote_result == 1:
            print("promote %s %s task: Successful."  %(projLabel, envLabel))
            print("sleep 5 seconds")
            time.sleep(5)
            check_env_status(key, projLabel, nextLabel)
            print(tasko_text)
        else:
            print("promote failed. Exit with error.")
            exit(1)
    except Exception as ex:
        print("not found %s" %ex)
        return False
    return promote_result
    
if args.listProject:
    try:
        ret = listproject(key)
    except Exception as ex:
        print("not found %s" %ex)
        print('something went wrong with listproject')
elif args.check_status and args.projLabel: 
    if args.envLabel:
        check_env_status(key,  args.projLabel, args.envLabel)
    elif not args.envLabel:
        check_env_status(key,  args.projLabel)
elif args.listEnvironment and args.projLabel:
    try:
        ret = listEnvironment(key, args.projLabel)
    except Exception as ex:
        print(ex)
        print("something went wrong with listEnvironment.")
elif args.build and args.projLabel:
    try:
        ret = buildproject(key, args.projLabel)
    except Exception as ex:
        print(ex)
        print("something went wrong with buildproject.")
elif args.promote and args.projLabel and args.envLabel:
     try:
        ret = promoteenvironment(key, args.projLabel,  args.envLabel)
     except Exception as ex:
        print("not found %s" %ex)
        print("something went wrong with promote environment.")
else:
    print("Please verify you entered correct parameters. Exiting.")

    
