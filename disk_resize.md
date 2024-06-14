# How to extend VMware VM SLES root disk size online without reboot

## Problem
/ disk size is running out of space and you need to extend the root disk size of a SLES VM without reboot.

## Solution
This solution is tested for SLES VMs running on VMware with vmdk files for disk storage.

LVM, multipath, and other disk configurations are not covered in this solution.

### Steps:
** 1. Extend the disk size in VMware - edit settings of the VM and change the disk size. e.g. from 24GB to 48GB.**

__Note:
__If the VM has snapshot levels, you need to delete all snapshots before you can extend the disk size.__

**2. Check the disk size in the VM in running SLES system:**
```bash
rescan-scsi-bus.sh --alltargets
lsblk
```
```
localhost:~ # lsblk /dev/vda
NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINTS
vda    253:0    0   48G  0 disk 
├─vda1 253:1    0  512M  0 part /boot/efi
├─vda2 253:2    0   20G  0 part /usr/local
│                               /var
│                               /tmp
│                               /srv
│                               /root
│                               /opt
│                               /home
│                               /boot/grub2/x86_64-efi
│                               /boot/grub2/i386-pc
│                               /.snapshots
│                               /
└─vda3 253:3    0  3.5G  0 part [SWAP]
```
The block device /dev/vda is now increased to 48GB.

**For KVM and libvirt VMs after block device is increased you can use the following command to tell VM about the disk size change:**
```bash
virsh blockresize --domain test1 vda --size 48GB
```



**3. Check the partition table:**
```bash
fdisk -l /dev/vda
```
```
fdisk -l /dev/vda
GPT PMBR size mismatch (50331647 != 100663295) will be corrected by write.
The backup GPT table is not on the end of the device.
Disk /dev/vda: 48 GiB, 51539607552 bytes, 100663296 sectors
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disklabel type: gpt
Disk identifier: 0754976C-FEE2-44EF-89A1-C580CDFD2EFD

Device        Start      End  Sectors  Size Type
/dev/vda1      2048  1050623  1048576  512M EFI System
/dev/vda2   1050624 42993663 41943040   20G Linux filesystem
/dev/vda3  42993664 50331614  7337951  3.5G Linux swap
```
We see that the disk size is increased to 48GB but the partition table is not updated yet.
We have 3 partitions on the disk: vda1, vda2, vda3. The vda2 partition is the root partition which we want to extend.

But prior to extend the 2nd partition we need to temporarily remove the swap partition vda3.

**4. Backup partition table:**
```bash
sfdisk -d /dev/vda > /tmp/vda-partition-table.bak
```
**5. Disable swap:**
```bash
swapoff /dev/vda3
```
**6. Delete the swap partition:**
```bash
fdisk /dev/vda

Welcome to fdisk (util-linux 2.37.4).
Changes will remain in memory only, until you decide to write them.
Be careful before using the write command.

GPT PMBR size mismatch (50331647 != 100663295) will be corrected by write.
The backup GPT table is not on the end of the device. This problem will be corrected by write.
This disk is currently in use - repartitioning is probably a bad idea.
It's recommended to umount all file systems, and swapoff all swap
partitions on this disk.


Command (m for help): p

Disk /dev/vda: 48 GiB, 51539607552 bytes, 100663296 sectors
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disklabel type: gpt
Disk identifier: 0754976C-FEE2-44EF-89A1-C580CDFD2EFD

Device        Start      End  Sectors  Size Type
/dev/vda1      2048  1050623  1048576  512M EFI System
/dev/vda2   1050624 42993663 41943040   20G Linux filesystem
/dev/vda3  42993664 50331614  7337951  3.5G Linux swap

Command (m for help): d
Partition number (1-3, default 3): 3

Partition 3 has been deleted.

Command (m for help): 

```
Do not type "w" to write the changes yet. We need to extend the 2nd partition first.

**7. Extend the 2nd partition:**
We need to first delete the 2nd partition and create it again.

