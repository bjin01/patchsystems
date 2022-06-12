#!/usr/bin/python

import subprocess
import argparse
#import getpass
import textwrap
import csv
#import time
import datetime
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
mylogs.addHandler(stream)

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
              python3.6 getcve_info.py --config /root/suma_config.yaml --cve CVE-2008-3270

              '''))

parser.add_argument("--config", help="enter the config file name that contains login information e.g. /root/suma_config.yaml",  required=False)
parser.add_argument("--cve", help="Enter the group name that you want to check.",  required=False)
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

def get_affectedsystems(advisory_nme):
    try:
        result_affectedsystems = session.errata.listAffectedSystems(key, advisory_nme)
    except Exception as e:
        mylogs.error("get affected systems failed. %s" %(e))
        result2email()
        suma_logout(session, key)
        exit(1)
    
    if len(result_affectedsystems) > 0:
        for i in result_affectedsystems:
            True
            #print(i)
    else:
        print("No effected systems found.")
    return

def get_systemname(id):
    try:
        result_system_name = session.system.getName(key, id)
    except Exception as e:
        mylogs.error("get systems name failed. %s" %(e))
        result2email()
        suma_logout(session, key)
        exit(1)
    return result_system_name['name']

def get_systemgroups(id):
    grouplist = []
    try:
        result_system_groups = session.system.listGroups(key, id)
    except Exception as e:
        mylogs.error("get systems groups failed. %s" %(e))
        result2email()
        suma_logout(session, key)
        exit(1)
    if len(result_system_groups) > 0:
        for i in result_system_groups:
            if i['subscribed'] == 1:
                grouplist.append(i['system_group_name'])

    return grouplist


def get_subscripedBaseChannel(id):
    try:
        result_basechannel = session.system.getSubscribedBaseChannel(key, id)
    except Exception as e:
        mylogs.error("get result_basechannel failed. %s" %(e))
        result2email()
        suma_logout(session, key)
        exit(1)
    #print(result_basechannel)
    if len(result_basechannel) > 0:
        return result_basechannel['name']

        """ for i in result_basechannel:
            print(i) """
    else:
        return "Nothing"
    return "Nothing"

def create_csv_report(finalresult):
    csvfile = "/var/log/cve_info.csv"
    if len(finalresult):
        with open(csvfile, 'w', newline='') as file:
            fieldnames = ['system_id', 'name', 'patch_name', 'patch_status', 'in_Channel', 'groups', 'base_channel', "comment"]
            writer = csv.writer(file)
            writer.writerow(fieldnames)
            for i in finalresult:
                newline = []
                patchnames = ""
                groups = ""
                in_channels = ""
                for p in i['patch_name']:
                    patchnames += p + " "
                for g in i['groups']:
                    groups += g + " "
                for c in i['in_Channel']:
                    in_channels += c + " "
                newline.append(i['system_id'])
                newline.append(i['name'])
                newline.append(patchnames)
                newline.append(i['patch_status'])
                newline.append(in_channels)
                newline.append(groups)
                newline.append(i['base_channel'])
                newline.append(i['comment'])
                writer.writerow(newline)
            print("Please find the csv file in: {}".format(csvfile))    
    return

def is_channel_in_subscribedChannels(systemid, channel_labels):
    channel_with_patch_found = False
    try:
        result_subscribed_channels = session.system.listSubscribedChildChannels(key, systemid)
    except Exception as e:
        mylogs.error("get result_subscribed_channels failed. %s" %(e))
    
    for s in result_subscribed_channels:
        for l in channel_labels:
            if s['label'] in l:
                channel_with_patch_found = True

    return channel_with_patch_found

def get_systempatch_status(cve):
    patchstatus_filter = ["AFFECTED_PATCH_INAPPLICABLE", "AFFECTED_PATCH_APPLICABLE", "NOT_AFFECTED", "PATCHED", "AFFECTED_PATCH_INAPPLICABLE_SUCCESSOR_PRODUCT"]
    try:
        result_systempatch_status = session.audit.listSystemsByPatchStatus(key, cve, patchstatus_filter)
    except Exception as e:
        mylogs.error("get system patch status failed. %s" %(e))
        print("Failed to query the {}, no info found".format(cve))
        result2email()
        suma_logout(session, key)
        exit(1)
    if len(result_systempatch_status) > 0:
        #print("----")
        #print("ID \tStatus \t\tChannel \tPatch_name")
        for i in result_systempatch_status:
            result_single = {}
            result_single['comment'] = ""
            result_single['system_id'] = i['system_id']
            result_single['name'] = get_systemname(i['system_id'])
            result_single['patch_status'] = i['patch_status']
            result_single['in_Channel'] = i['channel_labels']
            result_single['patch_name'] = i['errata_advisories']
            result_single['groups'] = get_systemgroups(i['system_id'])
            result_single['base_channel'] = get_subscripedBaseChannel(i['system_id'])
            if i['patch_status'] in "AFFECTED_PATCH_INAPPLICABLE_SUCCESSOR_PRODUCT":
               result_single['comment'] = "Patch available, but system needs a newer product."
            if i['patch_status'] in "AFFECTED_PATCH_APPLICABLE":
               result_single['comment'] = "Patch is available and channels is subscribed."
            finalresult.append(result_single)
    else:
        print("Nothing returned")
        
    create_csv_report(finalresult)
    return



def get_cve(cve):
    patch_list = {}
    try:
        result_cve = session.errata.findByCve(key, cve)
    except Exception as e:
        mylogs.error("get cve failed. %s" %(e))
        result2email()
        suma_logout(session, key)
        exit(1)
    
    if len(result_cve) > 0:
        print("----\n")
        for i in result_cve:
            
            #print("{}: {} - {} \t".format(i['advisory_name'], i['advisory_type'], i['advisory_synopsis']))
            get_affectedsystems(i['advisory_name'])     
    return True


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
        else:
            patch_list[j] = 0
        
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
        print("Get group failed: %s" % groupname)
        mylogs.error("get systems list from group failed. %s" %(e))
        result2email()
        suma_logout(session, key)
        exit(1)
    mylogs.info("List of Systems is ready.")

    server_list = {}
    patch_list = []
    for a in result_systemlist:
        server_list[a['id']] = a["name"]
       
    patch_list = get_servers_patches(server_list)
    # print(patch_list, server_id_list)
    if not args.headerOff:
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

if isNotBlank(args.cve):
    
    result = get_systempatch_status(args.cve)
    mylogs.info(result)
else:
    mylogs.info("group name is empty.")
    result2email()
    suma_logout(session, key)
    exit(1)
    
suma_logout(session, key)
result2email()