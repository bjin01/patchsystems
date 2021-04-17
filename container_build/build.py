#!/usr/bin/env python3
import yaml
import os
import sys
from xmlrpc.client import ServerProxy
from xmlrpc.client import DateTime
from datetime import datetime
import ssl
import argparse
import textwrap

def get_login(path=None):
    if path:
        path = path
    else:
        path = os.path.join(os.environ["HOME"], "suma_config.yaml")
    with open(path) as f:
        login = yaml.load_all(f, Loader=yaml.FullLoader)
        for a in login:
            login = a
    return login

def schduled_build_image(profile, build_host, build_version):
    getsystemid = client.system.getId(key, build_host)
    print("systemid: %s" % str(getsystemid))
    if getsystemid:
        print("Schedule image build...")
        ret_build = client.image.scheduleImageBuild(key, profile, build_version, getsystemid[0]['id'], earlierst_occurence)
        if ret_build:
            print("Image Build Job ID: %s" % str(ret_build))
    return

parser = argparse.ArgumentParser()
parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
This scripts helps to manage container image build. 
Sample command:
               python3 build.py -h

              python3 build.py -c ~/suma_config.yaml

              python3 container_build/build.py -p sles15sp2_profile -b pxenode01.bo2go.home -s 21
              
Check taskomatic logs in order to monitor the status of the build and promote tasks e.g. # tail -f /var/log/rhn/rhn_taskomatic_daemon.log. '''))
parser.add_argument("--config", "-c", help="enter config file path that provides suma host user and password")
parser.add_argument("--profile", "-p", help="enter profile name")
parser.add_argument("--build_host", "-b", help="enter build host name")
parser.add_argument("--build_version", "-s", help="enter build image version")

args = parser.parse_args()

now = datetime.today()
#print(now)
earlierst_occurence = DateTime(now)
#print(earlierst_occourence)

if args.config:
    if os.path.exists(args.config):
        path = args.config
        login = get_login(path)
    else:
        print("The config file does not exist. %s" % args.config)
        sys.exit(1)
else:
    login = get_login()

MANAGER_URL = "https://" + login['suma_host'] + "/rpc/api"
MANAGER_LOGIN = login['suma_user']
MANAGER_PASSWORD = login['suma_password']

# You might need to set to set other options depending on your
# server SSL configuartion and your local SSL configuration
context = ssl.create_default_context()
client = ServerProxy(MANAGER_URL, context=context)
key = client.auth.login(MANAGER_LOGIN, MANAGER_PASSWORD)

if args.profile and args.build_host and args.build_version:
    schduled_build_image(args.profile, args.build_host, args.build_version)
else:
    images = client.image.listImages(key)
    for h in images:
        print("Image: %s, version: %s" % (h['name'], h['version']))

    imageprofiles = client.image.profile.listImageProfiles(key)
    for i in imageprofiles:
        print("Profile label: %s" % i['label'])

    activesystems = client.system.listActiveSystems(key)
    for a in activesystems:
        systemdetails = client.system.getDetails(key, a['id'])
        for x in systemdetails['addon_entitlements']:
            #print(x)
            if x == "container_build_host":
                print("%s %s: %s" %(x, a['name'], a['id']))
client.auth.logout(key)