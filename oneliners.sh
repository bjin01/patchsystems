#Get vendors which are not SUSE from the RPMDB
rpm -qa --qf "%{NAME} %{VERSION} %{VENDOR}\n" | grep -v SUSE
