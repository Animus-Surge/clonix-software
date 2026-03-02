#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  echo "FATAL: Must be run as root!"
  exit 1
fi

# TODO: Transition to live image, arch
# TODO: Write pxe boot setup systems in powershell
# TODO: Extra packages
# TODO: Error handling and error checking
# TODO: Extra install options (i.e. get this tarball and extract it here, make these
#       desktop entries, add this config, etc); might be handled by parent script (python)

skip_bootmgr=true

output_log=/dev/stdout
source_file=
target=
dry_run=false
use_luks=false
use_tpm=false
use_btrfs=false
is_dualboot=false
btrfs_compress_alg=zstd
hostname=egr-u-invalid
extra_pkgs=()

usage() {
echo "Usage: $0 -f <archive> -t <target> [OPTIONS]"
echo ""
echo "This script prepares and deploys a compressed system image"
echo "(filesystem or disk image) onto a target drive, with"
echo "optional encryption, btrfs, and extra packages support."
echo ""
echo "Required Arguments:"
echo "  -f, --file <path>     : Input compressed file, prefers zstd"
echo "  -t, --target <path>   : Target device (e.g. /dev/sda, /dev/nvme0n1)"
echo ""
echo "Optional Flags and Options:"
echo "  -b, --btrfs           : Use btrfs instead of ext4"
echo "  -c, --compress <alg>  : btrfs compression algorithm (default zstd)"
echo "  -d, --dual-boot       : Configure grub to scan for other operating systems"
echo "  -D, --dry-run         : Give a complete summary of what would happen, without doing anything"
echo "  -l, --luks            : Enable LUKS encryption"
echo "  -L, --log-file        : Specifies output for most log information (Defaults /dev/stdout)"
echo "  -m, --tpm             : Use the system TPM for encryption (enables luks)"
echo "  -n, --hostname <name> : Target's hostname (default egr-u-invalid)"
echo "  -p, --package <pkg>   : An extra package to add to the cloned image (can be used multiple times)"
echo "  -r, --property <k/v>  : A key-value option. Appended to props.conf."
echo "  -R, --conf-file <file>: The file to use instead of props.conf. Must be a bash script."
echo ""
echo "  -h, --help            : Display this help message."
echo ""
exit 1
}

# Argument parsing
opts=$(getopt -o f:t:ldDbmc:sn:p:r:R:L:h --long file:,target:luks,dual-boot,dry-run,btrfs,tpm,compress:,hostname:,package:,property:,conf-file:,--log-file,help -n "$0" -- "$@")

if [ $? != 0 ]; then
echo "ERROR: failed to parse options." >&2 ; usage
fi

eval set -- "$opts"

# remove old props.conf
rm -f props.conf

while true; do
  case "$1" in
  -D|--dry-run)
    dry_run=true
    shift
    ;;
  -d|--dual-boot)
    is_dualboot=true
    shift
    ;;
  -f|--file)
    source_file="$2"
    shift 2
    ;;
  -t|--target)
    target="$2"
    shift 2
    ;;
  -l|--luks)
    use_luks=true
    shift
    ;;
  -L|--log-file)
    $output_log="$2"
    shift 2
    ;;
  -m|--tpm)
    use_luks=true
    use_tpm=true
    shift
    ;;
  -b|--btrfs)
    use_btrfs=true
    shift
    ;;
  -c|--compress)
    btrfs_compress_alg="$2"
    shift 2
    ;;
  -n|--hostname)
    hostname="$2"
    shift 2
    ;;
  -p|--package)
    # Convert comma-separated string into a bash array
    echo "WARN: Extra packages functionality is currently unimplemented."
    # extra_pkgs="$2 $extra_pkgs"
    shift 2
    ;;
  -r|--property)
    key=${2%%=*}
    value=${2#*=}

    if [[ "key" == "value" ]]; then
      echo "ERROR: property must be in key=value format. Skipping $2"
    else
      echo "export $key=\"$value\"" >> props.conf
    fi
    shift 2
    ;;
  -R|--conf-file)
    . $2
    shift 2
    ;;
  -h|--help)
    usage
    ;;
  --)
    # End of options marker
    shift
    break
    ;;
  *)
    echo "Internal error in argument parsing: $1" >&2
    usage
    ;;
  esac
