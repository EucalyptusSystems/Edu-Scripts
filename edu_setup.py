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
from optparse import OptionParser

def modify_system(system_name, prop_name, prop_value, remote, token):
    """
    Generic method to modify systems in cobbler.

    system_name -- String with the name of the system
    prop_name -- name of the property in cobbler to be changed
    prop_value -- value to change the property in cobbler to
    remote -- xmlrpclib server connection to the cobbler server
    token -- Token to modify settings on the cobbler server
    """

    handle = remote.get_system_handle(system_name, token)

    remote.modify_system(handle, prop_name, prop_value, token)

    return remote.save_system(handle, token)
    
def reboot_system(system_name, remote):
    """
    Reboot the system so that a kickstart will happen.

    system_name -- name of the system to perform the task on
    remote -- XMLRPC handler to use for accessing the Cobbler API
    """

    env.disable_known_hosts = True

    system = remote.get_system(system_name)
    env.host_string = system['interfaces']['eth0']['ip_address']
    
    if env.host_string == "":
        env.host_string = system['interfaces']['br0']['ip_address']
 
    run('/sbin/reboot')

def create_crypt(password):
    """
    Create a basic crypted password hash to use on the system.

    password -- password string that has not been crypted
    """
    
    manager = CRYPTPasswordManager('$1$')
    return manager.encode(password)

def remote_set_password(remote, system_name, crypt):
    """
    Set the password on the remote machine using 'usermod' and the crypt that
    that was created earlier.

    remote -- Conection to the Cobbler server
    system_name -- name of the system to perform the task on
    crypt -- password crypted to be used
    """

    env.disable_known_hosts = True

    system = remote.get_system(system_name)
    env.host_string = system['interfaces']['eth0']['ip_address']

    run('/usr/sbin/usermod -p \'' + crypt + '\' root')    

def set_pod_passwords(remote, pods, password_size):
    """
    Set the pod passwords. In this method we do all of the other steps that
    are needed such as passphrase generation, crypt generation, and finally 
    modification of the remote system's root password. To keep consistent
    passwords on both frontend and node machines we only allow for entire pod
    passwords to be changed. This relieves the student from needing to remember
    two passwords for his single pod.

    remote -- Conection to the Cobbler server
    pods -- Integer list of posts to be updated.
    password_size -- Size of the passphrase to be generated.
    """

    for frontend in pods:
        node = frontend[0:5] + "-node"

        print frontend + " " + node
    
        password = "eucalyptus"
        
        print "Password given to the systems in Pod " + frontend[3:5] + ": " + password
        print ""
        
        crypt = create_crypt(password)

        remote_set_password(remote, frontend, crypt)
        remote_set_password(remote, node, crypt)

def print_profiles(profiles):
    """
    Print out the available profiles.

    profiles -- a list of the available profiles for use on the pods
    """

    print "Available profiles for the pods are the following:"

    for profile in profiles:
        print "  %s" % (profile)

def get_profiles(remote):
    """
    Get the available profiles for the pods
    
    remote -- xmlrcplib server connection to the cobbler server
    """

    profiles = remote.find_profile({"name": "edu-*-frontend"})
    my_profiles = []
    
    for profile in profiles:
        my_profiles.append(profile[:(len(profile)-9)])

    return my_profiles

def check_profile(profile, remote):
    """
    Checks the validity of a profile
    
    profile -- profile name
    remote -- xmlrpclib server connection to the cobbler server
    """

    return profile in get_profiles(remote)
    
def check_pods(pods):
    """
    Check to make sure we are working with complete pods and not just random systems.

    pods -- list of pods given to the script
    """

    all_pods = True

    if len(pods) % 2 != 0:
        return False

    for system in pods:
        if "frontend" in system:
           if (system[:6] + "node") in pods:
               all_pods = True
           else:
                all_pods = False

        if "node" in system:
            if (system[:6] + "frontend") in pods:
                all_pods = True
            else:
                all_pods = False

    return all_pods

def get_all_pods(remote):
    """
    A simple lookup for all hostnames that begin with "pod" on the cobbler
    server. Cobbler allows for non-administrative actions to be token less
    so we don't pass the token to this function.

    remote -- xmlrpclib server connection to the cobbler server

    TODO -- Make it work only on pod* systems. Should be easy but should test first
    """

    return remote.find_system({"hostname":"pod*"})

