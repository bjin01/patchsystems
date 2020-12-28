# SUSE Manager Hub - sample script - List systems from peripheral SUSE Managers

The script utilizes a yaml config file to read the peripheral suse manager hostnames, user_login and password.
Have a look at the suma_servers.yaml file as example.
The user login and passwords for hub server and all peripheral suma servers, you want to talk to, should be stored in the yaml file.

This is a more "advanced - hello world" python script that shows how to talk to multiple suma servers using SUSE Manager Hub.

Run it:
```python hubconnect.py```