done

if [[ -f props.conf ]]; then
  . ./props.conf
fi

# Validations

# Determine required options specified
if [ -z "$source_file" ] || [ -z "$target" ]; then
  echo "ERROR: Both source file (-f) and target (-t) options must be specified." >&2
  usage
fi

# Check if the archive exists
if [ ! -f "$source_file" ]; then
  echo "ERROR: Source $source_file does not exist. Unable to continue." >&2
  exit 1
fi

# TODO: other checks; assume everything else is fine (for now)

# Gather system information

i_tpmver=N/A

## TPM
dmesg | grep -i tpm > /dev/null
if [ $? -eq 0 ] && $use_tpm; then
  if [[ -e /dev/tpm0 ]]; then
    if [[ -e /dev/tpmrm0 ]]; then
      i_tpmver="2.0"
    else
      i_tpmver="1.2"
    fi
  else
    echo "ERROR: No TPM device was found, and you had specified to use the TPM. Disabling TPM."
    echo "NOTE:"
    echo "If this is incorrect, you can fix this post-install by performing TPM steps manually."
    echo "See https://wiki-vcu.atlassian.net/wiki/spaces/~712020cfcf61261297472abb6d62d34d4c8490/pages/572752306/systemd-cryptenroll"
    echo "or https://wiki-vcu.atlassian.net/wiki/spaces/~712020cfcf61261297472abb6d62d34d4c8490/pages/573898777/tpm-tools"
    echo "for more information."
    echo ""
    use_tpm=false
  fi
fi

# Output summary

echo "Summary:"
echo "Source: $source_file"
echo "Target: $target"
echo "Use LUKS: $use_luks"
if $use_luks; then
  echo "Use TPM: $use_tpm"
  echo "TPM version: $i_tpmver"
fi
echo "Use BTRFS: $use_btrfs"
echo "Dualboot system: $is_dualboot"
echo "Target Hostname: $hostname"
echo "Extra Packages: ${extra_pkgs[*]:-None}"
echo ""

# Check if target is nvme
partition_prefix=
if [[ "$target" == *nvme* ]]; then
  partition_prefix=p
fi
# TODO: allow the user to change something on the fly

