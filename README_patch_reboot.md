# Patch __active__ systems of a group and reboot them based on patch job completion

This solution has two scripts. One script is to schedule patch jobs for a given group. The second script is to schedule reboot of those systems based on patch job status.

p1.py - is triggering the patch job.
r1.py - is to evaluate patch job status if completed then a reboot job will be scheduled.

The reboot will be triggered for all systems who's patch job has completed independant if a reboot is required or not.
This approach is good for maintenance windows where systems need to be patched and rebooted.

Only active systems of a given group will be targeted otherwise we have to many pending jobs waiting for nodes which are maybe offline for longer period.

Usage:

First the scripts (r1.py and p1.py) should be placed in a directory of your choice.
The scripts will need a --config parameter to parse in the login information for calling SUSE Manager API. So create a config file in yaml format like below:
```
server: suma.domain.example
user: myuser
password: 8klwis9
```
Calling p1.py to patch:
Assuming all files are placed in same directory and you run below script from this directory.
-c is for the configuration file with login information
-g is the group name you want to patch

```
cd ~/patch_jobs
p1.py -c sumaconf.yaml -g caasp
```
The p1.py script will write the patch job ID's into a file called joblist_patches.json in the current directory.

The joblist_patches.json will be used in the next step for reboot script as input file.

Now we want to run the r1.py as reboot script to schedule reboot jobs in SUSE Manager. This should be a recurring task running every 10 minutes to evaluate the patch job status.

For the recurring feature I choose to use systemd timer that starts a systemd service to execute the r1.py. So every 10 minutes the r1.py will be executed to see either the patch jobs are done and if a job is completed and a reboot job will be scheduled for the respective system.

Now create a systemd service file and systemd timer file for p1.py
You find the sample files in this repository systemd directory. Put these two files into /etc/systemd/system on SUSE Manager host.
Then run:
```
systemctl daemon-reload
```

