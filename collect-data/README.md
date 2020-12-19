# Collect SUSE Manager system information script

This python script is intended to collect information from SUSE Manager 
The script will count number of virtual or physical systems and put the data
into the given text file and send it by email to the given email address.

## usage:

```python collect_systems_report-v1.py -s bjsuma.bo2go.home -u bjin -p suse1234 -d -f /tmp/test.txt -m bo.jin@jinbo01.com```

```# python collect_systems_report-v1.py --help
usage: PROG [-h] -s SERVER -u USERNAME -p [PASSWORD] [-f FILEPATH]
            [-m TO_EMAIL] [-d]

This scripts collect all systems in SUSE Manager. 
Sample command:
              python collect_systems_report-v1.py -s bjsuma.bo2go.home -u bjin -p suse1234 

optional arguments:
  -h, --help            show this help message and exit
  -s SERVER, --server SERVER
                        Enter your suse manager host address e.g.
                        myserver.abd.domain
  -u USERNAME, --username USERNAME
                        Enter your suse manager loginid e.g. admin
  -p [PASSWORD]         Enter your password
  -f FILEPATH, --filename FILEPATH
                        Enter file path and name you want data to be written
                        into e.g. -f /home/user/results.txt
  -m TO_EMAIL, --to_email TO_EMAIL
                        Enter valid email address you want send to e.g. -m
                        foo.bar@email.domain.com
  -d, --details         print more details of the system information
  ```
  
  
