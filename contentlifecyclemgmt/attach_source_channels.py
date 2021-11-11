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
This scripts helps to attach source channels to clm project 
Sample command:
              python3 attach_source_channels.py --attach --config /root/suma_config.yaml 
              python3 attach_source_channels.py --detach --config /root/suma_config.yaml 
The script can attach source channels. '''))
parser.add_argument("--attach", action="store_true")
parser.add_argument("--detach", action="store_true")
parser.add_argument("--config", help="Enter the config file name that contains login and channel information e.g. /root/suma_config.yaml",  required=False)
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


def attach_source_channels(suma_data):
    sourceType = "software"

    print("Attaching source channels to project: %s " %(suma_data['clm_project']))
    for i in suma_data['sourceChannelLabels']:
        try:
            result_systemlist = session.contentmanagement.attachSource(key, suma_data['clm_project'], sourceType, i)
            print("%s" %(i))
        except:
            print("Attaching channel %s failed." %(i))
    return "finished."

def detach_source_channels(suma_data):
    sourceType = "software"

    print("Detaching source channels from project: %s " %(suma_data['clm_project']))
    for i in suma_data['sourceChannelLabels']:
        try:
            result_systemlist = session.contentmanagement.detachSource(key, suma_data['clm_project'], sourceType, i)
            print("%s" %(i))
        except:
            print("Detaching channel %s failed." %(i))
    return "finished."


if args.config:
    suma_data = get_login(args.config)
    session, key = login_suma(suma_data)
else:
    conf_file = "/root/suma_config.yaml"
    suma_data = get_login(conf_file)
    session, key = login_suma(suma_data)

if isNotBlank(suma_data['clm_project']):
    if args.attach:
        result = attach_source_channels(suma_data)
        print(result)
    if args.detach:
        result = detach_source_channels(suma_data)
        print(result)
else:
    print("clm_project label is empty.")
    exit(1)
    
suma_logout(session, key)
