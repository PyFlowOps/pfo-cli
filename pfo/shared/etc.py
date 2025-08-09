import os

from halo import Halo
from pfo.shared import k8s_config

# This function is used to ensure that the correct entries in the /etc/hosts file are present.
spinner = Halo(spinner="dots")

def ensure_hosts_entries():
    """
    Ensure that the specified entries are present in the /etc/hosts file.
    :param entries: A list of tuples (ip_address, hostname) to ensure in /etc/hosts.
    """
    entries = k8s_config.get("base", {}).get("hosts", [])

    hosts_file_path = '/etc/hosts'
    
    if not os.path.exists(hosts_file_path):
        raise FileNotFoundError(f"{hosts_file_path} does not exist.")
    
    with open(hosts_file_path, 'r') as file:
        current_entries = file.readlines()
    
    current_hosts = [line.strip() for line in current_entries if line.strip() and not line.startswith('#')]

    # Let's create a list of hosts that need to be added to the /etc/hosts file
    add_hosts_list = [] # This will hold the hosts that need to be added
    for entry in entries:
        if entry not in current_hosts:
            add_hosts_list.append(entry)

    if add_hosts_list:
        with open(hosts_file_path, 'a') as file:
            for host in add_hosts_list:
                file.write(f"{host}\n")
    else:
        spinner.info("No new hosts entries to add.")
        return

    spinner.succeed("Hosts entries ensured successfully.")
    return
