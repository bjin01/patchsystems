#!/usr/bin/python

import subprocess
import argparse
#import getpass
import textwrap
#import time
import datetime
import yaml
import os
from xmlrpc.client import ServerProxy, DateTime
import logging
import shutil
from os import access, R_OK
from os.path import isfile


logfilename = "/var/log/automic_suma_checkhosts.log"
mylogs = logging.getLogger(__name__)
mylogs.setLevel(logging.DEBUG)
#file handler adding here, log file should be overwritten every time as this will be sent via email
file = logging.FileHandler(logfilename, mode='w')
file.setLevel(logging.DEBUG)

fileformat = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s",datefmt="%H:%M:%S")
file.setFormatter(fileformat)

#handler for sending messages to console stdout
stream = logging.StreamHandler()
streamformat = logging.Formatter("%(asctime)s:%(filename)s:%(levelname)s:%(message)s",datefmt="%H:%M:%S")
stream.setLevel(logging.DEBUG)
stream.setFormatter(streamformat)

mylogs.addHandler(file)
#mylogs.addHandler(stream)

""" class Password(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        if values is None:
            values = getpass.getpass()

        setattr(namespace, self.dest, values) """

parser = argparse.ArgumentParser()
parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
This Script checks host status of a given group in SUSE Manager.

You need a suma_config.yaml file with login and email notification address.
If email notification will be used then you need to have mutt email client installed. 

Sample suma_config.yaml:
suma_host: mysumaserver.mydomain.local
suma_user: <USERNAME>
suma_password: <PASSWORD>
notify_email: <EMAIL_ADDRESS>

Sample command:
              python3 checkhosts.py --config /root/suma_config.yaml --group api_group_test
              python3 checkhosts.py --config /root/suma_config.yaml --group api_group_test
The script helps to list hosts and if there are patches to be installed of a given group and send email notifications optionally.'''))

parser.add_argument("--config", help="enter the config file name that contains login information e.g. /root/suma_config.yaml",  required=False)
parser.add_argument("--group", help="Enter the group name for which systems of a group you want to install live kernel patches.",  required=False)
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
            subject = "SUSE Manager - Check Host status."
            cmd1 = ['cat', logfilename]
            proc1 = subprocess.run(cmd1, stdout=subprocess.PIPE)
            cmd2 = [email_client_name, '-s', subject, suma_data["notify_email"]]
            proc2 = subprocess.run(cmd2, input=proc1.stdout)
    else:
        mylogs.info("Not sending email.")
    return

def printdict(dict_object):
    mylogs.info("Item---------------------------------------------")
    for a, b in dict_object.items():
        if isinstance(b, dict):
            for k, v in b.items():
                print("{:<20}".format(k), "{:<20}".format(v))
        else:
            print("{:<20}".format(a), "{:<20}".format(b))
        
    mylogs.info("----------------------------------------------------")

def get_servers_patches(mylist):

    patch_list = {}
    temp_server_list = []
    for i, j in mylist.items():
        try:
            temp_list = session.system.getRelevantErrata(key, i)
            #mylogs.info("Host: %s    %d patches." %(j, len(temp_list)))
        except:
            mylogs.error("failed to obtain patch list from %s" %(j))

        if temp_list and len(temp_list) != 0:
            patch_list[j] = len(temp_list)
        
    return patch_list

def isNotBlank(myString):
    if myString and myString.strip():
        #myString is not None AND myString is not empty or blank
        return True
    #myString is None OR myString is empty or blank
    return False

def get_hosts(groupname):
    
    nowlater = datetime.datetime.now()
    earliest_occurrence = DateTime(nowlater)
    try:
        result_systemlist = session.systemgroup.listSystemsMinimal(key, groupname)
    except Exception as e:
        mylogs.error("get systems list from group failed. %s" %(e))
        result2email()
        exit(1)
    mylogs.info("List of Systems is ready.")

    server_list = {}
    patch_list = []
    for a in result_systemlist:
        server_list[a['id']] = a["name"]
       
    patch_list = get_servers_patches(server_list)
    # print(patch_list, server_id_list)
    print("Systeme mit installierbaren Patches:")
    if len(patch_list) > 0:
        for s, k in patch_list.items():
            print("%s: %d" %(s, k))
    return "finished."


if args.config:
    suma_data = get_login(args.config)
    session, key = login_suma(suma_data)
else:
    conf_file = "/root/suma_config.yaml"
    suma_data = get_login(conf_file)
    session, key = login_suma(suma_data)

if isNotBlank(args.group):
    
    result = get_hosts(args.group)
    mylogs.info(result)
else:
    mylogs.info("group name is empty.")
    result2email()
    exit(1)
    
suma_logout(session, key)
result2email()