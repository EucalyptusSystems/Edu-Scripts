#!/usr/bin/python2.6

"""
This script will enable an instructor to quickly and easily reset the pods
in the education cloud setup. This should allow the instructor to run a couple
short commands and end up with a brand-new system setup.

Of course this will evolve over time with the needs and requirements that the
Eucalyptus Education Cloud creates

Andrew Hamilton
Systems Administrator
Eucalyptus Systems
12/14/11
"""

import xmlrpclib
import sys
from cryptacular.crypt import CRYPTPasswordManager
from fabric.api import *
import random
import string
import edu_config

usage_string = """
Setup pods for Eucalyptus Systems training classes.

edu_setup [--set-password] [--all-pods] [--pod=XX] [--frontend=XX] [--node=XX]

OPTIONAL PARAMETERS

--set-password      This will cause a random root password to be set on any pods
                    which are mentioned with either --all-pods or --pod=XX.
                    Note: You cannot change the password on a single system
                    in a pod. Both systems must have change the root password.

--all-pods          Run the operation on all of the training pods. This can only
                    be mentioned once and all other delarations will be ignored.

--pod=XX            Run the operation on pod number XX. This flag can be used
                    multiple times.

--frontend=XX       Run the operation on only the frontend of pod number XX. 
                    This flag may be used multiple times. NOTE: This value is
                    not valid in conjunction with the --set_password hook.

--node=XX           Run the operation on only the node of pod number XX. This
                    flag may be used multiple times. NOTE: This value is not 
                    valid in conjunction with the --set_password hook.

-h, --help          Print this help text.
"""

def usage():
    print usage_string
    exit()

def setup_netboot(system_name, remote, token):
    """
    Setup netboot on the system given to this command through the XMLRPC
    interface to cobbler. We use the "netboot enabled" property and set it
    to True. Then we must save the settings so that cobbler server makes the
    setting effective.

    system_name -- String with the name of the system
    remote -- xmlrpclib server connection to the cobbler server
    token -- Token to modify settings on the cobbler server
    """

    handle = remote.get_system_handle(system_name, token)
 
    remote.modify_system(handle, "netboot_enabled", True, token)

    result = remote.save_system(handle, token)

    return result
def reboot_system(system_name, remote):
    """
    Reboot the system so that a kickstart will happen.

    system_name -- name of the system to perform the task on
    remote -- XMLRPC handler to use for accessing the Cobbler API
    """

    env.disable_known_hosts = True

    system = remote.get_system(system_name)
    env.host_string = system['interfaces']['eth0']['ip_address']
 
    run('/sbin/reboot')

def gen_passphrase(size):
    """
    Create a passphrase that will then be turned into a crypt.

    size -- This will be the number of characters of the resulting passphrase
    """

    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits

    return ''.join(random.choice(chars) for x in range(size))    

def create_crypt(password):
    """
    Create a basic crypted password hash to use on the system.

    password -- password string that has not been crypted
    """
    
    manager = CRYPTPasswordManager('$1$')
    crypt = manager.encode(password)

    return crypt

def remote_set_password(system_name, crypt):
    """
    Set the password on the remote machine using 'usermod' and the crypt that
    that was created earlier.

    system_name -- name of the system to perform the task on
    crypt -- password crypted to be used
    """

    env.disable_known_hosts = True

    system = remote.get_system(system_name)
    env.host_string = system['interfaces']['eth0']['ip_address']

    run('/usr/sbin/usermod -p \'' + crypt + '\' root')    

def set_pod_passwords(pods, password_size):
    """
    Set the pod passwords. In this method we do all of the other steps that
    are needed such as passphrase generation, crypt generation, and finally 
    modification of the remote system's root password. To keep consistent
    passwords on both frontend and node machines we only allow for entire pod
    passwords to be changed. This relieves the student from needing to remember
    two passwords for his single pod.

    pods -- Integer list of posts to be updated.
    password_size -- Size of the passphrase to be generated.
    """

    for pod in pods:
        if pod < 10:
            frontend = "pod0" + str(pod) + "-frontend"
            node = "pod0" + str(pod) + "-node"
        else:
            frontend = "pod" + str(pod) + "-frontend"
            node = "pod" + str(pod) + "-node"

        print frontend + " " + node
    
        #password = gen_passphrase(password_size)
	password = "eucalyptus"
        
        print "Password given to the systems in Pod " + str(pod) + ": " + password
        
        crypt = create_crypt(password)
        print crypt

        remote_set_password(frontend, crypt)
        remote_set_password(node, crypt)

def get_all_pods(remote):
    """
    A simple lookup for all hostnames that begin with "pod" on the cobbler
    server. Cobbler allows for non-administrative actions to be token less
    so we don't pass the token to this function.

    remote -- xmlrpclib server connection to the cobbler server
    """

    pods = remote.find_system({"hostname":"*"})
    return pods

def connect_to_cobbler(server, username, password):
    """
    Make the connection to the cobbler server that will be used for the
    all operations on the system. This will keep from having to make a 
    connection everytime we perform an operation on the server and should
    keep a (possible) huge connection load on the cobbler server

    server -- The IP or FQDN of the cobbler server
    username -- Username with admin rights on the cobbler server
    password -- Password of the corresponding username above
    """

    remote = xmlrpclib.Server("http://" + server + "/cobbler_api")
    token = remote.login(username, password)

    return remote, token

pods = []
server = edu_config.CBLR_SERVER
username = edu_config.CBLR_USER
password = edu_config.CBLR_PASS
remote, token = connect_to_cobbler(server, username, password)
set_password = False
password_size = 10

if sys.argv[1] == "--testing":
    print "Server: " + server
    print "Username: " + username
    print "Password: " + password
    exit()
if len(sys.argv) == 1:
    usage()
elif sys.argv[1] == "--set-password":
    set_password = True
    for arg in sys.argv[2:]:
        if arg == "--all-pods":
            pods = [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
                    11, 12, 13, 14, 15, 16, 17, 18 ]
            break
        elif arg[:6] == "--pod=":
            pods.append(int(arg[6:]))
        else:
            usage()
else:
    for arg in sys.argv[1:]:
        if arg == "--all-pods":
            pods = get_all_pods(remote)
            break
        elif arg[:6] == "--pod=":
            current_pod = arg[6:]
            if len(current_pod) == 1:
                pods.append("pod0" + str(current_pod) + "-frontend")
                pods.append("pod0" + str(current_pod) + "-node")
            else:
                pods.append("pod" + str(current_pod) + "-frontend")
                pods.append("pod" + str(current_pod) + "-node")
        elif arg[:11] == "--frontend=":
            current_pod = arg[11:]
            if len(current_pod) == 1:
                pods.append("pod0" + str(current_pod) + "-frontend")
            else:
                pods.append("pod" + str(current_pod) + "-frontend")
        elif arg[:7] == "--node=":
            current_pod = arg[7:]
            if len(current_pod) == 1:
                pods.append("pod0" + str(current_pod) + "-node")
            else:
                pods.append("pod" + str(current_pod) + "-node")
        else:
            usage()

if set_password == True:
    set_pod_passwords(pods, password_size)
else:
    for system in pods:
        result = setup_netboot(system, remote, token)
        if result == True:
            print "Success for " + system    
        
        reboot_system(system, remote)    

