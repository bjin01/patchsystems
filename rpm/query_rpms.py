#!/usr/bin/python3.6 
import rpm
from xmlrpc.client import ServerProxy, DateTime
import yaml
import os
import hashlib
import re
import logging
import argparse,  getpass,  textwrap, sys

pid = os.getpid()
logfilename = "/var/log/rhn/query_rpms.log"
mylogs = logging.getLogger(__name__)
mylogs.setLevel(logging.DEBUG)

file = logging.FileHandler(logfilename, mode='w')
file.setLevel(logging.DEBUG)

fileformat = logging.Formatter("%(asctime)s:[pid %(process)d]:%(levelname)s: - %(message)s",datefmt="%H:%M:%S")
file.setFormatter(fileformat)

#handler for sending messages to console stdout
stream = logging.StreamHandler()
streamformat = logging.Formatter("%(asctime)s:[pid %(process)d]:%(filename)s:%(levelname)s:%(message)s",datefmt="%H:%M:%S")


class Password(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        if values is None:
            values = getpass.getpass()
        setattr(namespace, self.dest, values)

parser = argparse.ArgumentParser()
#parser.add_argument("-v", "--verbosity", action="count", default=0)
parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
This scripts queries job status by passing jobstatus json formatted file with jobid and serverid. 
Sample command:
              python3.6 jobstatus.py -c /root/suma_config.yaml -f ./jobs.json -o /var/log/jobstatus_list.log\n \
Check Job status of the systems. The output will be shown in terminal and written to a local file 'jobstatus_list.log' ''')) 

parser.add_argument("-v", "--verbose", help="show more output to stdout",  required=False)
parser.add_argument("-c", "--config", help="enter the config file name that contains login information e.g. /root/suma_config.yaml",  required=False)
parser.add_argument("-l", "--channel_label", help="Enter the channel label name e.g. mychannel_sles15sp3-x86",  required=True)

args = parser.parse_args()

def get_rpm_details():
    ts = rpm.TransactionSet()
    mi = ts.dbMatch()
    for h in mi:
        name = str(h['name'], "utf-8")
        version = str(h['version'], "utf-8")
        release = str(h['release'], "utf-8")
        print("%s-%s-%s" % (name, version, release))
    return

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

def get_channel(search_channel):
    list_of_ch_result = []
    set_ch_list = set()
    for i in list_of_channels:
        chname = "^" + search_channel + "$"
        if re.search(chname, i['label']):
            mylogs.debug("Channel. {}".format(i['label']))
            set_ch_list.add(i['label'])
            if i['parent_label'] == "":
                mylogs.debug("This is a parent channel. {}".format(i['label']))
                set_ch_list.add(i['label'])
                
        if re.search(chname, i['parent_label']):
            mylogs.debug(i['label'])
            set_ch_list.add(i['label'])
    
    list_of_ch_result = list(set_ch_list)
    return list_of_ch_result

def get_listAllPackages(channels_list):
    package_id_list_all = []
    
    for i in channels_list:
        package_id_list = []
        try:
            packagelist = session.channel.software.listAllPackages(key, i)
            for p in packagelist:
                package_id_list.append(p['id'])
            mylogs.debug("{}: {}".format(i, len(package_id_list)))
            
        except:
            mylogs.info("Error getting packages from {}".format(packagelist))
        package_id_list_all.extend(package_id_list)
    return package_id_list_all

def check_checksum(file):
    md5_hash = hashlib.new("sha256")
    a_file = open(file, "rb")
    content = a_file.read()
    md5_hash.update(content)
    digest = md5_hash.hexdigest()

    return digest

def check_rpm_location(package_details):
    rpm_path = "/var/spacewalk/" + package_details['path']
    rpm_checksum = package_details['checksum']
    rpm_name = package_details['name']

    if not os.path.exists(rpm_path):
        mylogs.info("\033[93mMissing: {} {}\033[00m".format(package_details['name'], package_details['version']))
        mylogs.info("Package is needed in channels:")
        for i in package_details["providing_channels"]:
            mylogs.debug("\t\033[93m{}\033[00m".format(i))
        return
    if not check_checksum(rpm_path) == rpm_checksum:
        mylogs.info("033[93mError: checksum not matching: {}\033[00m".format(rpm_name))
        print("Package is nneded in channels:")
        for i in package_details["providing_channels"]:
            mylogs.debug("\t\033[93m{}\033[00m".format(i))
    return

def check_rpm_file(list_of_package_id):
    mylogs.info("Now checking the package rpm files on local disk. {}".format(len(list_of_package_id)))
    mylogs.info("---\033[93mWe check if files exist in /var/spacewalk and if checksum matches the same in SUMA DB.\033[00m---")
    mylogs.info("----------------------------------------------------------")
    times = 8
    message_counter = 0
    if len(list_of_package_id) > 64:
        message_counter = int(len(list_of_package_id) / times)
        counter = message_counter
    else:
        counter = 0
    remaining_counter = len(list_of_package_id)
    for id in list_of_package_id:
        
        try:
            package_details = session.packages.getDetails(key, id)
            _ = check_rpm_location(package_details)
        except:
            mylogs.info("Erros getting package details for: {}".format(id))
        if counter > 0:
            counter -= 1
        remaining_counter -= 1
        #print(remaining_counter)
        if counter == 0:
            mylogs.info("We are still checking... Please wait...{} packages remaing.".format(remaining_counter))
            counter = message_counter

    return

if __name__ == '__main__':
    mylogs.addHandler(file)
    if args.verbose in "debug":
        stream.setLevel(logging.DEBUG)
        mylogs.addHandler(stream)
    else:
        stream.setLevel(logging.INFO)
        mylogs.addHandler(stream)

    if args.config:
        suma_data = get_login(args.config)
        session, key = login_suma(suma_data)
        mylogs.info("SUMA Login successful.")
    else:
        conf_file = "/root/suma_config.yaml"
        suma_data = get_login(conf_file)
        session, key = login_suma(suma_data)
        mylogs.info("SUMA Login successful.")
    
    if args.channel_label:
        try:
            list_of_channels = session.channel.listSoftwareChannels(key)
        except:
            mylogs.info("Erros gettings channels. {}".format(args.channel_label))
            suma_logout(session, key)
            sys.exit(1)
        channels_return = get_channel(args.channel_label)
        #print(channels_return)
        allpackages_id_list = get_listAllPackages(channels_return)
        mylogs.info("Total no of package IDs: {}".format(len(allpackages_id_list)))
        _ = check_rpm_file(allpackages_id_list)
        mylogs.info("That's it.")
        suma_logout(session, key)