def get_all_frontends(remote):
    """
    A simple lookup for all frontend systems. Used when changing passwords.
    
    remote -- xmlrpclib server connection to the cobbler server
    """

    return remote.find_system({"hostname": "pod*-frontend"})
    
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

def get_pods(pods, frontends, nodes, start, end):
    """
    Setup the pod, frontend, and node numbers that were parsed out of the
    command line argument.

    The return value is turned into a set and then back into a list to remove
    any duplicate entires we might have.

    pods -- The list of pods to add
    frontends -- The list of frontends to add
    nodes -- The list of nodes to add
    start -- Beginning of a range of pods
    end -- End of a range of pods to use
    """

    new_pods = []

    if (start < end):
        if pods is None:
            pods = []
        for pod in xrange(start, end+1):
            pods.append(str(pod))

    if not pods is None:
        for pod in pods:
            if int(pod) < 10 and len(pod) < 2:
                new_pods.append("pod0%s-frontend" % pod)
                new_pods.append("pod0%s-node" %pod)
            else:
                new_pods.append("pod%s-frontend" % pod)
                new_pods.append("pod%s-node" % pod)

    if not frontends is None:
        for frontend in frontends:
            if int(frontend) < 10 and len(frontend) < 2:
                new_pods.append("pod0%s-frontend" % frontend)
            else:
                new_pods.append("pod%s-frontend" % frontend)

    if not nodes is None:
        for node in nodes:
            if int(node) < 10 and len(node) < 2:
                new_pods.append("pod0%s-node" % node)
            else:
                new_pods.append("pod%s-node" % node)

    return list(set(new_pods))
    
def main():
    pods = []
    password_size = edu_config.PASS_SIZE

    remote, token = connect_to_cobbler(edu_config.CBLR_SERVER, edu_config.CBLR_USER, 
                                       edu_config.CBLR_PASS)

    parser = OptionParser()
    parser.add_option("--set-password", action="store_true", dest="set_password", default=False,
        help="set the password of the pod to 'eucalyptus' and can only be used entire pods")
    parser.add_option("--all-pods", action="store_true", dest="all_pods", default=False,
        help="apply the operation to all pods")
    parser.add_option("--pod", action="append", type="string", dest="pods",
        help="used to select pods")
    parser.add_option("--frontend", action="append", type="string", dest="frontends",
        help="used to select frontends")
    parser.add_option("--node", action="append", type="string", dest="nodes",
        help="used to select nodes")
    parser.add_option("--get-profiles", action="store_true", dest="get_profiles", default=False,
        help="provide a list of available profiles")
    parser.add_option("--set-profile", action="store", type="string", dest="profile",
        help="set the lists systems with the profile provided")
    parser.add_option("--start-range", action="store", type="int", dest="start_range",
        help="starts a range of pods to use")
    parser.add_option("--end-range", action="store", type="int", dest="end_range",
        help="ends a range of pods to use")
    parser.add_option("--debug", action="store_true", dest="debug", default=False,
        help="show what the program has received from the command line")

    (options, args) = parser.parse_args()

    if options.all_pods:
        pods = get_all_pods(remote)
    else:
        pods = get_pods(options.pods, options.frontends, options.nodes, 
                        options.start_range, options.end_range)

    pods.sort()

    if not options.debug:
        if options.set_password:
            set_pod_passwords(remote, pods, password_size)
        elif options.get_profiles:
            profiles = get_profiles(remote)
            print_profiles(profiles)
        elif options.profile != None:
            if not check_profile(options.profile, remote):
                print "Profile does not exist. Please check the name with --get-profiles"
                exit(2)

            if not check_pods(pods):
                print "Profiles should only be set on complete pods"
                exit(2)

            for system in pods:
                if "frontend" in system:
                    result = modify_system(system, "profile", options.profile+"-frontend",
                                            remote, token)
                else:
                    result = modify_system(system, "profile", options.profile+"-node",
                                            remote, token)

                if result == True:
                    print "Profile Changed for %s" % (system)
                else:
                    print "Error changing profile on %s" % (system)
        elif len(pods) == 0:
            parser.print_help()
        else:
            for system in pods:
                result = modify_system(system, "netboot_enabled", True, remote, token)

                if result == True:
                    print "Success for " + system    
                else:
                    print "Error for %s" % (system)
                 
                reboot_system(system, remote)    
    else:
        print ""
        print options
        print ""
        print pods

if __name__ == "__main__":
    main()
    exit
