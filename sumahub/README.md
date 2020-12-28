# SUSE Manager Hub - sample script - List systems from peripheral SUSE Managers

The script utilizes a yaml config file to read the peripheral suse manager hostnames, user_login and password.
Have a look at the suma_servers.yaml file as example.
The user login and passwords for hub server and all peripheral suma servers, you want to talk to, should be stored in the yaml file.

This is a more "advanced - hello world" python script that shows how to talk to multiple suma servers using SUSE Manager Hub.

__Config it:__
First create a yaml config file using below parameters and place the file in the same directory as the python script.
```
hub: sumahub.bo2go.home
hub_user: bjin01
hub_password: suse1234

peripheral_sumas:
  suma1:
    servername: bjsuma.bo2go.home
    username: bjin
    password: suse1234
    active: True

  suma2:
    servername: testserver
    username: testuser
    password: testpasswd
    active: False
```
The "active: True" or "active: False" helps to control which peripheral suse manager server is currently active you want to manage. If active is false then the respective peripheral suse manager server is excluded from the current management.

__Run it:__
```python hubconnect.py```

__Sample Results:__
```
# python hubconnect.py 

Peripheral SUMA Hostname: bjsuma.bo2go.home 1000010000:
system list:
        1: asfasdf
        2: azure-sap-test.bo2go.home
        3: bjlx15
        4: caasp01.bo2go.home
        5: caasp02.bo2go.home
        6: caasp03.bo2go.home
        7: caasp04.bo2go.home
        8: caasp05.bo2go.home
        9: my15sp1test.bo2go.home
        10: mycentos.bo2go.home
        11: myscsi
        12: myutu20.bo2go.home
        13: pampam.bo2go.home
        14: smt1.bo2go.home
        15: testrhel02.bo2go.home
        16: testrhel72.bo2go.home
        17: tomcat1.bo2go.home
        18: tomcat2.bo2go.home
```

