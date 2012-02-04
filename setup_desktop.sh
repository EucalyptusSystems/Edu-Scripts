#!/bin/bash

echo "Starting script..." >> /root/script_run.txt

echo "Setting the hostname..." >> /root/script_run.txt
#
# Get the public IP address, run host to do a reverse lookup, but it out of the
# host reply and finally strip off the final period (.)
#
HOSTNAME=`curl -s http://169.254.169.254/latest/meta-data/public-ipv4 | xargs -I {} host {} | cut -d' ' -f5 | cut -d'.' -f1-3`
hostname $HOSTNAME

#
# Set the password for the system and VNC
#
# Passwords will be based on a weekly word. This value will be taken and have
# the desktop number stripped from the reverse lookup added to it. This password
# will then be crypted for both the system and VNC to allow user access to either.
#
WORD=""

DESKTOP_NUM=`echo $HOSTNAME | cut -d'.' -f1 | sed -Ee 's/[a-z\-]//g'`
PASSWORD=`echo ${WORD}${DESKTOP_NUM} | tr [:upper:] [:lower:]`


/bin/echo $PASSWORD > /root/my_password.txt

#
# Install makepasswd and create the hash for the system.
#
/usr/bin/aptitude -y install makepasswd

MKPASSWD=`which makepasswd`

echo "Setup root password" >> /root/script_run.txt

/bin/echo ${PASSWORD} | $MKPASSWD --clearfrom=- --crypt-md5 | /usr/bin/awk '{ print $2 }' | /usr/bin/xargs -I {} usermod -p {} root

#
# Set up VNC password
#
# If the /root/.vnc directory does not exist then first create it. After this run
# the vncpasswd utility to create the stupid hash that VNC uses for auth.
#
# We may possibly remove this as it may be easier to setup user accounts and run a
# DM that the user will use to login to the desktop at a later date.
#
if [ ! -d /root/.vnc ]; then
        /bin/mkdir /root/.vnc
            /bin/chmod 700 /root/.vnc
            fi

            echo "Setup VNC setup." >> /root/script_run.txt

            /bin/echo ${PASSWORD} | /usr/bin/vncpasswd -f >/root/.vnc/passwd 

#
# Start the VNC server as the root user. Need to use su since we may still be before
# boot so we don't have a complete environment like VNC needs.
#
/bin/su - root -c "/usr/bin/vncserver :1 -geometry 1440x900 -depth 16 -nevershared"

#
# Set up SSH non-hashed known hosts
#
# This should probably be eventually changed in the config for the system on the image
# that we are using for the desktops but I'm lazy and haven't do this yet.
#
if [ ! -d /root/.ssh ]; then
        /bin/mkdir /root/.ssh
            /bin/chmod 700 /root/.ssh
            fi

            echo "Setup SSH config" >> /root/script_run.txt
             
             /bin/echo "HashKnownHosts no" >> /root/.ssh/config

#
# Turn off DNS look ups in SSH
#
# Again this should probably be placed into the image if I ever create another image that we
# want to use.
#
echo "Turn off DNS in SSH" >> /root/script_run.txt

echo "UseDNS no" >> /etc/ssh/sshd_config

/usr/sbin/service ssh restart