# BEGIN DRY RUN SUMMARY BLOCK
if $dry_run; then
  echo ""
  echo "Summary of changes and steps taken:"
  echo "- Formatting:"
  echo " - parted $target -- mklabel gpt"
  echo " - parted $target -- mkpart primary fat32 8MiB 1GiB"
  echo " - parted $target -- set 1 esp on"
  echo " - mkfs.vfat -F 32 $target${partition_prefix}1"
  if $use_luks; then
    echo " - parted $target -- mkpart primary ext4 1GiB 3GiB"
    echo " - parted $target -- mkpart primary ext4 3GiB 100%"
    echo " - mkfs.ext4 $target${partition_prefix}2"
    echo " - cryptsetup luksFormat -q \"$target${partition_prefix}3\""
    echo " - cryptsetup luksOpen \"$target${partition_prefix}3 dm_crypt-0"
    if $use_btrfs; then
      echo " - mkfs.btrfs /dev/mapper/dm_crypt-0"
    else
      echo " - mkfs.ext4 /dev/mapper/dm_crypt-0"
    fi
    echo "- Mount: mount $target${partition_prefix}3 /target"
  else
    echo " - parted $target -- mkpart primary ext4 1GiB 100%"
    if $use_btrfs; then
      echo " - mkfs.btrfs $target${partition_prefix}2"
    else
      echo " - mkfs.ext4 $target${partition_prefix}2"
    fi
    echo "- Mount: mount $target${partition_prefix}2 /target"
  fi
  
  echo "- Clone: "
  echo " - Copy $source_file to $target root partition"
  echo "  - pcstd -dcq $source_file | pv -pbert | tar -xpf - -C /target 2>/dev/null"
  echo "BEGIN POST INSTALL "
  if $use_luks; then
    echo "- mkdir -p /target/boot"
    echo "- mount $target${partition_prefix}2 /target/boot"
  fi
  echo "- mkdir -p /target/boot/efi"
  echo "- mount $target${partition_prefix}1 /target/boot/efi"
  for dir in dev proc run sys; do
    echo "- mount --bind /$dir /target/$dir"
  done
  echo "- Update /target/etc/fstab with new fs uuids"
  echo "- chroot /target"
  echo "BEGIN CHROOT"
  echo "- Reinstall linux-image* with target kernel version"
  echo "- Reinstall grub:"
  echo " - grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=ubuntu --recheck"
  echo " - grub-mkconfig -o /boot/efi/EFI/ubuntu/grub.cfg"
  echo "- Update /etc/crypttab:"
  if $use_luks; then
    if $use_tpm; then
      echo " - Activate TPM"
      if [ "$i_tpmver" == "1.2" ]; then
        echo "  - tpm_takeownership -y -z"
        echo "  - dd if=/dev/urandom of=/run/user/1000/tpm.key bs=1 count=256"
        echo "  - tpm_nvdefine -i 1 -s 256 -y -z -p 'READ_STCLEAR|OWNERWRITE' -r 7"
        echo "  - tpm_nvwrite -i 1 -s 256 -f /run/user/1000/tpm.key -z"
        echo "  - shred -u /run/user/1000/tpm.key"
        echo "  - crypttab: dm_crypt-0 UUID=... /mnt/tpm/key luks"
        echo "  - 10-encrypt.conf: "
        echo "      omit_dracutmodules+=\" tpm2-tss \""
        echo "      install_items+=\" /etc/crypttab \""
        echo "  - apt-get autopurge tpm2-tools"
      fi
      if [ "$i_tpmver" == "2" ]; then
        echo "  - systemd-cryptenroll $target${partition_prefix}3 --tpm2-device=auto"
        echo "  - crypttab: dm_crypt-0 UUID=... none luks,tpm2-device=auto"
        echo "  - 10-encrypt.conf: "
        echo "      omit_dracutmodules+=\" tpm12 \""
        echo "      install_items+=\" /etc/crypttab \""
        echo "  - apt-get autopurge trousers"
      fi
    else
      echo "  - crypttab: dm_crypt-0 UUID=... none luks"
      echo "  - 10-encrypt.conf: "
      echo "      omit_dracutmodules+=\" tpm12 tpm2-tss \""
      echo "      install_items+=\" /etc/crypttab \""
    fi
  else
    echo " - rm /etc/dracut.conf.d/10-encrypt.conf"
    echo " - apt-get autopurge tpm2-tools trousers"
  fi
  echo "- echo \"$hostname\" > /etc/hostname"
  echo "- dracut -f -kver /lib/modules/..."
  echo "END CHROOT"
  echo "- systemctl --root=/target enable puppet-first-run.service"
  echo "END MAIN INSTALL"
  echo "BEGIN POST-INSTALL"
  if $use_btrfs; then
    echo "- Compress filesystem; btrfs filesystem defragment"
  fi
  echo "- Write first-boot script and service"
  if ! $skip_bootmgr; then
    echo "- Reset UEFI boot entries"
  fi
  echo "END POST-INSTALL"
  echo "Done."
  exit 0
fi
# END DRY RUN SUMMARY BLOCK

echo "WARNING: These next steps will destroy ANY AND ALL DATA on $target. Please confirm you would like to continue."
read -r -p "Continue (y/N) > " start_conf
if [[ ! $start_conf =~ ^[Yy]$ ]]; then
  echo "WARNING: Aborting..."
  exit 0
fi

# LUKS passphrase, if applicable
if $use_luks; then
  while true; do
    luks_pk=
    echo "Please enter a passphrase for the LUKS volume."
    read -r -s -p "> " luks_pk1
    echo ""
    echo "Please enter it again."
    read -r -s -p "> " luks_pk2
    echo ""
    if [[ -z "$luks_pk1" ]]; then
      echo "ERROR: Passphrase cannot be empty. Try again."
    elif [[ $luks_pk1 == $luks_pk2 ]]; then
      luks_pk=$luks_pk1
      unset luks_pk1 luks_pk2
      break
    else
      echo "ERROR: Passphrases did not match. Try again."
    fi
  done
