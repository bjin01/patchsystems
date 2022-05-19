# Collect system patch status by CVE

This script helps to get a list of systems which have the respective CVE not patched yet. It is similar as the CVE Audit in the SUSE Manager UI function. The script will generate a csv file for users to import into Excel list.

You need a suma_config.yaml file with login and email notification address.
If email notification will be used then you need to have mutt email client installed and postfix configured. 

Sample suma_config.yaml:
suma_host: mysumaserver.mydomain.local
suma_user: <USERNAME>
suma_password: <PASSWORD>
notify_email: <EMAIL_ADDRESS>

Usage:
The CVE must be provided. The name of CVE is case-sensitive.
```
python3.6 getcve_info.py --config ~/suma_config.yaml --cve CVE-2021-34556
```

Output:
```
/var/log/cve_info.csv
```
