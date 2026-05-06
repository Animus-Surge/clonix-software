## modules/unlock_disks.py
# Creates `unlock-disks.service` systemd service for unlocking extra disks
# Version: 1.2

# Possible improvements:
# - Use Dracut instead of systemd

SERVICE_FILE = '''
[Unit]
Description=Unlock extra disks
DefaultDependencies=no
Before=local-fs.target
After=cryptsetup-pre.target
Wants=local-fs.target

{uuid_conditions}
ConditionPathExists=/usr/sbin/cryptsetup
ConditionPathExists=/dev/tpm0
{tpmrm0_exists}

[Service]
Type=oneshot
ExecStart=/usr/sbin/unlock-disks.sh

[Install]
WantedBy=sysinit.target
'''

SCRIPT_FILE = '''
#!/bin/bash


'''

def generate_files(extra_disk_uuids):
    """
    Generate systemd service file and unlock-disks.sh script.

    Returns:
        List of lines to add to fstab; None if failure
    """



    pass
