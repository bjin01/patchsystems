#!/usr/bin/python

import xmlrpclib,  argparse,  getpass,  textwrap,  json
import sys, os, yaml, shlex, subprocess, time
from datetime import datetime,  timedelta
from collections import defaultdict

#below code is parsing raw repo modules md into a dict
def parse_metadata(myfile):
    modules_dict = {}
    if os.path.exists(myfile):
        count = 0
        with open(myfile, 'r') as fp: 
            Lines = fp.readlines() 
            for l in Lines:
                if "name: " in l:
                    rpartition_result = l.strip().rpartition(":")
                    namekey = rpartition_result[2]
                    count = 1
                if "stream: " in l:
                    rpartition_result = l.strip().rpartition(":")
                    streamval = rpartition_result[2]
                    #print("before strip %s" %streamval)
                    streamval = streamval.strip()
                    #print("after strip %s" %streamval)
                    count = 2
                if "--" in l:
                    count = 0
                    namekey =""
                    streamval = ""

                if count == 2:
                    already_exist = False
                    #need to do below verification as the metadata could have dupblicate \
                    # entries for module and streams
                    namekey_extended = ""
                    for a, v in modules_dict.items():
                        if namekey in a and streamval in v:
                            already_exist = True
                            break
                        else:
                            if namekey in a and streamval not in v:
                                #print("special", namekey, streamval)
                                namekey_extended = namekey + "@" + streamval
                                already_exist = False
                                break

                    if not already_exist:
                        if namekey_extended:
                            modules_dict[namekey_extended] = streamval
                        else:
                            modules_dict[namekey] = streamval
                    

    if len(modules_dict.keys()) != 0:
        for a, b in modules_dict.items():
            print(a, b)
        return modules_dict
    else:
        sys.exit(1)

#below code checks if the filter is already created and return false or true
def lookup_filter(session_key, value, delete_flag):
    try:
        filters = session_client.contentmanagement.listFilters(session_key)
        #print(filters)
    except:
        print("listfilters went wrong.")
    found = False
    for a in filters:
        #print("inside lookup_filter", a)
        if delete_flag == 1 and a['name'] in value:
            try:
                print("Deleting filter: %s" %a['name'])
                filters = session_client.contentmanagement.removeFilter(session_key, a['id'])
            except:
                print("delete filter went wrong. ID: %s" %a['id'])
        #print(value, a['criteria']['value'])
        """ if a['criteria']['value'] in value:
            if delete_flag == 0:
                print("Existing filter found. %s" %filtername)
                found = True
                return found
            if delete_flag == 1:
                try:
                    print("Deleting filter: %s" %a['name'])
                    filters = session_client.contentmanagement.removeFilter(session_key, a['id'])
                except:
                    print("delete filter went wrong. ID: %s" %a['id'])
                found = True
                return found        
        else:
            found = False """
            
    return found

#below code tries to find the given project name if it already exist
def lookup_clmproject(session_key, projectlabel):
    try:
        ret_lookupproject = session_client.contentmanagement.lookupProject(session_key, \
                            projectlabel)
        return True
    except:
        return False

#attache filters to the given project
def attache_filters(session_key, project_label, filter_id_list):
    temp_attache_filterslist = []
    for a in filter_id_list:
        try:
            ret_attache_filters = session_client.contentmanagement.attachFilter(session_key, \
                                    project_label, a)
        except:
            print("attaching filter failed.")
        if ret_attache_filters:
            temp_attache_filterslist.append(ret_attache_filters['name'])
    
    if len(temp_attache_filterslist) != 0:
        #print("Follwing filters have been attached to project: %s:" %project_label)
        for i in temp_attache_filterslist:
            x = 0
            #print(i)
        return True
    else:
        return False

#below is to find the child channels of the given parent_channel_label and return a list
def find_child_channels(session_key, parent_channel_label):
    try:
        print("try to find child channels...")
        ret_channels_list = session_client.channel.listSoftwareChannels(session_key)
    except:
        print("find listSoftwareChannels failed.")
        sys.exit(1)

    ret_channels = []
    ret_channels.append(parent_channel_label)
    if ret_channels_list:
        for i in ret_channels_list:
            #print(i)
            if i['parent_label'] == parent_channel_label:
                ret_channels.append(i['label'])

    return ret_channels