```bash

Command (m for help): d
Partition number (1,2, default 2): 

Partition 2 has been deleted.

Command (m for help): n
Partition number (2-128, default 2): 
First sector (1050624-100663262, default 1050624): 
Last sector, +/-sectors or +/-size{K,M,G,T,P} (1050624-100663262, default 100663262): +44G

Created a new partition 2 of type 'Linux filesystem' and of size 44 GiB.
Partition #2 contains a btrfs signature.

Do you want to remove the signature? [Y]es/[N]o: N

Command (m for help): 
```
**8. Check the partition table:**
```bash
Command (m for help): p

Disk /dev/vda: 48 GiB, 51539607552 bytes, 100663296 sectors
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disklabel type: gpt
Disk identifier: 0754976C-FEE2-44EF-89A1-C580CDFD2EFD

Device       Start      End  Sectors  Size Type
/dev/vda1     2048  1050623  1048576  512M EFI System
/dev/vda2  1050624 93325311 92274688   44G Linux filesystem

Command (m for help):
```

**9. Create swap partition:**
So we create a new partition and take all remaining free space and toggle the partition type from "Linux filesystem" to "Linux swap".

```bash
Command (m for help): n
Partition number (3-128, default 3): 
First sector (93325312-100663262, default 93325312): 
Last sector, +/-sectors or +/-size{K,M,G,T,P} (93325312-100663262, default 100663262): 

Created a new partition 3 of type 'Linux filesystem' and of size 3.5 GiB.

Command (m for help): t
Partition number (1-3, default 3): 
Partition type or alias (type L to list all): swap

Changed type of partition 'Linux filesystem' to 'Linux swap'.

Command (m for help): 
```

**10. Review the partition table:**
```bash
Command (m for help): p
Disk /dev/vda: 48 GiB, 51539607552 bytes, 100663296 sectors
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disklabel type: gpt
Disk identifier: 0754976C-FEE2-44EF-89A1-C580CDFD2EFD

Device        Start       End  Sectors  Size Type
/dev/vda1      2048   1050623  1048576  512M EFI System
/dev/vda2   1050624  93325311 92274688   44G Linux filesystem
/dev/vda3  93325312 100663262  7337951  3.5G Linux swap

Command (m for help):
```
**11. Write the changes to disk:**
```bash
Command (m for help): w
The partition table has been altered.
Syncing disks.

localhost:~ # 
```
**12. Resize the filesystem:**
In case of filesystem ext3/4 use this command:
```bash
resize2fs /dev/vda2
```

In case of filesystem xfs use this command:
```bash
xfs_growfs /dev/vda2
```

In case of btrfs filesystem use this command:
```bash
btrfs filesystem resize max /
```

**13. Activate swap:**
```bash
mkswap /dev/vda3
swapon /dev/vda3
```
mkswap generates new partion UUID which must be updated in /etc/fstab.
```
mkswap /dev/vda3
Setting up swapspace version 1, size = 3.5 GiB (3757023232 bytes)
no label, UUID=41a063c1-6b88-40a0-bf03-fad15a0a1b73
```
Update /etc/fstab with the new UUID:
```bash
vi /etc/fstab
UUID=41a063c1-6b88-40a0-bf03-fad15a0a1b73  swap                    swap   defaults                      0  0
```


**14. Check the disk size:**
```bash
lsblk
df -hT
free -m
```
Sample output from btrfs filesystem after resizing:
```
df -hT
Filesystem     Type      Size  Used Avail Use% Mounted on
devtmpfs       devtmpfs  4.0M     0  4.0M   0% /dev
tmpfs          tmpfs     2.6G  4.0K  2.6G   1% /dev/shm
tmpfs          tmpfs     710M  9.1M  701M   2% /run
tmpfs          tmpfs     4.0M     0  4.0M   0% /sys/fs/cgroup
/dev/vda2      btrfs      44G  2.6G   42G   6% /
/dev/vda2      btrfs      44G  2.6G   42G   6% /.snapshots
/dev/vda2      btrfs      44G  2.6G   42G   6% /boot/grub2/i386-pc
/dev/vda2      btrfs      44G  2.6G   42G   6% /boot/grub2/x86_64-efi
/dev/vda2      btrfs      44G  2.6G   42G   6% /home
/dev/vda2      btrfs      44G  2.6G   42G   6% /opt
/dev/vda2      btrfs      44G  2.6G   42G   6% /root
/dev/vda2      btrfs      44G  2.6G   42G   6% /srv
/dev/vda2      btrfs      44G  2.6G   42G   6% /tmp
/dev/vda2      btrfs      44G  2.6G   42G   6% /var
/dev/vda2      btrfs      44G  2.6G   42G   6% /usr/local
/dev/vda1      vfat      511M  5.1M  506M   1% /boot/efi
tmpfs          tmpfs     355M  4.0K  355M   1% /run/user/0
```

**15. Done.**



