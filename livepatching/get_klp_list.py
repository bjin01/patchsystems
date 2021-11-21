#!/usr/bin/python

import argparse,  getpass,  textwrap, time
import datetime
import yaml
import os
import subprocess
from xmlrpc.client import ServerProxy, Error, DateTime

class Password(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        if values is None:
            values = getpass.getpass()

        setattr(namespace, self.dest, values)

parser = argparse.ArgumentParser()
parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
This list live patching and send email. 
Sample command:
              python3 get_klp_list.py --config /root/suma_config.yaml --list_klp --email bo.jin@jinbo01.com
The script deployes klp. '''))
parser.add_argument("--servername", help="Enter exact system name shown in SUSE Manager to deploy klp to it. e.g. mytestserver.example.com",  required=False)
parser.add_argument("--list_klp", action="store_true")
parser.add_argument("--config", help="Enter the config file name that contains login and channel information e.g. /root/suma_config.yaml",  required=False)
parser.add_argument("--email", help="Enter email address you want to send list of live patching overview to",  required=False)
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
    print("Item---------------------------------------------")
    for a, b in dict_object.items():
        if isinstance(b, dict):
            for k, v in b.items():
                print("{:<20}".format(k), "{:<20}".format(v))
        else:
            print("{:<20}".format(a), "{:<20}".format(b))
        
    print("----------------------------------------------------")

def getpkg_servers_lists(mylist):
    pkgname = "patterns-lp-lp_sles"
    temp_pkg_list = []
    temp_server_list = []
    for i in mylist:
        try:
            temp_list = session.system.listLatestInstallablePackages(key, i)
        except:
            print("failed to obtain pkg list from %s" %(i))
            continue
        
        for s in temp_list:
            if s['name'].startswith(pkgname):
                print(s['name'], " : ", s['id'], " for systemid ", i)
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
        print("get systems list from group failed. %s" %(e))
        exit(1)
    print("Scheduling SUSE Live Patching initial rollout")

    server_id_list = []
    pkg_list = []
    for a in result_systemlist:
        server_id_list.append(a['id'])
       
    pkg_list, server_id_list = getpkg_servers_lists(server_id_list)
    print(pkg_list, server_id_list)
    if len(pkg_list) and len(server_id_list) > 0:
        try:
            result_job = session.system.schedulePackageInstall(key, server_id_list, pkg_list, earliest_occurrence, True)
            print("Job ID: %s" %(result_job))
        except Exception as e:
            print("scheduling job failed %s." %(e))
    else:
        print("Nothing to install. Either already installed or channels not available to the systems.")
    return "finished."

def schedule_klp_install_single(suma_data, servername):
    
    nowlater = datetime.datetime.now()
    earliest_occurrence = DateTime(nowlater)
    try:
        result_system_id = session.system.getId(key, servername)
    except Exception as e:
        print("get systems id failed. %s" %(e))
        exit(1)
    print("Scheduling SUSE Live Patching initial rollout to single node.")

    server_id_list = []
    pkg_list = []
    for a in result_system_id:
        server_id_list.append(a['id'])
       
    pkg_list, server_id_list = getpkg_servers_lists(server_id_list)
    print(pkg_list, server_id_list)
    if len(pkg_list) and len(server_id_list) > 0:
        try:
            result_job = session.system.schedulePackageInstall(key, server_id_list, pkg_list, earliest_occurrence, True)
            print("Job ID: %s" %(result_job))
        except Exception as e:
            print("scheduling job failed %s." %(e))
    else:
        print("Nothing to install. Either already installed or channels not available to the systems.")
    return "finished."

def list_klp(suma_data):
    
    klp = "kernel-livepatch-"
    
    try:
        result_systemlist = session.system.listSystems(key)
        #print("Job ID: %s" %(result_systemlist))
    except Exception as e:
        print("get systems list failed %s." %(e))
    
    file_of_list = open("/var/log/klp_list.txt", "w")
    file_of_list.write("Overview of SUSE Live Patching on systems.\n")
    for i in result_systemlist:
        klp_pkgs= []
        klp_pkg = ""
        try:
            result_system_kernel = session.system.getRunningKernel(key, i['id'])
        except Exception as e:
            print("get systems kernel failed %s." %(e))
        try:
            result_system_klp = session.system.getKernelLivePatch(key, i['id'])
        except Exception as e:
            print("get systems kernel failed %s." %(e))
        try:
            result_installed = session.system.listInstalledPackages(key, i['id'])
            if result_installed:
                for s in result_installed:
                    if s['name'].startswith(klp):
                        klp_pkg = s['name']
                        klp_pkgs.append(klp_pkg)
        except Exception as e:
            print("get systems kernel failed %s." %(e))
        print('{:<30} {:>30} ---- {:20} - {}'.format(i['name'], result_system_kernel, result_system_klp, klp_pkgs))
        if isNotBlank(result_system_klp):
            file_of_list.write('{:<30} {:>30} ---- {:20} - {}\n'.format(i['name'], result_system_kernel, result_system_klp, klp_pkgs))
        else:
            file_of_list.write('{:<30} {:>30} ---- No Live Patch installed\n'.format(i['name'], result_system_kernel))
    file_of_list.close()
    return

def send_email(email_addr):
    subject = "SUSE Manager - Live Patching List"
    cmd1 = ['cat', '/var/log/klp_list.txt']
    proc1 = subprocess.run(cmd1, stdout=subprocess.PIPE)
    cmd2 = ['mutt', '-s', subject, email_addr]
    proc2 = subprocess.run(cmd2, input=proc1.stdout)
    return

if args.config:
    suma_data = get_login(args.config)
    session, key = login_suma(suma_data)
else:
    conf_file = "/root/suma_config.yaml"
    suma_data = get_login(conf_file)
    session, key = login_suma(suma_data)

if isNotBlank(args.group):
    result = schedule_klp_install(suma_data, args.group)
    print(result)
elif isNotBlank(args.servername):
    result = schedule_klp_install_single(suma_data, args.servername)
    print(result)
elif args.list_klp:
    list_klp(suma_data)
    send_email(args.email)
else:
    print("group name is empty and also no single system name provided.")
    exit(1)
    
suma_logout(session, key)
