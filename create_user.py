#!/usr/bin/env python3

import yaml
import os
import argparse
import getpass
import textwrap
import subprocess
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
        session_key = session_client.auth.login(MANAGER_LOGIN, MANAGER_PASSWORD)
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

def new_users(ad_users, suma_users, session, key, role):
    email_domain = "@richemont.com"
    default_pwd = "asdfasdf"
    set_ad_users = set(ad_users)
    set_suma_users = set(suma_users)
    new_diff_users = set_ad_users.difference(set_suma_users)
    print("diff ad_users: %s" % list(new_diff_users))
    for i in list(new_diff_users):
        email = i + email_domain
        ret = session.user.create(key, i, default_pwd, i, i, email, 1)
        if ret == 1:
            print("User %s created." % i)
            add_roles(role, i, session, key)
        else:
            print("Failed to create user %s." % i)
    return

def add_roles(roles, login, session, key):
    if roles in "admin":
        role_list = ['org_admin', 'channel_admin', 'config_admin', 'system_group_admin',]
        for r in role_list:
            ret = session.user.addRole(key, login, r)
            if ret == 1:
                print("User %s role %s added." % (login, r))
            else:
                print("Failed to add user %s role %s." % (login, r))

    elif roles in "normal-user":
        role_list = ['system_group_admin']
        for r in role_list:
            ret = session.user.addRole(key, login, r)
            if ret == 1:
                print("User %s role %s added." % (login, r))
            else:
                print("Failed to add user %s role %s." % (login, r))

    return

def delete_users(ad_users, suma_users, session, key):
    set_ad_users = set(ad_users)
    set_suma_users = set(suma_users)
    new_diff_users = set_suma_users.difference(set_ad_users)
    print("diff to delete users: %s" % list(new_diff_users))
    for i in list(new_diff_users):
        ret = session.user.delete(key, i)
        if ret == 1:
            print("User %s deleted." % i)
        else:
            print("Failed to delete user %s." % i)
    return

def list_roles(session, key):
    role_list = session.user.listAssignableRoles(key)
    #print("user roles: %s" % role_list)
    return

parser = argparse.ArgumentParser()
#parser.add_argument("-v", "--verbosity", action="count", default=0)
parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
This script creates users from AD and delete users which does not exist anymore.
Sample command:
              python3 create_user.py -c ./suma_config.yaml -g susemanager -r admin \n \

If pam users from the given AD group is missing those users will be deleted from SUMA automatically.
'''))
parser.add_argument("-c", "--config", help="Enter config file in yaml format that holds login.",  default='./suma_config.yaml',  required=True)
parser.add_argument("-g", "--group", help="Enter AD group name.",  default='testgroup',  required=True)
parser.add_argument("-r", "--role", help="Enter role name 'admin' or default 'normal-user'.",  default='normal-user',  required=False)
args = parser.parse_args()

if __name__ == '__main__':
    suma_login = get_login(args.config)
    session, key = login_suma(suma_login)
    suma_users = get_suma_users(session, key)
    ad_users = get_ad_users(args.group)
    # print("suma users: %s" % suma_users)
    # print("AD users: %s" % ad_users)
    new_users(ad_users, suma_users, session, key, args.role)
    delete_users(ad_users, suma_users, session, key)
    list_roles(session, key)
    suma_logout(session, key)
