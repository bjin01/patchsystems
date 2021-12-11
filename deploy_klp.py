#!/usr/bin/python

import subprocess
import argparse
import getpass
import textwrap
import time
import datetime
import yaml
import os
from xmlrpc.client import ServerProxy, Error, DateTime
import logging
import shutil
from os import access, R_OK
from os.path import isfile


logfilename = "/var/log/klp_deploy.log"
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
mylogs.addHandler(stream)

# And all that demo test code below this
class Password(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        if values is None:
            values = getpass.getpass()

        setattr(namespace, self.dest, values)

parser = argparse.ArgumentParser()
parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
This is SUSE Live Patching initial deployment tool:
You need a suma_config.yaml file with login and email notification address.
If email notification will be used then you need to have mutt email client installed. 

Sample suma_config.yaml:
suma_host: mysumaserver.mydomain.local
suma_user: <USERNAME>
suma_password: <PASSWORD>
notify_email: <EMAIL_ADDRESS>


Sample command:
              python3 deploy_klp.py --config /root/suma_config.yaml --group api_group_test
              python3 deploy_klp.py --config /root/suma_config.yaml --servername mytestserver.example.com
              python3 deploy_klp.py --config /root/suma_config.yaml --servername mytestserver.example.com --email
The script deployes klp. '''))
parser.add_argument("--config", help="Enter the config file name that contains login and channel information e.g. /root/suma_config.yaml",  required=False)
parser.add_argument("--group", help="Enter a group name as target.",  required=False)
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
    SUMA = "https://" + login['suma_user'] + ":" + login['suma_password'] + "@" + login['suma_host'] + "/rpc/api"
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
            subject = "SUSE Manager - Live Patching Deployment logs."
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


def getpkg_servers_lists(mylist):
    pkgname = "patterns-lp-lp_sles"
    temp_pkg_list = []
    temp_server_list = []
    for i,j in mylist.items():
        try:
            temp_list = session.system.listLatestInstallablePackages(key, i)
        except:
            mylogs.error("failed to obtain pkg list from %s" %(j))
            continue
        
        for s in temp_list:
            
            if s['name'].startswith(pkgname):
                mylogs.info("%s: %s for system: %s will be installed."%(s['name'], s['id'], j))
                temp_pkg_list.append(s['id'])
                temp_server_list.append(i)
    final_pkg_list = list(set(temp_pkg_list))
    final_server_list = list(set(temp_server_list))
    return final_pkg_list, final_server_list

def isNotBlank(myString):
    if myString and myString.strip():
        #myString is not None AND myString is not empty or blank
        return True
    #myString is None OR myString is empty or blank
    return False

def schedule_klp_install(suma_data, groupname):
    
    nowlater = datetime.datetime.now()
    earliest_occurrence = DateTime(nowlater)
    try:
        result_systemlist = session.systemgroup.listSystemsMinimal(key, groupname)
    except Exception as e:
        mylogs.error("get systems list from group failed. %s" %(e))
        result2email()
        exit(1)
    mylogs.info("Scheduling SUSE Live Patching initial rollout")

    server_list = {}
    pkg_list = []
    for a in result_systemlist:
        server_list[a['id']] = a['name']
       
    pkg_list, server_id_list = getpkg_servers_lists(server_list)
    mylogs.debug("Package list id: %s, Server list id %s"%(pkg_list, server_id_list))
    if len(pkg_list) and len(server_id_list) > 0:
        try:
            result_job = session.system.schedulePackageInstall(key, server_id_list, pkg_list, earliest_occurrence, True)
            mylogs.info("Job ID: %s" %(result_job))
        except Exception as e:
            mylogs.error("scheduling job failed %s." %(e))
    else:
        mylogs.info("Nothing to install. Either already installed or channels not available to the systems.")
    return "finished."

def schedule_klp_install_single(suma_data, servername):
    
    nowlater = datetime.datetime.now()
    earliest_occurrence = DateTime(nowlater)
    try:
        result_system_id = session.system.getId(key, servername)
    except Exception as e:
        mylogs.error("get systems id failed. %s" %(e))
        result2email()
        exit(1)
    mylogs.info("Scheduling SUSE Live Patching initial rollout to single node.")

    server_id_list = []
    pkg_list = []
    for a in result_system_id:
        server_id_list.append(a['id'])
       
    pkg_list, server_id_list = getpkg_servers_lists(server_id_list)
    mylogs.debug(pkg_list, server_id_list)
    if len(pkg_list) and len(server_id_list) > 0:
        try:
            result_job = session.system.schedulePackageInstall(key, server_id_list, pkg_list, earliest_occurrence, True)
            mylogs.info("Job ID: %s" %(result_job))
        except Exception as e:
            mylogs.error("scheduling job failed %s." %(e))
    else:
        mylogs.info("Nothing to install. Either already installed or channels not available to the systems.")
    return "finished."

if args.config:
    suma_data = get_login(args.config)
    session, key = login_suma(suma_data)
else:
    conf_file = "/root/suma_config.yaml"
    suma_data = get_login(conf_file)
    session, key = login_suma(suma_data)

if isNotBlank(args.group):
    result = schedule_klp_install(suma_data, args.group)
    mylogs.info(result)
elif isNotBlank(args.servername):
    result = schedule_klp_install_single(suma_data, args.servername)
    mylogs.info(result)
else:
    mylogs.error("group name is empty and also no single system name provided.")
    result2email()
    exit(1)
    
suma_logout(session, key)
result2email()