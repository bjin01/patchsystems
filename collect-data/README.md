# Collect SUSE Manager system information script

This python script is intended to collect information from SUSE Manager 
The script will count number of virtual or physical systems and put the data
into the given text file and send it by email to the given email address.

## features:
* sum all systems, virtual and physicals and by "installed products" which are Baseproduct
* can list system details which are relevant for the counting
* write results into a given file
* send the file content via email to desired recipient

## usage:

```python collect_systems_report-v1.py -s bjsuma.bo2go.home -u bjin -p suse1234 -d -f /tmp/test.txt -m test@test.domain.com```

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
  
  ## Sample overview result:
  ```
Monthly Audit of Linux servers - 19/12/2020, 13:08:00
Total: 17
Total VM: 17
Total bare-metal: 0
Total SLES: 8
Total SLES_for_SAP: 5
Total Expanded Support: 2
Total RHEL: 0
Total Centos: 1
```

## if -d for details used then the results are:
```

This are the system details from 2020-12-19 13:08:00.682588:
1000010217 asfasdf:
	VM: True
	baseproduct: SLES
	version: 15.1
	architecture: x86_64

1000010163 azure-sap-test.bo2go.home:
	VM: True
	baseproduct: SLES_SAP
	version: 15.1
	architecture: x86_64

....
```


