import argparse,  getpass,  textwrap, time
import datetime
import yaml
import os
import re
import subprocess
from xmlrpc.client import ServerProxy, Error, DateTime

class Password(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        if values is None:
            values = getpass.getpass()

        setattr(namespace, self.dest, values)

parser = argparse.ArgumentParser()
parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
This script creates activation keys based on an predefined input file. 
Sample command:
              python3 create_activationkeys.py --config /root/suma_config.yaml
              python3 create_activationkeys.py --config /root/suma_config.yaml --delete_keys
The script creates or delete activationkeys in SUMA. '''))
parser.add_argument("--config", help="Enter the config file name that contains login and channel information e.g. /root/suma_config.yaml",  required=False)
parser.add_argument("--delete_keys", action="store_true")


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
    print("Item---------------------------------------------")
    for a, b in dict_object.items():
        if isinstance(b, dict):
            for k, v in b.items():
                print("{:<20}".format(k), "{:<20}".format(v))
        else:
            print("{:<20}".format(a), "{:<20}".format(b))
        
    print("----------------------------------------------------")

def verify_actkeys(actkey_list):
    verify_actkeys_list = {}
    try:
        existing_keylist = session.activationkey.listActivationKeys(key)
    except:
        print("failed to get activationkey list")
    for h, j in actkey_list.items():
        key_exist = False
        for s in existing_keylist:
            if re.search(h, s['key']):
                print("found existing key %s" %(h))
                key_exist = True
        
        try:
            verify_parent_channel = session.channel.software.isExisting(key, j)
            if verify_parent_channel:
                channel_ok = True
            else:
                print("parent channel doesn't exist: %s" %(j))
                print("The activationkey %s will not be created." %(h))
        except:
            print("failed to get activationkey list")
        
        if not key_exist:
            channel_ok = False
            try:
                verify_parent_channel = session.channel.software.isExisting(key, j)
                if verify_parent_channel:
                    channel_ok = True
                else:
                    print("parent channel doesn't exist: %s" %(j))
                    print("The activationkey %s will not be created." %(h))
            except:
                print("failed to get activationkey list")
            if channel_ok:
                verify_actkeys_list[h] = j
    return verify_actkeys_list

def create_actkey(suma_data):
    actkey_list = {}
    for i in suma_data['activationkeys']:

        for a, b in i.items():
            
            #print(a, b)
            try:
                temp_list = session.contentmanagement.listProjectEnvironments(key, a)
                for x in temp_list:
                    parent_ch_name = a + "-" + x['label'] + "-" + b
                    keyname = a + "-" + x['label']
                    actkey_list[keyname] = parent_ch_name

            except:
                print("failed to get project environments:  %s" %(a))
    
    
    
    #print(verified_actkey_list)
    if not args.delete_keys:
        verified_actkey_list = verify_actkeys(actkey_list)
        create_keys_final(verified_actkey_list)
    
    if args.delete_keys:
        delete_keys_final(actkey_list)
    return

def delete_keys_final(verified_actkey_list):
    for c, _ in verified_actkey_list.items():
        try:
            actkey_name = "1-" + c
            result_keycreate = session.activationkey.delete(key, actkey_name)
            print("Activationkey %s deleted." %actkey_name)
        except:
            print("Failed to delete activationkey: %s" %c)
    return

def create_keys_final(verified_actkey_list):
    for c, d in verified_actkey_list.items():
        print("activationkey: %s \t%s" %(c, d))
        try:
            childchannel_list = []
            entitlement_list = []
            actkey_name = c
            actkey_name_description = c
            result_keycreate = session.activationkey.create(key, actkey_name, actkey_name_description, d, entitlement_list, False)
            #time.sleep(5)
            temp_childchannel_list = session.channel.software.listChildren(key, d)
            for t in temp_childchannel_list:
                childchannel_list.append(t['label'])
            #print("child channels for %s: \t%s" % (d, childchannel_list))
            try:
                real_keyname = "1-" + c
                result_add_childchannels = session.activationkey.addChildChannels(key, real_keyname, childchannel_list)
                print("Key %s created. Status code: %s" %(real_keyname,result_add_childchannels))
                print("Child Channels added to %s" %(d))
            except:
                print("failed to add child channels to %s" %(d))

        except:
            print("failed to create activationkey:  %s" %(c))

    return

def isNotBlank(myString):
    if myString and myString.strip():
        #myString is not None AND myString is not empty or blank
        return True
    #myString is None OR myString is empty or blank
    return False

if args.config:
    suma_data = get_login(args.config)
    session, key = login_suma(suma_data)
    create_actkey(suma_data)
else:
    conf_file = "/root/suma_config.yaml"
    suma_data = get_login(conf_file)
    session, key = login_suma(suma_data)
    create_actkey(suma_data)

    
suma_logout(session, key)
