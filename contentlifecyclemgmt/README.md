# SUSE Manager - Content Lifecycle Management - create filters and projects

```clm-channel.py``` 

This helper script that can be used to:
* parse centos8 and rhel8 appstream modules metadata.
* import those found modules and streams into SUSE Manager as module filters.
* create a content lifecycle management project with given label.
* attache given parent channel label with child channels.
* attache the newly imported filters to the project.
* delete clm project by provide the project label.
* delete clm filters by provide the given raw metadata file in yaml.

### Get centos 8 appstream repo metadata file:
* Download the modules metadata file from any centos8 mirrors.
e.g. ```http://mirror.inode.at/data/centos/8.2.2004/AppStream/x86_64/os/repodata/```

find a file like below, download it, extract it on your local system.
```
    29ca407bc5a6166ebf443c05da1dc642267b193fb5859f4b6a4c68550d1d40c0-modules.yaml.gz
```
You will use this *-modules.yaml file as raw metadata file with the script as below.

### Sample usage:

below creates filters parsed from given yaml file, create project and \
attach centos8 parent and child channels.
```
    python clm-channel.py -s bjsuma.bo2go.home -u bjin -p suse1234 -f \
        centos8-modulesmd.yaml -cname testproject -sl centos8-x86_64
``` 

below cli deletes the given project label
``` 
    python clm-channel.py -s bjsuma.bo2go.home -u bjin -p suse1234 -dp xxxx
```
    
below cli delete all filters that are found from the given module metadata file
``` 
    python clm-channel.py -s bjsuma.bo2go.home -u bjin -p suse1234 \
        -f centos8-modulesmd.yaml -df
```

### Optional arguments:

```
optional arguments:
  -h, --help            show this help message and exit
  -s SERVER, --server SERVER
                        Enter your suse manager host address e.g.
                        myserver.abd.domain
  -u USERNAME, --username USERNAME
                        Enter your suse manager loginid e.g. admin
  -p [PASSWORD]         Enter your password
  -d DELETE, --delete DELETE
                        delete clm project with given clm label
  -f IMPORTFILE, --importfile IMPORTFILE
                        import appstream module metadata file in yaml
  -cname CLMNAME, --clmname CLMNAME
                        enter you a clm project name as label and name
  -sl PARENT_CHANNEL_LABEL, --parent_channel_label PARENT_CHANNEL_LABEL
                        enter parent channel label which should attached to
                        clm project
  -ps SHOW_PROJECT_SOURCES, --show_project_sources SHOW_PROJECT_SOURCES
                        enter clm project label
  -dp DELETE_PROJECT, --delete_project DELETE_PROJECT
                        delete project by enter clm project label
  -ic IMPORT_CUSTOM_FILE, --import_custom_file IMPORT_CUSTOM_FILE
                        specify custom file that contains modules and streams
                        in yaml
  -l, --list            list clm projects
  -lf, --listfilters    list clm filters
  -df, --deletefilters  delete clm filters
  ```
