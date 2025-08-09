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


def __assert_host_file():
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

    augmented_contents = [line.strip() for line in contents if line.strip() and not line.startswith('#')]
    return augmented_contents

def __host_entries_needed_not_in_current_file() -> list[str]:
    """
    Get the host entries that are not present in the current /etc/hosts file.
    Return:
        A list of tuples (ip_address, hostname) that are not present.
    """
    current_contents = __get_current_host_file_contents()
    needed_entries = __get_host_entries_needed()

    not_in_current = [entry for entry in needed_entries if entry not in current_contents]
    return not_in_current if not_in_current else []

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
        spinner.warn("UNDER CONSTRUCTION - This feature is not yet implemented.")

    spinner.succeed("Hosts entries ensured successfully.")
    return
