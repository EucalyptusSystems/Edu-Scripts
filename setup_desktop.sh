#!/bin/bash

echo "Starting script..." >> /root/script_run.txt

PASSWORD=`< /dev/urandom /usr/bin/tr -dc A-Za-z0-9 | /usr/bin/head -c8`
/bin/echo $PASSWORD > /root/my_password.txt

/usr/bin/aptitude -y install makepasswd

MKPASSWD=`which makepasswd`

echo "Setup root password" >> /root/script_run.txt

/bin/echo ${PASSWORD} | $MKPASSWD --clearfrom=- --crypt-md5 | /usr/bin/awk '{ print $2 }' | /usr/bin/xargs -I {} usermod -p {} root

#######
# Set up VNC password
#######
if [ ! -d /root/.vnc ]; then
    /bin/mkdir /root/.vnc
    /bin/chmod 700 /root/.vnc
fi

echo "Setup VNC setup." >> /root/script_run.txt

/bin/echo ${PASSWORD} | /usr/bin/vncpasswd -f >/root/.vnc/passwd 

/bin/su - root -c "/usr/bin/vncserver :1 -geometry 1440x900 -depth 16 -nevershared"

########
# Set up SSH non-hashed known hosts
########
if [ ! -d /root/.ssh ]; then
    /bin/mkdir /root/.ssh
    /bin/chmod 700 /root/.ssh
fi

echo "Setup SSH config" >> /root/script_run.txt
 
/bin/echo "HashKnownHosts no" >> /root/.ssh/config

########
# Turn off DNS look ups in SSH
########
echo "Turn off DNS in SSH" >> /root/script_run.txt

echo "UseDNS no" >> /etc/ssh/sshd_config

/usr/sbin/service ssh restart

