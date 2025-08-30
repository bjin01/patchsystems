#!/usr/bin/python

import argparse,  getpass,  textwrap, time
import datetime
import yaml
import os
from cryptography.fernet import Fernet
import logging
import atexit
import six
from xmlrpc.client import ServerProxy, Error

log = logging.getLogger("clm_run")
log.propagate = False
formatter = logging.Formatter('%(asctime)s | %(module)s | %(levelname)s | %(message)s') 

if not any(isinstance(h, logging.StreamHandler) for h in log.handlers):
    streamhandler = logging.StreamHandler()
    streamhandler.setFormatter(formatter)
    log.addHandler(streamhandler)

_sessions = {}

def set_log_level(log_level):
    """Set the log level globally for the logger."""
    if log_level.upper() == "DEBUG":
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

def encrypt_password(pwd):
    key = Fernet.generate_key()
    print("Randomly generated key! Keep it safely!: \n{}".format(key.decode()))
    # Instance the Fernet class with the key
    fernet = Fernet(key)
    
    # then use the Fernet class instance
    # to encrypt the string string must
    # be encoded to byte string before encryption
    encrypted_pwd = fernet.encrypt(pwd.encode())
    print("\nSave this encrypted password in your configuration file.\n{} ".format(encrypted_pwd.decode()))

def _decrypt_password(password_encrypted, suma_key_file="/root/suma_key.yaml"):
    
    encrypted_pwd = ""
    if not os.path.exists(suma_key_file):
        log.error("No suma_key.yaml found")
        if os.environ.get('SUMAKEY') == None: 
            log.fatal("You also don't have ENV SUMAKEY set. Use unencrypted pwd.")
            return str(password_encrypted)
        else:
            
            encrypted_pwd = os.environ.get('SUMAKEY')
    else:
        
        with open(suma_key_file, 'r') as file:
            sumakey_dict = yaml.safe_load(file)
            encrypted_pwd = sumakey_dict["SUMAKEY"]

    if not encrypted_pwd == "":
        saltkey = bytes(str(encrypted_pwd), encoding='utf-8')
        fernet = Fernet(saltkey)
        encmessage = bytes(str(password_encrypted), encoding='utf-8')
        pwd = fernet.decrypt(encmessage)
    else:
        log.fatal("encrypted_pwd is empty. Use unencrypted pwd.")
        return str(password_encrypted)        
    
    return pwd.decode()

def _get_suma_configuration(suma_config_file="suma_config.yaml"):
    '''
    Return the configuration read from the configuration
    file or directory
    '''

    try:
        with open(suma_config_file, 'r') as file:
            suma_config = yaml.safe_load(file)
            if not suma_config:
                suma_config = {}
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file '{suma_config_file}' not found.")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file '{suma_config_file}': {e}")

    if suma_config:
        try:
            suma_server = suma_config.get('suma_server', "localhost")
            username = suma_config.get('suma_api_username', None)
            password_encrypted = suma_config.get('suma_api_password', None)
            password = _decrypt_password(password_encrypted, suma_config.get('suma_key_file', "/root/suma_key.yaml"))
            protocol = suma_config.get('protocol', 'https')
            


            if not username or not password:
                log.error(
                    'Username or Password has not been specified in the master '
                    'configuration for %s', suma_server
                )
                return False

            ret = {
                'api_url': '{0}://{1}/rpc/api'.format(protocol, suma_server),
                'username': username,
                'password': password,
                'servername': suma_server
            }
            return ret
        except Exception as exc:  # pylint: disable=broad-except
            log.error('Exception encountered: %s', exc)
            return False

    return False


def _get_client_and_key(url, user, password, verbose=0):
    '''
    Return the client object and session key for the client
    '''
    session = {}
    session['client'] = six.moves.xmlrpc_client.Server(url, verbose=verbose, use_datetime=True)

    session['key'] = session['client'].auth.login(user, password)
    return session


def _disconnect_session(session):
    '''
    Disconnect API connection
    '''
    session['client'].auth.logout(session['key'])


def _get_session(suma_config):
    '''
    Get session and key
    '''
    server = suma_config["servername"]
    if server in _sessions:
        return _sessions[server]

    session = _get_client_and_key(suma_config['api_url'], suma_config['username'], suma_config['password'])
    atexit.register(_disconnect_session, session)

    client = session['client']
    key = session['key']
    _sessions[server] = (client, key)

    return client, key