fi

mkdir -p /target

# Ensure no mounts active
. ./deactivate_target.sh 2>/dev/null
. ./deactivate_source.sh 2>/dev/null

echo $(date) >> $output_log
echo "INFO: Starting deployment." >> $output_log


echo "TASK 1: partition drive." >> $output_log

mkdir -p /target

if $use_luks; then
  # Create table, partitions, set ESP for esp partition
  parted $target --script mklabel gpt \
    mkpart primary fat32 8M 1G \
    mkpart primary ext4 1G 3G \
    mkpart primary ext4 3G 100% \
    set 1 esp on >> $output_log

  udevadm settle

  # Format partitions
  yes | mkfs.vfat -F 32 ${target}${partition_prefix}1 >> $output_log
  yes | mkfs.ext4 ${target}${partition_prefix}2 >> $output_log
  echo -n "$luks_pk" | cryptsetup luksFormat -q "${target}${partition_prefix}3" - >> $output_log
  echo -n "$luks_pk" | cryptsetup luksOpen "${target}${partition_prefix}3" "dm_crypt-0" - >> $output_log

  # LVM setup
  pvcreate "/dev/mapper/dm_crypt-0" >> $output_log
  vgcreate "ubuntu-vg" "/dev/mapper/dm_crypt-0" >> $output_log
  lvcreate -n "ubuntu-lv" -l 100%FREE "ubuntu-vg" >> $output_log

  if $use_btrfs; then
    yes | mkfs.btrfs "/dev/mapper/dm_crypt-0" >> $output_log
  else
    yes | mkfs.ext4 "/dev/mapper/dm_crypt-0" >> $output_log
  fi

  echo "SUCCESS: Created EFI partition at $target${partition_prefix}1" >> $output_log
  echo "SUCCESS: Created boot partition at $target${partition_prefix}2" >> $output_log
  echo "SUCCESS: Created encrypted root partition at $target${partition_prefix}3" >> $output_log

else
  parted $target --script mklabel gpt \
    mkpart primary fat32 8M 1G \
    mkpart primary ext4 1G 100% \
    set 1 esp on >> $output_log

  udevadm settle

  yes | mkfs.vfat -F 32 ${target}${partition_prefix}1 >> $output_log

  if $use_btrfs; then
    yes | mkfs.btrfs ${target}${partition_prefix}2 >> $output_log
  else
    yes | mkfs.ext4 ${target}${partition_prefix}2 >> $output_log
  fi

  echo "SUCCESS: Created boot partition at $target${partition_prefix}1" >> $output_log
  echo "SUCCESS: Created root partition at $target${partition_prefix}2" >> $output_log
fi

echo "INFO: Partitioning complete." >> $output_log

echo "TASK 2: Copy base system image" >> $output_log

chroot="/target"

# Mount root
if $use_luks; then
  mount "/dev/mapper/dm_crypt-0" "$chroot"
else
  mount "$target${partition_prefix}2" "$chroot"
fi

# Copy compressed system
if echo "$source_file" | grep "http"; then
  # Use server
  if curl -L --progress-bar "$source_file" | pzstd -dc | tar -xf - -C /target 2> /dev/null; then
    echo "SUCCESS: Successfully copied base image to /target" >> $output_log
  else
    echo "ERROR: Failed to copy base image to /target. See above for details."
    echo "FATAL: Unable to continue."
    exit 1
  fi
else
  # Use tarball
  if pzstd -dcq "$source_file" | pv -pbert | tar --xattrs --xattrs-include='*' -xpf - -C "/target" 2>/dev/null; then
    echo "SUCCESS: Successfully copied base image to /target." >> $output_log
  else
    echo "ERROR: Failed to copy base image to /target. See above for details."
    echo "FATAL: Unable to continue."
    exit 1
  fi
fi

