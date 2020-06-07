# SUSE Manager - patch systems (SLES) automation
# xmlrpc api python script: patch all systems of a group

The idea is to provide a python script using spacewalk api to patch all systems within a given group and within an maintanance window of around three hours with system reboots.

The python script will be triggered through crontab on suse manager host at a given point in time.

__Commandline sample:__
`python patchsystemsByGroupWithRebootV2.py -s bjsuma.bo2go.home -u bjin -p suse1234 -g "testgroup" -o 2 -r`

The patchsystemsByGroupWithRebootV2.py will check followings:
1. Is the given group available?
2. Are the systems within group active? Inactive systems will be left out from further processing.
3. Create patch apply jobs for the affected systems of the systemgroup.
4. -o ("--in_hours") parameter is giving the number of hours from now on the jobs should be scheduled for.  
5. __system reboot: with -r parameter all active systems will also get a reboot job scheduled. This parameter is optional. The reboot happens one hour after the start time of patch jobs. So if your patch job is about to start in 2 hours the reboot job will be scheduled to start in 3 hours from the time when this script got executed.__
6. This script will also generate a joblist.json file into the current working directory and stores the action id of the jobs for later status queries.


__Recent Enhancements:__
1. cancelAllActions.py can be used to delete all action id which was created by the patchsystemsByGroupWithRebootV2.py script. 
`python cancelAllActions.py -s bjsuma.bo2go.home -u bjin -p suse1234 -f ./joblist.json`
2. jobstatus.py shows the job status of the recently created jobs into terminal and optionally into given output file.
`python jobstatus.py -s bjsuma.bo2go.home -u bjin -p suse1234 -f ./joblist.json -o /var/log/jobstatus_list.log`

3. a new feature has been added (June 2020)
-sr, --schedule_reboot: provide exact desired reboot time in format e.g. 15:30 20-04-1970. This param is optional but the desired schedule reboot time must not to be earlier than the desired patch install time otherwise script will exit with error.

4. if running script without -o and -sr but with -r for reboot - then it will create patch install jobs for now + a timeshifted reboot job of now + 10 minutes. This 10minutes allow reboot jobs occur after install jobs.
   

## future improvments:
1. add RHEL package install support
2. Intensive testing for reboot schedule is needed if you want to deploy patches to several hundreds systems.
3. Add salt grains to indicate staging environment

## monitoring job status
__jobstatus.py__ shows status from jobs which had been created by patchsystemsByGroupWithRebootV2.py.

```python jobstatus.py -s bjsuma.bo2go.home -u bjin -p suse1234 -f ./joblist.json -o /var/log/jobstatus_list.log```


1. the script accepts parameters of desired job log file location with -o option.
2. the script reads in the joblist.json file which was written by patchsystemsByGroupWithRebootV2.py with jobid information for each system.
3. the script will also monitors if affected systems need a system reboot once patch job completed. If reboot is needed the script will create reboot jobs for immediate run.
4. the script is running in loop and can be interrupted by pressing "ctrl+'c'" keyboard sequences.

### hint:
You might create a systemd unit file to run this jobstatus.py script as systemd service and monitor the log file with tail -f.
