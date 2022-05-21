#!/usr/bin/python

import subprocess
import argparse
#import getpass
import textwrap
import csv
#import time
import datetime
from this import d
import yaml
import os
from xmlrpc.client import ServerProxy, DateTime
import logging
import shutil
from os import access, R_OK
from os.path import isfile

pid = os.getpid()
logfilename = "/var/log/rhn/getcve_info.log"
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
This Script retrieves information about patches for a given CVE Numer for all systems. Like CVE Audit and outputs in csv file.

You need a suma_config.yaml file with login and email notification address.
If email notification will be used then you need to have mutt email client installed. 

Sample suma_config.yaml:
suma_host: mysumaserver.mydomain.local
suma_user: <USERNAME>
suma_password: <PASSWORD>
notify_email: <EMAIL_ADDRESS>

Sample command:
              python3.6 getcve_info.py --config /root/suma_config.yaml --keyword kernel

              '''))

parser.add_argument("--config", help="enter the config file name that contains login information e.g. /root/suma_config.yaml",  required=False)
parser.add_argument("--keyword", help="Enter one word that you want to get CVE list for.",  required=False)
parser.add_argument("--email", help="use this option if you want email notifcation, the log file will be sent to it. The email address is provided in the suma_config.yaml",  action="store_true")
args = parser.parse_args()

finalresult = []

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

def get_cvelist(patch_name):
    cve_list = []
    try:
        cve_list = session.errata.listCves(key, patch_name)
    except:
        mylogs.error("failed to obtain cve list from %s" %(patch_name))
    return cve_list

def get_servers_patches(mylist):
    patch_type = "Security Advisory"
    patch_list = {}
    temp_server_list = []
    for i, j in mylist.items():
        try:
            temp_list = session.system.getRelevantErrataByType(key, i, patch_type)
            #mylogs.info("Host: %s    %d patches." %(j, len(temp_list)))
        except:
            mylogs.error("failed to obtain patch list from %s" %(j))

        if temp_list and len(temp_list) != 0:
            for a in temp_list:
                if args.keyword in a["advisory_synopsis"]:
                    print("{}: {} {} {}".format(j, a["advisory_type"], a["advisory_synopsis"], a["advisory_name"]))
                    cvelist = get_cvelist(a["advisory_name"])
                    if len(cvelist) > 0:
                        for c in cvelist:
                            print("\t{}".format(c))

        else:
            patch_list[j] = 0
        
    return patch_list

def isNotBlank(myString):
    if myString and myString.strip():
        #myString is not None AND myString is not empty or blank
        return True
    #myString is None OR myString is empty or blank
    return False

def get_hosts():
    
    nowlater = datetime.datetime.now()
    earliest_occurrence = DateTime(nowlater)
    try:
        result_systemlist = session.system.listSystems(key)
    except Exception as e:
        print("Get systems failed")
        mylogs.error("get systems list failed.")
        result2email()
        suma_logout(session, key)
        exit(1)
    mylogs.info("List of Systems is ready.")

    server_list = {}
    patch_list = []
    for a in result_systemlist:
        server_list[a['id']] = a["name"]
    #(server_list)
    patch_list = get_servers_patches(server_list)
    # print(patch_list, server_id_list)
    
    """ if len(patch_list) > 0:
        for s, k in patch_list.items():
            print("%s: %d" %(s, k)) """
    return "finished."


if args.config:
    suma_data = get_login(args.config)
    session, key = login_suma(suma_data)
else:
    conf_file = "/root/suma_config.yaml"
    suma_data = get_login(conf_file)
    session, key = login_suma(suma_data)

if isNotBlank(args.keyword):
    
    result = get_hosts()
    mylogs.info(result)
else:
    mylogs.info("keyword is empty.")
    result2email()
    suma_logout(session, key)
    exit(1)
    
suma_logout(session, key)
result2email()