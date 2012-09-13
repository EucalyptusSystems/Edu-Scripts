#platform=x86, AMD64, or Intel EM64T
# System authorization information
auth  --useshadow  --enablemd5
# System bootloader configuration
bootloader --location=mbr
# Partition clearing information
clearpart --all --initlabel
# Firewall configuration
firewall --disabled
# Run the Setup Agent on first boot
firstboot --disable
# System keyboard
keyboard us
# System language
lang en_US
# Use network installation
url --url=$tree
# If any cobbler repo definitions were referenced in the kickstart profile, include them here.
$yum_repo_stanza
# Network information
$SNIPPET('network_config')
# Reboot after installation
reboot

# Use a text based installation
text
#Root password
rootpw --iscrypted 
# SELinux configuration
selinux --disabled
# Do not configure the X Window System
skipx
# System timezone
timezone --utc America/Los_Angeles
# Install OS instead of upgrade
install
# Disable the abrt and auditd services
services --disabled abrt,auditd
# Clear the Master Boot Record
zerombr
# System bootloader configuration
bootloader --location=mbr
# Partitioning
part / --fstype ext3 --ondisk=sda --size=20000 --asprimary
part /mnt/extra --fstype ext3 --ondisk=sda  --grow --size=10000 --asprimary
part /instances --fstype ext3 --ondisk=sdb --grow --size=10000 --asprimary
part swap --ondisk=sda --size=2000 --asprimary

%pre
$SNIPPET('log_ks_pre')
$SNIPPET('kickstart_start')
$SNIPPET('pre_install_network_config')
# Enable installation monitoring
$SNIPPET('pre_anamon')

%packages
$SNIPPET('func_install_if_enabled')
$SNIPPET('puppet_install_if_enabled')
@Base
@Core
keyutils
iscsi-initiator-utils
trousers
bridge-utils
fipscheck
device-mapper-multipath
wget
-pcmciautils

%post
$SNIPPET('log_ks_post')
$SNIPPET('install_pub_key')
# Start yum configuration 
$yum_config_stanza
# End yum configuration
$SNIPPET('post_install_kernel_options')
$SNIPPET('es_post_install_network_config')
$SNIPPET('func_register_if_enabled')
$SNIPPET('puppet_register_if_enabled')
$SNIPPET('download_config_files')
$SNIPPET('koan_environment')
$SNIPPET('redhat_register')
$SNIPPET('cobbler_register')
# Enable post-install boot notification
$SNIPPET('post_anamon')
# Start final steps
$SNIPPET('kickstart_done')
# End final steps