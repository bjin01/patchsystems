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