parser = argparse.ArgumentParser()
parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
This scripts helps to manage content lifecycle management projects. 
Sample command:
              python clm_run.py --listProject
              python clm_run.py --listEnvironment --projLabel myprojlabel
              python clm_run.py --build --projLabel myprojlabel \n \
              python clm_run.py --promote --projLabel myprojlabel --envLabel teststage  \n \
              python clm_run.py --check_status --projLabel myprojlabel --envLabel teststage  \n \
The script can build project, update and promote stages or environments.
Check taskomatic logs in order to monitor the status of the build and promote tasks e.g. # tail -f /var/log/rhn/rhn_taskomatic_daemon.log. '''))

parser.add_argument("--encrypt_pwd", default="", help="provide password to encrypt it")
parser.add_argument("--config", default="/root/suma_config.yaml", help="Path to config file")
parser.add_argument("--listProject", action="store_true")
parser.add_argument("--listEnvironment", action="store_true")
parser.add_argument("--check_status", action="store_true")
parser.add_argument("--build", action="store_true")
parser.add_argument("--promote", action="store_true")
parser.add_argument("--projname", help="Enter the desired project name. e.g. myproject",  required=False)
parser.add_argument("--projLabel", help="Enter the project label. e.g. mytest",  required=False)
parser.add_argument("--envLabel", help="Enter the environment label. e.g. dev",  required=False)
args = parser.parse_args()


status_text = ['built', 'building',  'generating_repodata']
tasko_text = 'Check taskomatic logs in order to monitor the status of the build and promote tasks e.g. # tail -f /var/log/rhn/rhn_taskomatic_daemon.log.'

if args.encrypt_pwd:
    if args.encrypt_pwd.strip() != "":
        clear_pwd = args.encrypt_pwd.strip()
        encrypt_password(clear_pwd)
        exit(0)
    else:
        log.warning("You provided a empty password to encryption. Exit.")
        exit(1)

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

""" def printdict(dict_object):
    for i in dict_object:
        keys = i.keys()
        val = i.values()
        print("Item---------------------------------------------")
        for k in keys:
            print ("{:<20}".format(k)), 
        print("\n")
        for v in val:
            print ("{:<20}".format(v)), 
        print("\n")
        print("----------------------------------------------------")
    return """

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

def listproject(key):
    projlist = session.contentmanagement.listProjects(key)
    if projlist:
        printdict(projlist)
        return True
    else:
        print("no projects found")
        return False

def listEnvironment(key, projectLabel):
    envlist = session.contentmanagement.listProjectEnvironments(key, projectLabel)
    if envlist:
        printdict(envlist)
        return True
    else:
        print("no projectEnvironments found")
        return False

def isNotBlank(myString):
    if myString and myString.strip():
        #myString is not None AND myString is not empty or blank
        return True
    #myString is None OR myString is empty or blank
    return False

def check_env_status(key,  projLabel,  *args):
    lookup_projenv_return = session.contentmanagement.listProjectEnvironments(key, projLabel)
    ok = True
    mystatus = ["built", "unkown"]
    for a in lookup_projenv_return:
        for h, i in a.items():
            
            if h == "status":
                if not i.find(mystatus[0]) and not i.find(mystatus[1]):
                    print("%s: work progress: %s" %(a['name'], i))
                    ok = False
                    break
    
    if not ok:
        print("")
        print("environments in progress, a new build or promote not possible")
        exit(1)

    
    """ try:
        lookup_projenv_return = session.contentmanagement.listProjectEnvironments(key, projLabel)
        ok = True
        for a in lookup_projenv_return:
            for h, i in a.items():
                if h == "status":
                    if i != "built" or i != None or i != "":
                        print("project environment in working projegress: %s" %(i))
                        ok = False
        
        if not ok:
            print("")
            print("environments in progress, a new build or promote not possible")
            exit(1)
    except:
        print("project environment lookup failed. %s Exit." %projLabel)
        exit(1) """

    if not args:
        envLabel = ''
    else:
        for a in args:
            envLabel = a
    if not isNotBlank(envLabel):
        lookup_proj_return = session.contentmanagement.lookupProject(key, projLabel)
        for k,  v in lookup_proj_return.items():
            if k in 'firstEnvironment':
                envLabel = v
        try:
            lookupenv = session.contentmanagement.lookupEnvironment(key, projLabel,  envLabel)
            for k,  v in lookupenv.items():
                #print("lets see k %s, v is: %s" %(k, v))
                if k == "status":
                    for s in status_text:
                        #print(s)
                        if s in v:
                            print("%s: %s is %s" %(projLabel, envLabel, s))
                            break
        except Exception as ex:
            print("not found %s" %ex)
            print("check_env_status failed. Exit with error")
            exit(1)
    else:
        try:
            lookupenv = session.contentmanagement.lookupEnvironment(key, projLabel,  envLabel)
            print("%s: %s is %s" %(projLabel, envLabel, lookupenv['status']))
        except Exception as ex:
            print("not found %s" %ex)
            print("check_env_status failed. Exit with error")
            exit(1)
    return

