#!/usr/bin/python
import xmlrpclib
import sys
import yaml

def get_peripheral_suma_name(serverid, yamlconf_data):
    hub_suma_url = "http://localhost/rpc/api"
    hub_suma_session_client = xmlrpclib.Server(hub_suma_url, verbose=0)
    hub_suma_session_key = hub_suma_session_client.auth.login(yamlconf_data["hub_user"], yamlconf_data["hub_password"])

    try:
        result_getname = hub_suma_session_client.system.getName(hub_suma_session_key, serverid)
        hub_suma_session_client.auth.logout(hub_suma_session_key)
        return result_getname
    except:
        print("uuups, requested ID %s peripheral suma name not found. Something went wrong. Exit with error." %serverid)
        sys.exit(1)
    hub_suma_session_client.auth.logout(hub_suma_session_key)

def list_peripheral_suma_managed_systems(systemsPerServer):
    successfulResponses = systemsPerServer["Successful"]["Responses"]
    failedResponses = systemsPerServer["Failed"]["Responses"]

    for system in successfulResponses:
        if isinstance(system, list):
            print("system list:")
            count = 0
            for i in system:
                count += 1
                print("\t%s: %s" %(count, i['name'])) 
        else: 
            print("\tsystem name: %s" %system['name'])
    
    if failedResponses:
        print("Also watch out for failedResponses! %s" %failedResponses)

def read_yamlfile(yaml_file):
    with open(yaml_file, "r") as yamlfile:
        yamldata = yaml.load(yamlfile, Loader=yaml.FullLoader)
    return yamldata

def peripheral_suma_listsyStems(client, hubSessionKey, serverIDs, peripheral_usernames, peripheral_passwords):
    client.hub.attachToServers(hubSessionKey, serverIDs, peripheral_usernames, peripheral_passwords)

    # Execute call
    systemsPerServer = client.multicast.system.listSystems(hubSessionKey, serverIDs)

    return systemsPerServer

def printresults(systemsPerServer, yamlconf_data):
    if systemsPerServer["Successful"]["ServerIds"]:
        suma_peripheral_list = systemsPerServer["Successful"]["ServerIds"]
        #print("List of SUMA peripheral servers: %s" %suma_peripheral_list)
        if isinstance(suma_peripheral_list, list):
            for a in suma_peripheral_list:
                result = get_peripheral_suma_name(a, yamlconf_data)
                if result:
                    print("Peripheral SUMA Hostname: %s %s:" %(result["name"], result["id"]))
                    list_peripheral_suma_managed_systems(systemsPerServer)
        return True
    else:
        if systemsPerServer["Failed"]["Responses"]:
            print("Get data from %s, but failed: %s" %(systemsPerServer["Failed"]["ServerIds"], systemsPerServer["Failed"]["Responses"]))
            print("It might be possible that the given peripheral SUMA host is not available.\n")
        return False

# the main program part starts here
HUB_URL = ""
HUB_LOGIN = ""
HUB_PASSWORD = ""

yamlconf_data = read_yamlfile("suma_servers.yaml")

if yamlconf_data:
    HUB_URL = "http://"+ yamlconf_data["hub"] +":2830/hub/rpc/api"
    HUB_LOGIN = yamlconf_data["hub_user"]
    HUB_PASSWORD = yamlconf_data["hub_password"]
else:
    print("There is no suma_login in yaml file configured. Exit with error. You should write a config file with login data for hub and peripheral suma servers.")
    sys.exit(1)

if HUB_URL != "":
    client = xmlrpclib.Server(HUB_URL, verbose=0)
else:
    print("no Url to HUB server provided.")
    sys.exit(1)

# Login (uncomment only one line)
if HUB_LOGIN != "" and HUB_PASSWORD != "":
    hubSessionKey = client.hub.login(HUB_LOGIN, HUB_PASSWORD)
else:
    print("no Login data provide..")
    sys.exit(1)

# get list of Server IDs registered to the Hub
if hubSessionKey:
    serverIDs = client.hub.listServerIds(hubSessionKey)
else:
    print("No Session key generated. Maybe login failed.")
    sys.exit(1)

if len(yamlconf_data["peripheral_sumas"]) != 0:
    
    for s in yamlconf_data["peripheral_sumas"]:
        peripheral_usernames = []
        peripheral_passwords = []
        peripheral_suma_hosts = []
        
        if yamlconf_data["peripheral_sumas"][s]["active"]:
            peripheral_usernames.append(yamlconf_data["peripheral_sumas"][s]["username"])
            peripheral_passwords.append(yamlconf_data["peripheral_sumas"][s]["password"])
            peripheral_suma_hosts.append(yamlconf_data["peripheral_sumas"][s]["servername"])

        if len(peripheral_usernames) != 0 and len(peripheral_passwords) != 0:
            client.hub.attachToServers(hubSessionKey, serverIDs, peripheral_usernames, peripheral_passwords)
            systemsPerServer = client.multicast.system.listSystems(hubSessionKey, serverIDs)

            printresults(systemsPerServer, yamlconf_data)
        else:
            print("SUMA Host %s is set active: False. Skipping\n" %yamlconf_data["peripheral_sumas"][s]["servername"])

#logout
client.hub.logout(hubSessionKey)