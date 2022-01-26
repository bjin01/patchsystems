# Scripts to be used for Automic workflows.
The python3 scripts will be used by AUTOMIC in order to schedule patch and reboot jobs according previous job status.

## Technical prerequisites:
Following rpm packages will be needed on the respective linux host on which the python scripts should be executed.
This three packages can be found in SUSE Manager Product repositories.
python3.6, python3-pyYaml, python3-salt 

To run the scripts the host need to be able to reach SUSE Manager via the network by ideally through FQDN and you must have SUSE Manager API logon credentials.
In order to make HTTPS ssl handshake the CA file must be also placed on the respective host.

The SUSE Manager hostname and logon credentials must be stored in a yaml config file. Below we a config file named "suma_config.yaml".
Look at the sample config file in this foleder.
The email address for notification is optional. 

The optional parameter --email will attach the log file and send it via email on the host if postfix is configured and mutt is installed.


## The workflow:
__Step 1:__
    * query host list of a given group in SUSE Manager. The list will show the hostnames with number of outstanding patches.

```
python3.6 checkhosts.py --config suma_config.yaml --group mygroup 
Systeme mit installierbaren Patches:
caasp01.bo2go.home: 202
caasp02.bo2go.home: 18
pxenode01: 82
```

__Step 2:__
    * Automic executes the patchsystems.py script and triggers a patch job. The output shows hostname and its jobid.
```
python3.6 patchsystems.py --config suma_config.yaml --systemname caasp01.bo2go.home
Patch Job:
caasp01.bo2go.home: 12290
```

__Step 3:__
    * Automic uses the jobid of previous script output to query the job status. The job status can be "inprogress", "failed" or "completed" and Automic will trigger a reboot job if previous job was successful..
```
python3.6 checkjobstatus.py --config suma_config.yaml --jobid 12290
Patch Update: 12290: inprogress
```

__Step 4:__
    * After the previous step finished and the patch job reached a final state either failed or completed then Automic will trigger a reboot job if previous job was successful.
```
python3.6 rebootsystems.py --config suma_config.yaml --systemname caasp01.bo2go.home
Reboot Job:
caasp01.bo2go.home: 12289
```

__Step 5:__
    * After reboot job reached a final state, either failed or completed then automic finished the patching workflow.


## Logs:
/var/log/automic_suma_checkhosts.log
/var/log/automic_suma_patchsystems.log
/var/log/automic_suma_checkjobstatus.log
/var/log/automic_suma_rebootsystems.log