def lookupProject(key, projLabel):
    try:
        session.contentmanagement.lookupProject(key, projLabel)
        return True
    except:
        print("Project label does not exist: %s" %projLabel)
        return False
    


def buildproject(key,  projLabel):
    result_lookup_project = lookupProject(key, projLabel)
    buildresult = 0
    if result_lookup_project:
        check_env_status(key, projLabel)
        current_time = time.localtime()
        myversion = time.strftime('%Y-%m-%d', current_time)
        buildresult = session.contentmanagement.buildProject(key, projLabel, myversion)

    if buildresult == 1:
            print("Build %s task: Successful"  %(projLabel))
            print("sleep 5 seconds")
            time.sleep(5)
            check_env_status(key, projLabel)
            print(tasko_text)
    else:
            print("Build failed. Exit with error.")
            exit(1)    
    return buildresult

def promoteenvironment(key,  projLabel,  envLabel):
    result_lookup_project = lookupProject(key, projLabel)
    if result_lookup_project:
        try:
            nextenvironment = session.contentmanagement.listProjectEnvironments(key, projLabel)
        except Exception as ex:
            print("not found %s" %ex)
            print("lookup project and environment label failed. exit.")
            exit(1)
    
        for i in nextenvironment:
            if i['label'] == envLabel:
                nextLabel = i['nextEnvironmentLabel']
                check_env_status(key,  projLabel, nextLabel)
                break
   
    try:
        promote_result = session.contentmanagement.promoteProject(key, projLabel,  envLabel)
        if promote_result == 1:
            print("promote %s %s task: Successful."  %(projLabel, envLabel))
            print("sleep 5 seconds")
            time.sleep(5)
            check_env_status(key, projLabel, nextLabel)
            print(tasko_text)
        else:
            print("promote failed. Exit with error.")
            exit(1)
    except Exception as ex:
        print("not found %s" %ex)
        return False
    return promote_result


suma_config = _get_suma_configuration(args.config)
server = suma_config["servername"]

try:
    session, key = _get_session(suma_config)
except Exception as exc:  # pylint: disable=broad-except
    err_msg = 'Exception raised when connecting to spacewalk server ({0}): {1}'.format(server, exc)
    log.error(err_msg)

if args.listProject:
    try:
        ret = listproject(key)
    except Exception as ex:
        print("not found %s" %ex)
        print('something went wrong with listproject')
elif args.check_status and args.projLabel: 
    if args.envLabel:
        check_env_status(key, args.projLabel, args.envLabel)
    elif not args.envLabel:
        check_env_status(key,  args.projLabel)
elif args.listEnvironment and args.projLabel:
    try:
        ret = listEnvironment(key, args.projLabel)
    except Exception as ex:
        print(ex)
        print("something went wrong with listEnvironment.")
elif args.build and args.projLabel:
    try:
        ret = buildproject(key, args.projLabel)
    except Exception as ex:
        print(ex)
        print("something went wrong with buildproject.")
elif args.promote and args.projLabel and args.envLabel:
     try:
        ret = promoteenvironment(key, args.projLabel,  args.envLabel)
     except Exception as ex:
        print("not found %s" %ex)
        print("something went wrong with promote environment.")
else:
    print("Please verify you entered correct parameters. Exiting.")

    
suma_logout(session, key)