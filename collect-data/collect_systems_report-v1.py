#!/usr/bin/python
"""This python script is intended to collect information from SUSE Manager 
The script will count number of virtual or physical systems and put the data
into the given text file and send it by email to the given email address.
"""
import xmlrpclib,  argparse,  getpass,  textwrap, sys, subprocess
from datetime import datetime,  timedelta

class Password(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        if values is None:
            values = getpass.getpass()
        setattr(namespace, self.dest, values)

def print_more_details(systemlist_final):
    print("\n\nThis are the system details from %s:\n\n" %datetime.now())
    if len(systemlist_final) != 0:
        for a in systemlist_final:
            print("%s %s:" %(a['id'], a['name']))
            print("\tVM: %s" %a['virtualization'])
            print("\tbaseproduct: %s" %a['baseproduct'])
            print("\tversion: %s" %a['version'])
            print("\tarchitecture: %s" %a['cpu'])

def getcpu(systemid):
    try:
        system_details = session_client.system.getCpu(session_key, systemid)
        if system_details['socket_count'] is not None:
            return system_details['socket_count']
        else:
            return 0
    except:
        print("Could not query cpu socket information from %s" %systemid)

def write_datafile(fpath, systemlist_final):
    my_now = datetime.now()
    with open(fpath, 'w') as f:
        f.write("Monthly Audit of Linux servers - %s\n" %(my_now.strftime("%d/%m/%Y, %H:%M:%S")))
        f.write("Total: %s\n"% count_Total)
        f.write("Total VM: %s\n" % count_virtual)
        f.write("Total bare-metal: %s \tTotal physical CPU Sockets %s\n" % (count_physical, count_physical_cpu_sockets))
        f.write("Total SLES: %s\n" % count_SLES)
        f.write("Total SLES_for_SAP: %s\n" % count_SLES_for_SAP)
        f.write("Total Expanded Support: %s\n" % count_RES)
        f.write("Total RHEL: %s\n" % count_RHEL)
        f.write("Total Centos: %s\n" % count_Centos)
        f.write("\n\nThis are the system details from %s:\n" %datetime.now())
        if len(systemlist_final) != 0:
            for a in systemlist_final:
                f.write("%s %s:\n" %(a['id'], a['name']))
                f.write("\tVM: %s\n" %a['virtualization'])
                f.write("\tbaseproduct: %s\n" %a['baseproduct'])
                f.write("\tversion: %s\n" %a['version'])
                f.write("\tarchitecture: %s\n\n" %a['cpu'])

def send_mail(to_email, fpath):
    try:
        check_output = subprocess.check_output(["mailx", "-V"])
        print("mailx programm is installed. %s" %check_output)
    except:
        print("mailx not found. Exit with error. 1")
        sys.exit(1)
    from_email = "test@test.domain.com" 
    subj = '"Monthly Audit of Linux servers"'
    cmd = "mailx " + "-r " + from_email + " " + "-s " + subj + " " + to_email + " " + "<" + fpath
    cmdoutput = subprocess.check_output([cmd], shell=True)
    if cmdoutput != "":
        print("mailx output: %s" %cmdoutput)

parser = argparse.ArgumentParser()
printdetails_parser = argparse.ArgumentParser()
#parser.add_argument("-v", "--verbosity", action="count", default=0)
parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
This scripts collect all systems in SUSE Manager. 
Sample command:
              python collect_systems_report-v1.py -s bjsuma.bo2go.home -u bjin -p suse1234 \n \
''')) 

parser.add_argument("-s", "--server", help="Enter your suse manager host address e.g. myserver.abd.domain",  default='localhost',  required=True)
parser.add_argument("-u", "--username", help="Enter your suse manager loginid e.g. admin ", default='admin',  required=True)
parser.add_argument('-p', action=Password, nargs='?', dest='password', help='Enter your password',  required=True)
parser.add_argument("-f", "--filename", dest='filepath', help="Enter file path and name you want data to be written into e.g. -f /home/user/results.txt ",  required=False)
parser.add_argument("-m", "--to_email", dest='to_email', help="Enter valid email address you want send to e.g. -m foo.bar@email.domain.com ",  required=False)

printdetails_parser = parser.add_mutually_exclusive_group(required=False)
printdetails_parser.add_argument("-d", '--details', dest='printdetails', help="print more details of the system information", action='store_true')
parser.set_defaults(printdetails=False)
args = parser.parse_args()

MANAGER_URL = "http://"+ args.server+"/rpc/api"
MANAGER_LOGIN = args.username
MANAGER_PASSWORD = args.password

session_client = xmlrpclib.Server(MANAGER_URL, verbose=0)
session_key = session_client.auth.login(MANAGER_LOGIN, MANAGER_PASSWORD)

if args.printdetails:
    print("args.printdetails %s" %args.printdetails)

try:
    systemslist = session_client.system.listSystems(session_key)
except:
    print("Something went wrong, api call failed.")
    sys.exit(1)

systemlist_final = []
systemdetails = {}
count_virtual = 0
count_physical = 0
count_SLES = 0
count_SLES_for_SAP = 0
count_RES = 0
count_RHEL = 0
count_Centos = 0
count_Total = 0
count_physical_cpu_sockets = 0

if len(systemslist) != 0:

    count_Total = len(systemslist)
    for i in systemslist:

        systemdetails['id'] = i['id']
        systemdetails['name'] = i['name']
        try:
            system_details = session_client.system.getDetails(session_key, i['id'])
            if system_details.get('virtualization') is not None and system_details['virtualization'] != "":
                systemdetails['virtualization'] = True
                count_virtual += 1

            else:
                systemdetails['virtualization'] = False
                count_physical += 1
                cpusocket_number = getcpu(i['id'])
                count_physical_cpu_sockets += cpusocket_number

        except:
            print("%s not found." % i['id'])

        try:
            userslist = session_client.user.listUsers(session_key)
            #print(userslist[0]['login'])
            if userslist[0]['login'] == args.username:
                #print(userslist[0]['login'], userslist[0]['id'])
                installedproducts = []
                installedproducts = session_client.system.getInstalledProducts(userslist[0]['id'], i['id'])
                #print(installedproducts)
                for x in installedproducts:
                    if x['isBaseProduct']:
                        systemdetails['baseproduct'] = x['name']
                        if systemdetails['baseproduct'] == "SLES":
                            count_SLES += 1
                        if systemdetails['baseproduct'] == "SLES_SAP":
                            count_SLES_for_SAP += 1
                        if "res" in systemdetails['baseproduct'].lower():
                            count_RES += 1
                        if "rhel" in systemdetails['baseproduct'].lower():
                            count_RHEL += 1
                        if systemdetails['baseproduct'] == "centos":
                            count_Centos += 1
                        systemdetails['cpu'] = x['arch']
                        systemdetails['version'] = x['version']

        except:
            print("%s installed products not found." % i['id'])
        
        dictionary_copy = systemdetails.copy()
        systemlist_final.append(dictionary_copy)
    
    print("Total: %s" % count_Total)
    print("Total VM: %s" % count_virtual)
    print("Total bare-metal: %s, \tTotal physical CPU Sockets %s" % (count_physical, count_physical_cpu_sockets))
    print("Total SLES: %s" % count_SLES)
    print("Total SLES_for_SAP: %s" % count_SLES_for_SAP)
    print("Total Expanded Support: %s" % count_RES)
    print("Total RHEL: %s" % count_RHEL)
    print("Total Centos: %s" % count_Centos)
    
else:
    sys.exit(1)

if args.printdetails:
        print_more_details(systemlist_final)

if args.filepath:
    write_datafile(args.filepath, systemlist_final)

if not args.filepath:
    print("You have not provided a output file to which the results should be written into. This is not bad but just be aware of this feature.")

if args.to_email and args.filepath:
    send_mail(args.to_email, args.filepath)

if args.to_email and not args.filepath:
    print("Hey, you have not provided the output file that content should be sent via email. Do this with -f filename")

session_client.auth.logout(session_key)