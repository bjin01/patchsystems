#!/usr/bin/python
import xmlrpclib,  argparse,  getpass,  textwrap,  json

class Password(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        if values is None:
            values = getpass.getpass()
        setattr(namespace, self.dest, values)

parser = argparse.ArgumentParser()
#parser.add_argument("-v", "--verbosity", action="count", default=0)
parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
This scripts cancells jobs by passing a json formatted file with jobid. 
The idea is to give administrators a handy script to test script based job creation and then immediately delete all just created jobs at once instead of using web UI.
Sample command:
              python jobstatus.py -s bjsuma.bo2go.home -u bjin -p suse1234 -f ./joblist.json\n \
Cancel Job actions of the systems. ''')) 

parser.add_argument("-s", "--server", help="Enter your suse manager host address e.g. myserver.abd.domain",  default='localhost',  required=True)
parser.add_argument("-u", "--username", help="Enter your suse manager loginid e.g. admin ", default='admin',  required=True)
parser.add_argument('-p', action=Password, nargs='?', dest='password', help='Enter your password',  required=True)
parser.add_argument("-f", "--jsonfile", help="Enter the json file name inluding path. e.g. ~/user/joblist.json ",  required=True)
args = parser.parse_args()

MANAGER_URL = "http://"+ args.server+"/rpc/api"
MANAGER_LOGIN = args.username
MANAGER_PASSWORD = args.password
session_client = xmlrpclib.Server(MANAGER_URL, verbose=0)
session_key = session_client.auth.login(MANAGER_LOGIN, MANAGER_PASSWORD)

with open(args.jsonfile, "r") as r_file:
    jobstatus_dict = json.load(r_file)

cancel_list = []

for k, v in jobstatus_dict.iteritems():
  for a,  b in v.iteritems():
      if a == 'Patch_jobs' or a == 'Reboot_jobs' :
          for jobid,  jobstatus in b.iteritems():
              cancel_list.append(int(jobid))


try:
    return_status = session_client.schedule.cancelActions(session_key, cancel_list)
except:
    print("Job Cancellation failed.")

if return_status == 1:
    print("All given job actions have been cancelled successfully")
else:
    print("Something went wrong, check job status in Web UI -> schedule -> pending/failed/completed ")
session_client.auth.logout(session_key)




            
