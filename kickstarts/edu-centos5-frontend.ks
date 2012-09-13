#platform=x86, AMD64, or Intel EM64T
# System authorization information
auth  --useshadow  --enablemd5
# System bootloader configuration
bootloader --location=mbr
# Partition clearing information
clearpart --all --initlabel --drives=sda,sdb
part / --fstype ext3 --ondisk=sda --size=20000 --start=1 --asprimary
part /mnt/extra --fstype ext3 --ondisk=sda  --grow --size=10000 --asprimary
part /buckets --fstype ext3 --ondisk=sdb --size=40000 --asprimary
part swap --ondisk=sda --size=2000 --asprimary

# Use text mode install
text
# Firewall configuration
firewall --disabled
# Run the Setup Agent on first boot
firstboot --disable
# System keyboard
keyboard us
# System language
lang en_US
# System timezone
timezone --utc America/Los_Angeles
# Use network installation
url --url=$tree
# If any cobbler repo definitions were referenced in the kickstart profile, include them here.
$yum_repo_stanza
# Network information
$SNIPPET('network_config')
# Reboot after installation
reboot

#Root password
rootpw --iscrypted 
# SELinux configuration
selinux --disabled
# Do not configure the X Window System
skipx
# System timezone
timezone  America/New_York
# Install OS instead of upgrade
install
# Clear the Master Boot Record
zerombr
# Allow anaconda to partition the system as needed
autopart


%pre
$SNIPPET('log_ks_pre')
$kickstart_start
$SNIPPET('pre_install_network_config')
# Enable installation monitoring
$SNIPPET('pre_anamon')

%packages
@base
@core
@editors
keyutils
iscsi-initiator-utils
trousers
bridge-utils
fipscheck
device-mapper-multipath
-@ X Window System
-@ GNOME Desktop Environment
-@ Graphical Internet
-@ Sound and Video
$SNIPPET('func_install_if_enabled')
$SNIPPET('puppet_install_if_enabled')

%post
$SNIPPET('log_ks_post')
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
$SNIPPET('install_pub_key')
# Enable post-install boot notification
$SNIPPET('post_anamon')
# Start final steps
$SNIPPET('kickstart_done')
# End final steps