echo "TASK 3: Post-install steps" >> $output_log

# Mount other partitions

if $use_luks; then
  mkdir -p /target/boot
  mount "$target${partition_prefix}2" "$chroot/boot"
fi
mkdir -p /target/boot/efi
mount "$target${partition_prefix}1" "$chroot/boot/efi"

# Bind mounts
for dir in dev proc run sys; do
  mount --bind "/$dir" "$chroot/$dir"
done

echo "INFO: Updating target fstab..." >> $output_log

# Generate new fstab
efi_uuid=$(blkid -s UUID -o value $target${partition_prefix}1)
echo "/dev/disk/by-uuid/$efi_uuid /boot/efi vfat defaults 0 0" > $chroot/etc/fstab

if $use_luks; then
  root_id=$(ls /dev/disk/by-id/dm-uuid-CRYPT-LUKS2*)
  boot_uuid=$(blkid -s UUID -o value $target${partition_prefix}2)
  root_uuid_crypttab="UUID=$(cryptsetup luksUUID "$target${partition_prefix}3")"
  
  echo "/dev/disk/by-uuid/$boot_uuid /boot ext4 defaults,nodev,nosuid 0 1" >> $chroot/etc/fstab

  if $use_btrfs; then
    echo "$root_id / btrfs defaults,compress=zstd 0 1" >> $chroot/etc/fstab
  else
    echo "$root_id / ext4 defaults 0 1" >> $chroot/etc/fstab
  fi
 
else
  root_uuid=$(blkid -s UUID -o value $target${partition_prefix}2)

  if $use_btrfs; then
    echo "/dev/disk/by-uuid/$root_uuid / btrfs defaults 0 1" >> $chroot/etc/fstab
  else
    echo "/dev/disk/by-uuid/$root_uuid / ext4 defaults 0 1" >> $chroot/etc/fstab
  fi
fi
  
echo "/swap.img none swap sw 0 0" >> $chroot/etc/fstab

# Chroot

kver=$(ls $chroot/lib/modules | head -n 1)
chroot $chroot /bin/bash <<EOT

echo "INFO: chroot into /target."
echo "INFO: Kernel version $kver"

# initrd handling

echo "INFO: Rebuilding initrd..."
apt-get update
apt-get reinstall linux-image-$kver linux-modules-$kver linux-modules-extra-$kver

# GRUB

echo "INFO: Configuring grub..."

if $is_dualboot; then # OS Prober disabled by default in base system image
  echo "INFO: Enabling OS Prober"
  sed '/GRUB_DISABLE_OS_PROBER/s/true/false/' /etc/default/grub > /etc/default/grub
fi

echo "INFO: Installing grub..."
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id="ubuntu" --recheck
grub-mkconfig -o /boot/efi/EFI/ubuntu/grub.cfg

echo "SUCCESS: Successfully installed and configured grub."
EOT

echo "INFO: Updating encryption settings..."

chroot $chroot /bin/bash <<EOT
# Update crypttab and handle encryption

echo "INFO: chroot into /target."

