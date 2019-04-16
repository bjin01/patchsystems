# patchsystems
spacewalk patch all systems of a group

The idea is to provide a python script using spacewalk api to patch all systems within a given group.

Commandline sample:
python patchsystems3.py -x -s bjsuma.bo2go.home -u bjin -p suse1234 -g "test1"

The patchsystems3.py will check followings:
1. Is the given group available?
2. Are the systems within group active?
3. Which patches are relevant or applicable for the systems within the given systemgroup?
4. Create patch apply jobs for the affected systems withint the given systemgroup.
5. After job creation the script calls an subprocess script schedulereboot.py to constantly check the remaining patch jobs which have been created within the last two hours and if no more jobs open (pending) then a reboot job will be scheduled.

