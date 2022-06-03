#!/usr/bin/python
from xmlrpc.client import ServerProxy, DateTime
import yaml
import argparse,  getpass,  textwrap,  json, sys
import logging
import os
from datetime import datetime,  timedelta
from collections import defaultdict
#from array import *

pid = os.getpid()
logfilename = "/var/log/rhn/upgrade_systems_byGroup_withReboot.log"
mylogs = logging.getLogger(__name__)
mylogs.setLevel(logging.DEBUG)

file = logging.FileHandler(logfilename, mode='w')
file.setLevel(logging.DEBUG)

fileformat = logging.Formatter("%(asctime)s:[pid %(process)d]:%(levelname)s: - %(message)s",datefmt="%H:%M:%S")
file.setFormatter(fileformat)

#handler for sending messages to console stdout
stream = logging.StreamHandler()
streamformat = logging.Formatter("%(asctime)s:[pid %(process)d]:%(filename)s:%(levelname)s:%(message)s",datefmt="%H:%M:%S")
stream.setLevel(logging.DEBUG)
#stream.setFormatter(streamformat)

class Password(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        if values is None:
            values = getpass.getpass()
        setattr(namespace, self.dest, values)

parser = argparse.ArgumentParser()
reboot_parser = argparse.ArgumentParser()
#parser.add_argument("-v", "--verbosity", action="count", default=0)
parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
This scripts schedules upgrade deployment jobs for given group's systems' in given hours from now on. A reboot will be scheduled as well. 
Sample command: \
upgrades active systems from group in 2 hours from now, no-reboot, for any systems only. \
              python3.6 upgrade_systems_byGroup_withReboot.py --config /root/suma_config.yaml -g test2 -o 2 --no_reboot \n \

Upgrade active systems from group in 2 hours from now, with reboot at specified date time, for any systems.\
              python3.6 upgrade_systems_byGroup_withReboot.py --config /root/suma_config.yaml -g test2 -o 2 -r -sr '15:30 20-06-2022'  \n \
Check Job status of the system. ''')) 

parser.add_argument("-v", "--verbose", help="show more output to stdout",  required=False)
parser.add_argument("--config", help="enter the config file name that contains login information e.g. /root/suma_config.yaml",  required=False)
parser.add_argument("-g", "--group_name", help="Enter a valid groupname. e.g. DEV-SLES12SP3 ",  required=True)
parser.add_argument("-o", "--in_hours", help="in how many hours from now should the job be started. e.g. 2 ",  required=False)
parser.add_argument("-sr", "--schedule_reboot", help="when it should reboot in format 15:30 20-04-1970",  required=False)

reboot_parser = parser.add_mutually_exclusive_group(required=True)
reboot_parser.add_argument("-r", '--reboot', help="either -r or -no-r must be specified to decide reboot or no-reboot.", dest='reboot', action='store_true')
reboot_parser.add_argument("-no_r", '--no_reboot', help="either -r or -no_r must be specified to decide reboot or no_reboot.", dest='no_reboot', action='store_true')
parser.set_defaults(reboot=False)
args = parser.parse_args()

mylogs.addHandler(file)
if args.verbose:
    mylogs.addHandler(stream)

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

def compare_upgrade_and_reboot_time():
    mylogs.info("Desired Upgrade start time: %s, Reboot start time: %s" %( check_install_time, check_schedule_reboot_time))
    if check_install_time and check_schedule_reboot_time:
        if check_schedule_reboot_time <= check_install_time:
            mylogs.error("Error: Your desired reboot schedule time happens earlier than your desired install time. That is not a good idea.")
            sys.exit(1)
        elif check_schedule_reboot_time <= datetime.now():
            mylogs.error("Error: Your desired reboot schedule time happens earlier than current time. That is not a good idea.")
            sys.exit(1)
    return

if args.in_hours:
    check_install_time = datetime.now() + timedelta(hours=int(args.in_hours))
else:
    check_install_time = datetime.now()

if args.schedule_reboot and args.reboot:
    check_schedule_reboot_time = datetime.strptime(args.schedule_reboot, "%H:%M %d-%m-%Y")
if args.reboot == True and not args.schedule_reboot:
    check_schedule_reboot_time = check_install_time + timedelta(hours=int(1))

if not args.no_reboot:
    compare_upgrade_and_reboot_time()

if args.config:
    suma_data = get_login(args.config)
    session, key = login_suma(suma_data)
    mylogs.info("SUMA Login successful.")
else:
    conf_file = "/root/suma_config.yaml"
    suma_data = get_login(conf_file)
    session, key = login_suma(suma_data)
    mylogs.info("SUMA Login successful.")

earliest_occurrence_upgradejob = DateTime(check_install_time)
allgroups = session.systemgroup.listAllGroups(key)

joblist = []
joblist_reboot = []
nested_dict = lambda: defaultdict(nested_dict)
jobsdict = nested_dict
jobsdict = {}
error1 = 0


def scheduleReboot(serverid,  servername):
    earliest_occurrence_reboot = DateTime(check_schedule_reboot_time)
    reboot_jobid = session.system.scheduleReboot(key, serverid, earliest_occurrence_reboot)
    try: 
        if reboot_jobid:
            system_name = session.system.getName(key, serverid)
            mylogs.info("Reboot Job ID %s for %s %s has been created" %(str(reboot_jobid),  (str(serverid)), system_name['name']))
            jobsdict[servername]['Reboot_jobs']  = {}
            jobsdict[servername]['serverid'] = serverid
            jobsdict[servername]['Reboot_jobs'][reboot_jobid] = 'pending'

    except NameError:
        mylogs.info("No reboot job created.")
        sys.exit(1)
    
    
def json_write(mydict):
    json_file = "upgrade_jobs.json"
    with open(json_file, "w") as write_file:
        json.dump(mydict, write_file,  indent=4)
    mylogs.info("Job Data has been written to {}".format(json_file))

def upgrade_os(e, pkg_upgradelist, earliest_occurrence):
    upgradelist = session.system.listLatestUpgradablePackages(key, e)
    system_name = session.system.getName(key, e)
    if not upgradelist:
        mylogs.info("All good. No upgrades needed:\t %s" %(system_name['name']))
        
    if len(upgradelist) == 0:
        mylogs.info("All good. upgradelist - No upgrades. \t %s" %(system_name['name']))
        
        
    for s in upgradelist:
        pkg_upgradelist.append(s['to_package_id'])
    if len(pkg_upgradelist) > 0:        
        system_actionid = session.system.schedulePackageInstall(key, e, pkg_upgradelist, earliest_occurrence)
        del pkg_upgradelist
        system_name = session.system.getName(key, e)
        jobsdict[system_name['name']]={}
        jobsdict[system_name['name']]['upgrade_jobs']  = {}
        jobsdict[system_name['name']]['serverid']= e
    
        jobsdict[system_name['name']]['upgrade_jobs'][system_actionid] =  'pending'
        mylogs.info("Job ID %s for %s %s has been created" %(str(system_actionid),  (str(e)), system_name['name']))
        if args.reboot == True:
            scheduleReboot(e,  system_name['name'])
    else:
        mylogs.info("No package to upgrade.")   

if args.group_name:
    grpfound = None
    for a in allgroups:
        
        if a['name'] == args.group_name:
            mylogs.info("Targeting systems in group: %s with %s systems." %(a['name'],  str(a['system_count'])))
            """ print("Targeting systems in group: %s with %s systems." %(a['name'],  str(a['system_count']))) """
            grpfound = True
            try:
                activesystemlist = session.systemgroup.listActiveSystemsInGroup(key, args.group_name)
            except:
                error1 = 1
                mylogs.info("uups something went wrong. We could not find the active systems in the given group name. Maybe the group is empty.")
            if len(activesystemlist) > 0:
                for a in activesystemlist:
                    pkg_upgradelist = []
                    upgrade_os(a, pkg_upgradelist, earliest_occurrence_upgradejob)
            break
    
    if not grpfound:
        mylogs.info("sorry we could not find the group you provided. Check if it exists or case-sensitive name correctness.")
        sys.exit(1)
    

json_write(jobsdict)
suma_logout(session, key)