echo "# <target name> <source device>     <key file>  <options>" > /etc/crypttab
if $use_luks; then
  if $use_tpm; then
    echo "INFO: Enabling TPM..."
    if [ "$i_tpmver" == "1.2" ]; then
      apt install -y trousers tpm-tools
      echo "INFO: Running TPM 1.2 tasks..."
      tpm_takeownership -y -z
      dd if=/dev/urandom of=/run/user/1000/tpm.key bs=1 count=256
      tpm_nvdefine -i 1 -s 256 -y -z -p 'READ_STCLEAR|OWNERWRITE' -r 7
      tpm_nvwrite -i 1 -s 256 -f /run/user/1000/tpm.key -z
      shred -u /run/user/1000/tpm.key

      echo "INFO: Updating /etc/crypttab..."
      echo "dm_crypt-0 $root_uuid_crypttab /mnt/tpm/key luks" > /etc/crypttab
      echo 'omit_dracutmodules+=" tpm2-tss "' > /etc/dracut.conf.d/10-encrypt.conf

      apt-get autopurge -y tpm2-tools
    fi
  
    if [ "$i_tpmver" == "2" ]; then
      apt install -y tpm2-tools
      echo "INFO: Running TPM 2.0 tasks..."
      PASSWORD="$luks_pk" systemd-cryptenroll "$target${partition_prefix}3" --tpm2-device=auto
    
      echo "INFO: Updating /etc/crypttab..."
      echo "dm_crypt-0 $root_uuid_crypttab none luks,tpm2-device=auto" > /etc/crypttab
      echo 'omit_dracutmodules+=" tpm12 "' > /etc/dracut.conf.d/10-encrypt.conf

      apt-get autopurge -y trousers
    fi
  else
    echo "dm_crypt-0 $root_uuid_crypttab none luks" > /etc/crypttab
    echo 'omit_dracutmodules+=" tpm2-tss tpm12 "' > /etc/dracut.conf.d/10-encrypt.conf
    apt-get autopurge -y tpm2-tools trousers
  fi
  echo 'install_items+=" /etc/crypttab "' >> /etc/dracut.conf.d/10-encrypt.conf
else
  apt-get autopurge tpm2-tools trousers
fi

echo "SUCCESS: Encryption settings updated."

EOT

echo "INFO: Final configuration, hostname, one more dracut run..."

chroot $chroot /bin/bash <<EOT
# Update hostname
echo "$hostname" > /etc/hostname

# One last reconfigure
dracut -f --kver "$kver"
EOT

echo "INFO: Enabling puppet on first boot..." >> $output_log

truncate -s 0 $chroot/etc/machine-id
systemctl --root=$chroot enable puppet-first-run.service

echo "INFO: Running post-install steps..." >> $output_log

repo1="http://egr-repo1.rams.adp.vcu.edu"
if [ ! -z $extra_pkgs]; then
  #TODO: implement
  echo "WARN: Extra packages functionality is currently unimplemented."
fi

if $use_btrfs; then
  echo "INFO: Compressing filesystem..." >> $output_log
  btrfs -v filesystem defragment -r -c $btrfs_compress_alg $chroot >> $output_log
fi

echo "INFO: Updating UEFI boot order..." >> $output_log
if ! $skip_bootmgr; then
entries=$(efibootmgr | grep '^Boot[0-9A-F]' | sed -E 's/Boot([0-9A-F]{4}).*/\1/')

for entry in $entries; do
  label=$(efibootmgr | grep "^Boot$entry" | cut -d' ' -f2-)

  if $(echo -n $label | grep Current); then
    continue
  fi

  if $is_dualboot && [[ "$label" == *"Windows Boot Manager"* ]] || [[ "$label" == "UEFI:"* ]]; then
    echo "Keeping $entry $label" >> $output_log
  else
    echo "Removing $entry $label" >> $output_log
    efibootmgr -b "$entry" -B > /dev/null 2>&1

    # TODO: add check logic
  fi
done

efibootmgr -c -d "$target" -p 1 -L "Ubuntu" -l '\EFI\ubuntu\shimx64.efi' > /dev/null

echo ""
echo "INFO: Created new boot entry, wiped preexisting linux entries. New boot order:" >> $output_log
efibootmgr >> $output_log

else
  echo "INFO: Skipping running efiboomgr (skip_bootmgr is true)."
fi

echo "INFO: Creating first-run files..." >> $output_log

file_target="$chroot/usr/local/bin/first-run.sh"
service_target="$chroot/etc/systemd/system/first-run.service"

cat <<EOF > $service_target
[Unit]
Description=Initial System Setup
After=NetworkManager.service
Before=display-manager.service
DefaultDependencies=no

[Service]
Type=oneshot
ExecStart=/usr/local/bin/first-run.sh
TimeoutSec=0
StandardOutput=journal+console

[Install]
WantedBy=multi-user.target
EOF

cat <<EOF > $file_target
#!/bin/bash

plymouth display-message --text="Starting timesyncd..."
systemctl start systemd-timesyncd
sleep 7

EOF

chmod +x $file_target

