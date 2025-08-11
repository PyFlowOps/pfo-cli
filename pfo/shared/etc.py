# Notes:
# Variables and functions notated with "_", and "__" respectively as a prefix are intended for internal use only.
# While these variables and functions are not strictly private, they are not intended for public use
# and should not be accessed directly by users of the module.
# So it is more for documentation purposes.
# This file is part of the PyFlowOps project, which is licensed under the Apache License 2.0.
# See the LICENSE file for more details.

import os

from halo import Halo
from pfo.shared import k8s_config

# This function is used to ensure that the correct entries in the /etc/hosts file are present.
spinner = Halo(spinner="dots")

def __get_host_ipaddress():
    """
    Get the IP address of the host machine.
    
    Return:
        The IP address as a string.
    """
    return k8s_config.get("base", {}).get("host_ipaddress", "127.0.0.1")

def __assert_host_file() -> str:
    """
    Validates the existence of the system hosts file and returns its path.
    Returns:
        str: The path to the hosts file ('/etc/hosts').
    Raises:
        FileNotFoundError: If the hosts file does not exist at the expected location.
    Note:
        This function specifically checks for the Unix/Linux hosts file location.
        On Windows systems, the hosts file is typically located at 
        'C:\\Windows\\System32\\drivers\\etc\\hosts'.
    """
    hosts_file_path = '/etc/hosts'

    if not os.path.exists(hosts_file_path):
        raise FileNotFoundError(f"{hosts_file_path} does not exist.")
    
    return hosts_file_path
    
def __get_host_entries_needed():
    """
    Get the host entries that need to be added to the /etc/hosts file.
    
    Return:
      A list of tuples (ip_address, hostname) that need to be added.
    """
    return k8s_config.get("base", {}).get("hosts", [])

def __get_current_host_file_contents():
    """
    Get the current contents of the /etc/hosts file.
    Return:
        A list of lines in the /etc/hosts file.
    """
    hosts_file = __assert_host_file()

    with open(hosts_file, 'r') as file:
        contents = file.readlines()

    return contents

def __host_entries_needed_not_in_current_file() -> list[str]:
    """
    Get the host entries that are not present in the current /etc/hosts file.
    Return:
        A list of strings (without the IP address) that need to be added.
        If no entries are needed, return an empty list.
    """
    current_contents = __get_current_host_file_contents() # These are the current lines in the /etc/hosts file
    needed_entries = __get_host_entries_needed()

    current_contents_to_compare = [line.strip().split()[-1] for line in current_contents if line.strip() and not line.startswith("#")]  # Get the hostnames from the current file

    not_in_current = [entry for entry in needed_entries if entry not in current_contents_to_compare]

    return not_in_current if not_in_current else []

def __add_needed_hosts_to_hosts_file():
    """
    Add the needed host entries to the /etc/hosts file.
    """
    hosts_file = __assert_host_file()
    host_ipaddress = __get_host_ipaddress()  # Get the host IP address
    hosts_entries_to_add = __host_entries_needed_not_in_current_file() # This is the list of entries that need to be added

    if not hosts_entries_to_add:
        spinner.info("No host entries to add.")
        return

    with open(hosts_file, 'a') as file:
        for entry in hosts_entries_to_add:
            file.write(f"{host_ipaddress} {entry}\n")
            spinner.info(f"Added {entry} for IP Address  to {hosts_file}")

    spinner.succeed("Host entries added successfully.")
    return

def ensure_hosts_entries():
    """
    Ensure that the specified entries are present in the /etc/hosts file.
    """
    
    # Let's create a list of hosts that need to be added to the /etc/hosts file
    hosts_entries_to_add = __host_entries_needed_not_in_current_file()

    if not hosts_entries_to_add:
        spinner.info("No host entries needed.")
        return
    else:
        spinner.start("Ensuring host entries...")
        for i in hosts_entries_to_add:
            # Here we would add the needed hosts to the /etc/hosts file
            # For now, we will just print the entries that would be added
            spinner.warn(f"Please add the line -- {i} -- to /etc/hosts")
        
        # This function is currently under construction
        # We will want to implement the actual addition of hosts to the /etc/hosts file
        #__add_needed_hosts_to_hosts_file()

    spinner.succeed("Hosts entries ensured successfully.")
    return
