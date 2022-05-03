import subprocess
import argparse
import textwrap
#import datetime
import yaml
import os
from xmlrpc.client import ServerProxy, DateTime
import logging
import shutil
from os import access, R_OK
from os.path import isfile

pid = os.getpid()
logfilename = "/var/log/rhn/create_update_gpgkeys.log"
mylogs = logging.getLogger(__name__)
mylogs.setLevel(logging.DEBUG)
#file handler adding here, log file should be overwritten every time as this will be sent via email
file = logging.FileHandler(logfilename, mode='w')
file.setLevel(logging.DEBUG)

fileformat = logging.Formatter("%(asctime)s:[pid %(process)d]:%(levelname)s: - %(message)s",datefmt="%H:%M:%S")
file.setFormatter(fileformat)

#handler for sending messages to console stdout
stream = logging.StreamHandler()
streamformat = logging.Formatter("%(asctime)s:[pid %(process)d]:%(filename)s:%(levelname)s:%(message)s",datefmt="%H:%M:%S")
stream.setLevel(logging.DEBUG)
#stream.setFormatter(streamformat)

mylogs.addHandler(file)
#mylogs.addHandler(stream)

""" class Password(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        if values is None:
            values = getpass.getpass()

        setattr(namespace, self.dest, values) """

parser = argparse.ArgumentParser()
parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
This Script creates or update GPG and SSL keys in SUSE Manager. The main purpose is to create and update Red Hat roting cdn SSL and GPG Keys.

You need a suma_config.yaml file with login and email notification address.
If email notification will be used then you need to have mutt email client installed. 

Sample suma_config.yaml:
suma_host: mysumaserver.mydomain.local
suma_user: <USERNAME>
suma_password: <PASSWORD>
notify_email: <EMAIL_ADDRESS>

Sample command:
              python3.6 create_update_gpgkeys.py --config /root/suma_config.yaml --create gpg --description "api test" --keyfile ./public.key 

              or 

              python3.6 create_update_gpgkeys.py --config /root/suma_config.yaml --update gpg --description "api test" --keyfile ./public.key
The script lists hosts and if there are patches to be installed of a given group and send email notifications optionally.'''))

parser.add_argument("--config", help="enter the config file name that contains login information e.g. /root/suma_config.yaml",  required=False)
parser.add_argument("--listkeys", help="We will list the existing keys in SUSE Manager.",  action="store_true")
parser.add_argument("--create", help="Enter the type of the key: gpg or ssl",  required=False)
parser.add_argument("--update", help="Enter the type of the key: gpg or ssl",  required=False)
parser.add_argument("--description", help="Enter the description of the key.",  required=False)
parser.add_argument("--keyfile", help="Enter the path of file containing the key in base64 pem format",  required=False)
parser.add_argument("--email", help="use this option if you want email notifcation, the log file will be sent to it. The email address is provided in the suma_config.yaml",  action="store_true")
args = parser.parse_args()

def get_login(path):
    
    if path == "":
        path = os.path.join(os.environ["HOME"], "suma_config.yaml")
    with open(path) as f:
        login = yaml.load_all(f, Loader=yaml.FullLoader)
        for a in login:
            login = a

    return login

def login_suma(login):
    MANAGER_LOGIN = login['suma_user']
    MANAGER_PASSWORD = login['suma_password']
    SUMA = "http://" + login['suma_user'] + ":" + login['suma_password'] + "@" + login['suma_host'] + "/rpc/api"
    with ServerProxy(SUMA) as session_client:
        session_key = session_client.auth.login(MANAGER_LOGIN, MANAGER_PASSWORD)
    return session_client, session_key

def suma_logout(session, key):
    session.auth.logout(key)
    return

def isNotBlank(myString):
    if myString and myString.strip():
        #myString is not None AND myString is not empty or blank
        return True
    #myString is None OR myString is empty or blank
    return False

def result2email():
    if args.email:
        assert isfile(logfilename) and access(logfilename, R_OK), \
        "File {} doesn't exist or isn't readable".format(logfilename)
        email_client_name = "mutt"
        path_to_cmd = shutil.which(email_client_name)    
        if path_to_cmd is None:
            mylogs.error(f"mutt email client is not installed.")
        else:
            mylogs.info("Sending log %s via email to %s" %(logfilename, suma_data["notify_email"]))
            subject = "SUSE Manager - Check Job status."
            cmd1 = ['cat', logfilename]
            proc1 = subprocess.run(cmd1, stdout=subprocess.PIPE)
            cmd2 = [email_client_name, '-s', subject, suma_data["notify_email"]]
            proc2 = subprocess.run(cmd2, input=proc1.stdout)
    else:
        mylogs.info("Not sending email.")
    return

def listallkeys():
    try:
        result_listkeys = session.kickstart.keys.listAllKeys(key)
        print("Description: \tType:")
        for a in result_listkeys:
            print("%s \t%s" %(a["description"], a["type"]))
            """ for i, h in a.items():
                print("%s: \t%s" %(i,h)) """
    except Exception as e:
        mylogs.error("Failed to get gpg and ssl keys list. %s" %(e))
        exit(1)
    return

def create_key():
    with open(args.keyfile) as fp:
        key_content = fp.read()
        
        try:
            result_create = session.kickstart.keys.create(key, args.description, args.create.upper(), key_content)
            print("Key created: %s" %result_create)
        except:
            print("Failed to create Key. Exit with error.")
            exit(2)
    return

def update_key():
    with open(args.keyfile) as fp:
        key_content = fp.read()
        try:
            result_create = session.kickstart.keys.update(key, args.description, args.update.upper(), key_content)
            print("Key created: %s" %result_create)
        except:
            print("Failed to update Key. Exit with error.")
            exit(2)
    return

def file_exist():
    try:
        assert isfile(args.keyfile) and access(args.keyfile, R_OK), \
            f"File {args.keyfile} doesn't exist or isn't readable"
        return True
    except AssertionError as msg:
        print(msg)
        return False

def check_type(type):
    if type.lower() in "gpg" or type.lower() in "ssl":
        print("OK, type is %s" % args.create)
        return True
    else:
        print("Type of key you provided must be either gpg or ssl. Try again, exit")
        return False

if args.config:
    suma_data = get_login(args.config)
    session, key = login_suma(suma_data)
else:
    conf_file = "/root/suma_config.yaml"
    suma_data = get_login(conf_file)
    session, key = login_suma(suma_data)

if args.listkeys:
    listallkeys()

if args.create and args.keyfile:
    if file_exist() and check_type(args.create):
        create_key()
    else:
        print("Exit with errors")
        exit(1)

if args.update and args.keyfile:
    if file_exist() and check_type(args.update):
        update_key()
    else:
        print("Exit with errors")
        exit(1)
    
suma_logout(session, key)
result2email()