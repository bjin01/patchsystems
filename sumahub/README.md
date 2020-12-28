# SUSE Manager Hub - sample script - List systems from peripheral SUSE Managers

The script utilizes a yaml config file to read the peripheral suse manager hostnames, user_login and password.
Have a look at the suma_servers.yaml file as example.
The user login and passwords for hub server and all peripheral suma servers, you want to talk to, should be stored in the yaml file.

This is a more "advanced - hello world" python script that shows how to talk to multiple suma servers using SUSE Manager Hub.

__Run it:
```python hubconnect.py```

__Sample Results:
```
# python hubconnect.py 
Get data from [1000010000], but failed: ['Fault(-1): com.redhat.rhn.common.translation.TranslationException: Could not find translator for class java.lang.String to interface com.redhat.rhn.domain.user.User']
It might be possible that the given peripheral SUMA host is not available.

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

