clm_run.py is a python3.6 script which calls SUSE Manager API to build and promote content lifecycle management project channels.

Config API credentials:
The data is stored in a file <HOME>/suma_config.yaml e.g. /root/suma_config.yaml
```
suma_host: <SUMA-HOST-NAME>
suma_user: <SUMA-USER>
suma_password: <PASSWORD>
notify_email: <Email-Recipients> comma separated
```

Usage:
```
Sample command:
              python clm_run.py --listProject
              python clm_run.py --listEnvironment --projLabel myprojlabel
              python clm_run.py --build --projLabel myprojlabel
              python clm_run.py --promote --projLabel myprojlabel --envLabel teststage
              python clm_run.py --check_status --projLabel myprojlabel --envLabel teststage
 The script can build project, update and promote stages or environments.
Check taskomatic logs in order to monitor the status of the build and promote tasks e.g. # tail -f /var/log/rhn/rhn_taskomatic_daemon.log.
```

place the systemd timer and service files under ```/etc/systemd/system/```

run following systmctl commands to enable the desired services:
```
systemctl enable clm_run_test@sles15sp5.timer
systemctl enable clm_run_prod@sles15sp5.timer
systemctl daemon-reload
```

To verify if timer is activated:
```
systemctl list-timers
```
