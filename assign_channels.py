#!/usr/bin/python

import argparse,  getpass,  textwrap, time
import datetime
import yaml
import os
from xmlrpc.client import ServerProxy, Error

class Password(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        if values is None:
            values = getpass.getpass()

        setattr(namespace, self.dest, values)

parser = argparse.ArgumentParser()
parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
This scripts helps to change channel assignment. 
Sample command:
              python clm_run.py --listProject
              python clm_run.py --listEnvironment --projLabel myprojlabel
              python clm_run.py --build --projLabel myprojlabel \n \
              python clm_run.py --promote --projLabel myprojlabel --envLabel teststage  \n \
              python clm_run.py --check_status --projLabel myprojlabel --envLabel teststage  \n \
The script can build project, update and promote stages or environments.
Check taskomatic logs in order to monitor the status of the build and promote tasks e.g. # tail -f /var/log/rhn/rhn_taskomatic_daemon.log. '''))

parser.add_argument("--listProject", action="store_true")
parser.add_argument("--listEnvironment", action="store_true")
parser.add_argument("--check_status", action="store_true")
parser.add_argument("--build", action="store_true")
parser.add_argument("--promote", action="store_true")
parser.add_argument("--projname", help="Enter the desired project name. e.g. myproject",  required=False)
parser.add_argument("--projLabel", help="Enter the project label. e.g. mytest",  required=False)
parser.add_argument("--envLabel", help="Enter the environment label. e.g. dev",  required=False)
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
    MANAGER_URL = "https://"+ login['suma_host'] +"/rpc/api"
    MANAGER_LOGIN = login['suma_user']
    MANAGER_PASSWORD = login['suma_password']
    SUMA = "http://" + login['suma_user'] + ":" + login['suma_password'] + "@" + login['suma_host'] + "/rpc/api"
    with ServerProxy(SUMA) as session_client:

    #session_client = xmlrpclib.Server(MANAGER_URL, verbose=0)
        session_key = session_client.auth.login(MANAGER_LOGIN, MANAGER_PASSWORD)
    return session_client, session_key

def suma_logout(session, key):
    session.auth.logout(key)
    return

def printdict(dict_object):
    for i in dict_object:
        print("Item---------------------------------------------")
        for k, v in i.items():
            if k in "lastBuildDate":
                converted = datetime.datetime.strptime(v.value, "%Y%m%dT%H:%M:%S")
                print ("{:<20}".format(k), "{:<20}".format(converted.strftime("%d.%m.%Y, %H:%M")))
            else:
                print ("{:<20}".format(k), "{:<20}".format(v))
        print("----------------------------------------------------")


conf_file = "/root/suma_config.yaml"
suma_login = get_login(conf_file)
session, key = login_suma(suma_login)



    
suma_logout(session, key)
