# SUMA package check script

The query_rpms.py for SUSE Manager/Uyuni queries the package metadata from the SUSE Manager via API and verifies if the package file and its checksum also match the path and checksum stored in the SUSE Manager database.

## How to use it:

1. Download the script to the local SUSE Manager host.

    ```wget https://github.com/bjin01/patchsystems/blob/master/rpm/query_rpms.py```

2. Create a suma_config.yaml file with login data provided.
Write a yaml file with below parameters and values.
```
suma_host: bjsuma.bo2go.home
suma_user: bjin
suma_password: suse1234
```

3. Run the script:
```
python3.6 query_rpms.py -v -c ./suma_config.yaml -l sle-module-containers15-sp2-pool-x86_64-sap
```
__If you provide a channel label that has child channels then all child channels will be "verified" as well.__

__If the SUMA host memory usage is higher than 80% then the script gives a  warning and exits with error.__

__If you use parameter "-v" for verbosity then you will get a bit more output.__

__The output will be stored in a log file ```/var/log/rhn/query_rpms.log```__

