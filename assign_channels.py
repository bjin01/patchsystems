#!/usr/bin/python

import argparse,  getpass,  textwrap, time
import datetime
import yaml
import os
from xmlrpc.client import ServerProxy, Error, DateTime

class Password(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        if values is None:
            values = getpass.getpass()

        setattr(namespace, self.dest, values)

parser = argparse.ArgumentParser()
parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
This scripts helps to change channel assignment. 
Sample command:
              python3 clm_run.py --group testsystems
The script can changes channel assignment for given group and channels. '''))

parser.add_argument("--group", help="Enter the group name for which systems of a group you want to change channels. e.g. testsystems",  required=False)
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

def isNotBlank(myString):
    if myString and myString.strip():
        #myString is not None AND myString is not empty or blank
        return True
    #myString is None OR myString is empty or blank
    return False


def assigne_channels(suma_data, groupname):
    nowlater = datetime.datetime.now()
    earliest_occurrence = DateTime(nowlater)
    result_systemlist = session.systemgroup.listSystemsMinimal(key, groupname)
    print("changing channels for: ")
    for i in result_systemlist:
        try:
            result_change_channels = session.system.scheduleChangeChannels(key, i['id'], suma_data['baseChannelLabel'], suma_data['childChannelLabels'], earliest_occurrence)
            print("%s" %(i['name']))
        except:
            print("change channels for %s failed." %(i['name']))
    return "finished."

conf_file = "/root/suma_config.yaml"
suma_data = get_login(conf_file)
session, key = login_suma(suma_data)

if args.group:
    result = assigne_channels(suma_data, args.group)
    print(result)
    
suma_logout(session, key)
