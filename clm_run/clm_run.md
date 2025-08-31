## Updates:
August 2025

What's new:
* Argument validation: The script now checks for necessary arguments when certain flags are used, providing clear error messages if requirements are not met.
* password encryption - new argument --encrypt_pwd to encrypt password for use in config file.
* minor code cleanup and comments added.
* systemd service files updated with comments for clarity.
* tested with python3.6 and python3.11 on SMLM 5.0 and 5.1 on SLE-Micro 5.5/6.1

# Content Lifecycle Management Automation with SUSE Manager
clm_run.py is a python3.6/python3.11 script which calls SUSE Manager API to build and promote content lifecycle management project channels.

The script should be placed **inside SMLM Container** in /root/scripts/ or any other directory of your choice.

__Config API credentials:__
The configuration data is stored in file <HOME>/suma_config.yaml e.g. /root/suma_config.yaml
```
suma_server: <SUMA-HOST-NAME>
suma_api_username: <SUMA-USER>
suma_api_password: <ENCRYPTED_PASSWORD>
protocol: https
```
**suma_key.yaml** is used to encrypt the password for use in the config file.

Put the KEY that was generated with the command below into the file **/root/suma_key.yaml**
```
python3.6 clm_run.py --encrypt_pwd MySecretPassword
```
Sample key file:
```
suma_key: 6okILLV8u8AvsmXy3k0h9w==
```

Usage:
```
Sample commands:
            python clm_run.py --encrypt_pwd MySecretPassword
            python clm_run.py --config /path/to/suma_config.yaml --listProjects  
            python clm_run.py --config /path/to/suma_config.yaml --listEnvironment --projLabel myprojlabel
            python clm_run.py --config /path/to/suma_config.yaml --build --projLabel myprojlabel
            python clm_run.py --config /path/to/suma_config.yaml --promote --projLabel myprojlabel --envLabel teststage
            python clm_run.py --config /path/to/suma_config.yaml --check_status --projLabel myprojlabel --envLabel teststage
 The script can build project, update and promote stages or environments.
Check taskomatic logs in order to monitor the status of the build and promote tasks e.g. # tail -f /var/log/rhn/rhn_taskomatic_daemon.log.
```

place the systemd timer and service files under ```/etc/systemd/system/```

Adapt the parameters in [clm_run_failed\@.service](clm_run_failed@.service) - this service file will be triggered if the build and promote service has failed and send email notifications via smtp.
You can omit email notifications and by commentting out this line.
run following systmctl commands to enable the desired services:
The instance name of the service is the project label of the clm project.

If the environments are called differently, e.g. stage1, stage2 etc. you need to adapt the --envLabel parameter in and rename the service file to clm_run_stage1\@.service and clm_run_stage2\@.service respectively.
```
systemctl enable clm_run_test@sles15sp5.timer
systemctl enable clm_run_prod@sles15sp5.timer
systemctl daemon-reload
```

To verify if timer is activated:
```
systemctl list-timers
```
