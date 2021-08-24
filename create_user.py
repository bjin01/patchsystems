#!/usr/bin/env python3

import yaml
import os 
import argparse
import getpass
import textwrap
import subprocess
from datetime import datetime,  timedelta
from xmlrpc.client import ServerProxy, Error

def get_login(path):
    
    if path == "":
        path = os.path.join(os.environ["HOME"], "suma_config.yaml")
    with open(path) as f:
        login = yaml.load_all(f, Loader=yaml.FullLoader)
        for a in login:
            login = a

    return login

def login_suma(login):
    MANAGER_URL = "http://"+ login['suma_host'] +"/rpc/api"
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

def get_suma_users(session, key):
    suma_users = session.users.listUsers(key)
    for i in suma_users:
        print("login: %s " % i['login'])
    return suma_users

def get_ad_users(ad_group):
    cmd = 'getent group'
    temp = subprocess.Popen([cmd, ad_group], stdout = subprocess.PIPE) 
        # get the output as a string
        output = str(temp.communicate())
    print("users from AD: %s" % output)

    return output

parser = argparse.ArgumentParser()
#parser.add_argument("-v", "--verbosity", action="count", default=0)
parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
This script creates users from AD and delete users which does not exist anymore. 
Sample command:
              python3 create_user.py -f suma_config.yaml \n \
''')) 
parser.add_argument("-c", "--config", help="Enter config file in yaml format that holds login.",  default='./suma_config.yaml',  required=True))
args = parser.parse_args()

if __name__ == '__main__': 
    suma_login = get_login(args.config)
    session, key = login_suma(suma_login)
    suma_users = get_suma_users(session, key)
    ad_users = get_ad_users(ad_group)

    client.close()