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


logfilename = "/var/log/automic_suma_checkjobstatus.log"
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
This Script checks job status.

You need a suma_config.yaml file with login and email notification address.
If email notification will be used then you need to have mutt email client installed. 

Sample suma_config.yaml:
suma_host: mysumaserver.mydomain.local
suma_user: <USERNAME>
suma_password: <PASSWORD>
notify_email: <EMAIL_ADDRESS>

Sample command:
              python3.6 checkjobstatus.py --config suma_config.yaml --jobid 12345
              
              or 

              python3.6 checkjobstatus.py --config suma_config.yaml --jobid 12345 --email
'''))

parser.add_argument("--config", help="enter the config file name that contains login information e.g. /root/suma_config.yaml",  required=False)
parser.add_argument("--jobid", help="Enter the ID of the job you want to query status.",  required=True)
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
            subject = "SUSE Manager - Check Job status."
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

def isNotBlank(myString):
    if myString and myString.strip():
        #myString is not None AND myString is not empty or blank
        return True
    #myString is None OR myString is empty or blank
    return False

def jobstatus(jobid):
    
    nowlater = datetime.datetime.now()
    earliest_occurrence = DateTime(nowlater)
    try:
        result_inprogress_actions = session.schedule.listInProgressActions(key)
    except Exception as e:
        mylogs.error("get inProgress Actions failed. %s" %(e))
        exit(1)
    
    try:
        result_failed_actions = session.schedule.listFailedActions(key)
    except Exception as e:
        mylogs.error("get result_failed_actions Actions failed. %s" %(e))
        exit(1)
    
    try:
        result_completed_actions = session.schedule.listAllCompletedActions(key)
    except Exception as e:
        mylogs.error("get result_completed_actions Actions failed. %s" %(e))
        exit(1)

    mylogs.info("Job Status collected.")

    if result_inprogress_actions:
        if len(result_inprogress_actions) > 0:
            
            for p in result_inprogress_actions:
               if p['id'] == int(jobid):
                   mylogs.info("Job %d is in-progress, Job Name: %s" %(int(jobid), p['name']))
                   print("%s: %d: inprogress" %(p['type'], int(jobid)))
                   return "Job inprogress"
                   

    if result_failed_actions:
        if len(result_failed_actions) > 0:
            
            for p in result_failed_actions:
               if p['id'] == int(jobid):
                   mylogs.info("Job %d is failed, Job Name: %s" %(int(jobid), p['name']))
                   print("%s: %d: failed" %(p['type'], int(jobid)))
                   return "Job failed"
                   

    if result_completed_actions:
        if len(result_completed_actions) > 0:
            
            for p in result_completed_actions:
               if p['id'] == int(jobid):
                   mylogs.info("Job %d is completed, Job Name: %s" %(int(jobid), p['name']))
                   print("%s: %d: completed" %(p['type'], int(jobid)))
                   return "Job completed"
                   

    return "finished."


if args.config:
    suma_data = get_login(args.config)
    session, key = login_suma(suma_data)
else:
    conf_file = "/root/suma_config.yaml"
    suma_data = get_login(conf_file)
    session, key = login_suma(suma_data)

if isNotBlank(args.jobid):
    result = jobstatus(args.jobid)
    mylogs.info(result)
else:
    mylogs.info("systemname name is empty.")
    result2email()
    exit(1)
    
suma_logout(session, key)
result2email()