#attache parent and child channels into the project
def attache_project_source(session_key, project_label, sourceType, parent_channel_label):
    try:
        print(project_label, sourceType, parent_channel_label)
        ret_attache_source = session_client.contentmanagement.attachSource(session_key, \
                                project_label, sourceType, parent_channel_label)
        return True
    except:
        print("attaching source channel failed.")
        return False

#attache newly created filters into the given project 
def create_project_attache_filters(session_key, label, name, description, filter_id_list):
    try:
        ret_createproject = session_client.contentmanagement.createProject(session_key, \
                                                                label, name, description)
        print("project created, ID: %s, name: %s" %(ret_createproject['id'], \
                                                    ret_createproject['label']))
    except:
        print("Creating clm project failed.")
        sys.exit(1)

    if len(filter_id_list) != 0:
        sourceType = "software"
        if args.parent_channel_label:
            ret_channels = find_child_channels(session_key, args.parent_channel_label)
            if ret_channels:
                print(ret_channels)
                for a in ret_channels:
                    attache_project_source(session_key, ret_createproject['label'], sourceType, a)
                attache_filters(session_key, ret_createproject['label'], filter_id_list)
        else:
            print("no parent_channel_label provided.")

#below code is for script parameters
class Password(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        if values is None:
            values = getpass.getpass()
        setattr(namespace, self.dest, values)

parser = argparse.ArgumentParser()
listclm_parser = argparse.ArgumentParser()
listfilters_parser = argparse.ArgumentParser()
deletefilters_parser = argparse.ArgumentParser()

#parser.add_argument("-v", "--verbosity", action="count", default=0)
parser = argparse.ArgumentParser(prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter, \
    description=textwrap.dedent('''\
This scripts schedules patch deployment jobs for given group's systems' in given hours from now on. \
    A reboot will be scheduled as well. 
Sample command:
    below creates filters parsed from given yaml file, create project and attach centos8 parent \
        and child channels.
        python clm-channel.py -s bjsuma.bo2go.home -u bjin -p suse1234 -f centos8-modulesmd.yaml \
                                -cname testproject -sl centos8-x86_64 \n 

    below cli deletes the given project label
        python clm-channel.py -s bjsuma.bo2go.home -u bjin -p suse1234 -dp xxxx \n
    
    below cli delete all filters that are found from the given module metadata file
        python clm-channel.py -s bjsuma.bo2go.home -u bjin -p suse1234 -f centos8-modulesmd.yaml -df \n \
    
''')) 
parser.add_argument("-s", "--server", help="Enter your suse manager host address e.g. myserver.abd.domain",  \
                        default='localhost',  required=True)
parser.add_argument("-u", "--username", help="Enter your suse manager loginid e.g. admin ", default='admin',  \
                        required=True)
parser.add_argument('-p', action=Password, nargs='?', dest='password', help='Enter your password', \
                        required=True)
parser.add_argument('-d', "--delete", help='delete clm project with given clm label',  required=False)
parser.add_argument('-f', "--importfile", help='import appstream module metadata file in yaml',  \
                        required=False)
parser.add_argument('-cname', "--clmname", help='enter you a clm project name as label and name',  \
                        required=False)
parser.add_argument('-sl', "--parent_channel_label", help='enter parent channel label which \
                        should attached to clm project', \
                        required=False)
parser.add_argument('-ps', "--show_project_sources", help='enter clm project label',  required=False)
parser.add_argument('-dp', "--delete_project", help='delete project by enter clm project label',  required=False)
parser.add_argument('-ic', "--import_custom_file", help='specify custom file that \
                        contains modules and streams in yaml', \
                        required=False)

listclm_parser = parser.add_mutually_exclusive_group(required=False)
listclm_parser.add_argument("-l", '--list', help="list clm projects", dest='listclm', action='store_true')
parser.set_defaults(listclm=False)

listfilters_parser = parser.add_mutually_exclusive_group(required=False)
listfilters_parser.add_argument("-lf", '--listfilters', help="list clm filters", dest='listfilters', action='store_true')
parser.set_defaults(listfilters=False)

deletefilters_parser = parser.add_mutually_exclusive_group(required=False)
deletefilters_parser.add_argument("-df", '--deletefilters', help="delete clm filters", dest='deletefilters', action='store_true')
parser.set_defaults(deletefilters=False)
args = parser.parse_args()

MANAGER_URL = "http://"+ args.server+"/rpc/api"
MANAGER_LOGIN = args.username
MANAGER_PASSWORD = args.password

session_client = xmlrpclib.Server(MANAGER_URL, verbose=0)
session_key = session_client.auth.login(MANAGER_LOGIN, MANAGER_PASSWORD)

#list attached channels into a project
if args.show_project_sources:
    try:
        ret_project_sources = session_client.contentmanagement.listProjectSources(session_key, \
                                args.show_project_sources)
    except:
        print("project source lookup failed. %s" %args.show_project_sources)
    if ret_project_sources:
        print(ret_project_sources)

#list existing projects
if args.listclm:
    projects = session_client.contentmanagement.listProjects(session_key)
    for a in projects:
        print("project label: %s" %(a['label']))

#list existing filters
if args.listfilters:
    print("listing filters:")
    filters = session_client.contentmanagement.listFilters(session_key)
    for a in filters:
        for i,h in a.items():
            print(i, h)
        print("---------------------------\n")

#delete given project
if args.delete_project:
    try:
        ret_searchproject = session_client.contentmanagement.lookupProject(session_key, \
                            args.delete_project)    
    except:
        print("lookup for %s to be deleted failed. It does not exist. Exit." %args.delete_project)
        sys.exit(1)

    if ret_searchproject:
        try:
            ret_delete_project = session_client.contentmanagement.removeProject(session_key, \
                                    args.delete_project)
        except:
            print("deleting project %s failed. Exit" %args.delete_project)
            sys.exit(1)
        if ret_delete_project == 1:
            print("clm project %s successful deleted." %args.delete_project)
            sys.exit(0)

#----------------------------------------------------------------------------------------
#below is to allow user using their custom file which contains manually modified modules
if args.import_custom_file:
    print("import custom file: %s" %args.import_custom_file)
    modules_dict = parse_metadata(args.import_custom_file)
    filter_id_list = []

    if len(modules_dict.keys()) != 0:
        print("module metadata found")
        for a, b in modules_dict.items():
            if "@" in a:
                a_new = a.split("@")
                print("look for a_new %s" %a_new[0])
                filtername = "module-" + a_new[0].strip() + "-" + b.strip()
                entitytype = "module"
                rule = "allow"
                value = a_new[0].strip() + ":" + b
                criteria = {'field': 'module_stream', 'value': value, 'matcher': 'equals'}
            else:
                filtername = "module-" + a.strip() + "-" + b.strip()
                entitytype = "module"
                rule = "allow"
                value = a + ":" + b
                criteria = {'field': 'module_stream', 'value': value, 'matcher': 'equals'}
            
            if args.deletefilters:
                found = lookup_filter(session_key, filtername, 1)
            else:
                found = lookup_filter(session_key, filtername, 0)
            if not found and not args.deletefilters:
                try:
                    ret_createfilter = session_client.contentmanagement.createFilter(session_key, \
                                        filtername, rule, entitytype, criteria)
                    if ret_createfilter:
                        filter_id_list.append(ret_createfilter['id'])
                except:
                    print("createFilter failed, because it might be already created.")
            
            if not found and args.deletefilters:
                print("attention: no filters to delete.")
    
    if args.clmname and not args.deletefilters:
        timestemp = datetime.now()
        description = "created by script at " + str(timestemp)
        project_found = lookup_clmproject(session_key, args.clmname)
        if not project_found and not args.deletefilters:
            create_project_attache_filters(session_key, args.clmname, args.clmname, \
                                            description, filter_id_list)
    
    if not args.clmname and not args.deletefilters:
        timestemp = datetime.now()
        description = "created by script at " + str(timestemp)
        projectlabel = "streams"
        projectname = "streams"
        project_found = lookup_clmproject(session_key, projectlabel)
        if not project_found and not args.deletefilters:
            create_project_attache_filters(session_key, projectlabel, projectname, \
                                            description, filter_id_list)

#grepout.txt is the default intermediate file to be used to write metadata into it.
grepfile = "grepout.txt"
if args.importfile:
    args_strings = "grep -A1 -E \'name: .*$\' " + args.importfile + " > " + grepfile
    print(args_strings)
    subprocess.check_output(args_strings, shell=True)
    modules_dict = parse_metadata(grepfile)
    filter_id_list = []

    if len(modules_dict.keys()) != 0:
        print("module metadata found.")
        for a, b in modules_dict.items():
            if "@" in a:
                a_new = a.split("@")
                print("look for a_new %s" %a_new[0])
                filtername = "module-" + a_new[0].strip() + "-" + b.strip()
                entitytype = "module"
                rule = "allow"
                value = a_new[0].strip() + ":" + b
                criteria = {'field': 'module_stream', 'value': value, 'matcher': 'equals'}
            else:
                filtername = "module-" + a.strip() + "-" + b.strip()
                entitytype = "module"
                rule = "allow"
                value = a + ":" + b
                criteria = {'field': 'module_stream', 'value': value, 'matcher': 'equals'}
            
            if args.deletefilters:
                found = lookup_filter(session_key, filtername, 1)
            else:
                found = lookup_filter(session_key, filtername, 0)

            if not found and not args.deletefilters:
                try:
                    ret_createfilter = session_client.contentmanagement.createFilter(session_key, \
                        filtername, rule, entitytype, criteria)
                    if ret_createfilter:
                        filter_id_list.append(ret_createfilter['id'])

                except:
                    print("createFilter failed, because it might be already created.")
            
            if not found and args.deletefilters:
                print("attention: no filters to delete.")

    if args.importfile and args.clmname and not args.deletefilters:
        timestemp = datetime.now()
        description = "created by script at " + str(timestemp)
        project_found = lookup_clmproject(session_key, args.clmname)
        if not project_found and not args.deletefilters:
            try:
                ret_createproject = session_client.contentmanagement.createProject(session_key, \
                                        args.clmname, args.clmname, description)
                print("project created, ID: %s, name: %s" %(ret_createproject['id'], \
                        ret_createproject['label']))
            except:
                print("Creating clm project failed.")
            
            print("lets see the filter_id_list %s" %filter_id_list)
            if len(filter_id_list) != 0:
                sourceType = "software"
                if args.parent_channel_label:
                    ret_channels = find_child_channels(session_key, args.parent_channel_label)
                    if ret_channels:
                        print(ret_channels)
                        for a in ret_channels:
                            attache_project_source(session_key, ret_createproject['label'], sourceType, a)
                        attache_filters(session_key, ret_createproject['label'], filter_id_list)
                else:
                    print("no parent_channel_label provided.")
        else:
            print("project %s exist already." %args.clmname)
    else:
        if args.importfile and not args.clmname and not args.deletefilters:
            timestemp = datetime.now()
            description = "created by script at " + str(timestemp)
            projectlabel = "streams"
            projectname = "streams"
            project_found = lookup_clmproject(session_key, projectlabel)
            if not project_found and not args.deletefilters:
                try:
                    ret_createproject = session_client.contentmanagement.createProject(session_key, \
                                        projectlabel, projectname, description)
                    print("default project name created, ID: %s, name: %s" %(ret_createproject['id'], projectlabel))
                except:
                    print("2 Creating clm project failed.")
                if len(filter_id_list) != 0:
                    sourceType = "software"
                    if args.parent_channel_label:
                        ret_channels = find_child_channels(session_key, args.parent_channel_label)
                        if ret_channels:
                            print(ret_channels)
                            for a in ret_channels:
                                attache_project_source(session_key, projectlabel, sourceType, a)
                            attache_filters(session_key, projectlabel, filter_id_list)
                    else:
                        print("no parent_channel_label provided.")
            else:
                print("project %s exist already." %projectlabel)