if [[ ! -e $PUPPET_START_ENV ]]; then
  cat <<EOF > $chroot/etc/puppetlabs/puppet/puppet.conf
[main]
server = hemlock.cs.vcu.edu
environment = $PUPPET_START_ENV

[agent]
runtimeout=3h
EOF
else
  cat <<EOF > $chroot/etc/puppetlabs/puppet/puppet.conf
[main]
server = hemlock.cs.vcu.edu

[agent]
runtimeout=3h
EOF
fi

if [[ ! -e $START_PUPPET ]] && $START_PUPPET; then
cat <<EOF >> $file_target
# BEGIN: START_PUPPET
plymouth display-message --text="Running first-boot updates, please wait..."

# Using whatever environment is loaded into /etc/puppetlabs/puppet/puppet.conf
/opt/puppetlabs/bin/puppet agent --test
# END: START_PUPPET
EOF
fi

if [[ ! -e $PUPPET_DISABLE_ON_COMPLETE ]] && $PUPPET_DISABLE_ON_COMPLETE; then
cat <<EOF >> $file_target
systemctl disable --now puppet  # PUPPET_DISABLE_ON_COMPLETE
EOF
fi

if [[ ! -e $PUPPET_CHANGE_ENV_ON_COMPLETE ]] && $PUPPET_CHANGE_ENV_ON_COMPLETE; then
cat <<EOF >> $file_target
sed -Ei "s|^#*[[:blank:]]*environment[[:blank:]]=[[:blank:]].*|environment = $PUPPET_CHANGE_ENV|" /etc/puppetlabs/puppet/puppet.conf   # PUPPET_CHANGE_ENV_ON_COMPLETE
EOF
fi

if [[ ! -e $NVIDIA_DRIVER_INSTALL ]] && $NVIDIA_DRIVER_INSTALL; then
cat <<EOF >> $file_target
# BEGIN NVIDIA_DRIVER_INSTALL
plymouth display-message --text="Installing nvidia driver..."
apt-get install --no-install-recommends -y nvidia-driver-pinning-590
apt-get update
apt-get install --no-install-recommends -y nvidia-driver
# END NVIDIA_DRIVER_INSTALL
EOF
fi

if $use_btrfs; then
  echo '# BEGIN BTRFS COMPRESSION' >> $file_target
  echo 'plymouth display-message --text="Compressing filesystem... [calculating file count]"' >> $file_target
  echo 'filect=$(find / -xdef -type f | wc -l)' $file_target
  echo 'current=0' >> $file_target
  echo 'plymouth display-message --text="Compressing filesystem..."' >> $file_target
  echo "stdbuf -oL btrfs -v filesystem defragment -rc $btrfs_compress_alg | while read -r line; do" >> $file_target
  echo '  ((current++))' >> $file_target
  echo '  pct=(((current / filect) * 100))' >> $file_target
  echo '  plymouth system-update --progress=$pct' >> $file_target
  echo 'done' >> $file_target
  echo '# END BTRFS COMPRESSION' >> $file_target
fi

cat <<EOF >> $file_target
plymouth display-message --text="Updates complete. Waiting for GDM to start..."

systemctl disable first-run
rm /usr/local/bin/first-run.sh
rm /etc/systemd/system/first-run.service
EOF

systemctl --root=$chroot enable first-run.service

if [[ ! -e $INSTALL_LABVIEW_DRIVERS ]] && $INSTALL_LABVIEW_DRIVERS; then
chroot $chroot /bin/bash <<EOT
if $(apt-get list --installed | grep labview-pro-2025-noble); then
  echo "INFO: Installing labview drivers..."

  apt-get install -y ni-488.2 ni-adcs ni-daqmx ni-dcpower ni-dmm ni-ecumc ni-fgen ni-flexrio ni-hwcfg-utility ni-pxiplatformservices ni-fpga-interface ni-rfsa ni-rfsg ni-scope ni-serial ni-switch ni-sync ni-syscfgruntime ni-visa ni-xnet
else
  echo "ERROR: Labview not installed, unable to install drivers."
fi
EOT
fi

echo "SUCCESS: System deployed."
