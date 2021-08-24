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
        print("%s %s %s" % (login['suma_host'], login['suma_user'], login['suma_password']))
        session_key = session_client.auth.login(MANAGER_LOGIN, MANAGER_PASSWORD)
        print("sessionkey: %s" % session_key)
    return session_client, session_key

def suma_logout(session, key):
    session.auth.logout(key)
    return

def get_suma_users(session, key):
    suma_users = session.user.listUsers(key)
    suma_user_list = []
    for i in suma_users:
         #print("login: %s " % i['login'])
         user_details = session.user.getDetails(key, i['login'])
         if user_details['use_pam']:
             suma_user_list.append(i['login'])
    return suma_user_list

def get_ad_users(ad_group):
    cmd = '/usr/bin/getent'

    ps = subprocess.Popen([cmd, 'group', ad_group], stdout=subprocess.PIPE)
    cut_output = subprocess.Popen(['/usr/bin/cut', '-f4', '-d:'],
                              stdin=ps.stdout, stdout=subprocess.PIPE)
    ps.stdout.close()
    output = cut_output.communicate()[0]
    tempstring = output.decode("utf-8")
    tempstring = tempstring.rstrip("\n")
    ad_users = tempstring.split(",")
    return ad_users

def new_users(ad_users, suma_users, session, key):
    email_domain = "@richemont.com"
    default_pwd = "asdfasdf"
    set_ad_users = set(ad_users)
    set_suma_users = set(suma_users)
    new_diff_users = set_ad_users.difference(set_suma_users)
    print("diff ad_users: %s" % list(new_diff_users))
    for i in list(new_diff_users):
        email = i + email_domain
        print("email address is: %s" % email)
        ret = session.user.create(key, i, default_pwd, i, i, email, 1)
        if ret == 1:
            print("User %s created." % i)
    return

def delete_users(ad_users, suma_users, session, key):
    set_ad_users = set(ad_users)
    set_suma_users = set(suma_users)
    new_diff_users = set_suma_users.difference(set_ad_users)
    print("diff to delete users: %s" % list(new_diff_users))

    return

parser = argparse.ArgumentParser()
#parser.add_argument("-v", "--verbosity", action="count", default=0)
parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
This script creates users from AD and delete users which does not exist anymore.
Sample command:
              python3 create_user.py -f suma_config.yaml \n \
'''))
parser.add_argument("-c", "--config", help="Enter config file in yaml format that holds login.",  default='./suma_config.yaml',  required=True)
parser.add_argument("-g", "--group", help="Enter AD group name.",  default='testgroup',  required=True)
args = parser.parse_args()

if __name__ == '__main__':
    suma_login = get_login(args.config)
    session, key = login_suma(suma_login)
    suma_users = get_suma_users(session, key)
    ad_users = get_ad_users(args.group)
    print("suma users: %s" % suma_users)
    print("AD users: %s" % ad_users)
    new_users(ad_users, suma_users, session, key)
    delete_users(ad_users, suma_users, session, key)
    suma_logout(session, key)
