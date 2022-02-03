#! /usr/bin/env python
"""
Script to fetch interface status data
"""
import json
import getpass
import sys
from pathlib import Path
import pandas as pd
from yaml import dump
from nornir import InitNornir
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.plugins.tasks.files import write_file


def create_defaults(hosts_data):
    """Creates the inventory file"""
    data_folder = Path("config/")
    path_file = data_folder / "defaults.yml"
    with open(path_file, "w") as open_file:
        hosts_file = open_file.write(hosts_data)
    return hosts_file


def get_nw_data(get_nw_task):
    """Get Interface Status Output and Write File"""
    command_var = sys.argv[1].lower()
    json_data_dir = Path("json_data/")
    hostname = get_nw_task.host.hostname
    Path(json_data_dir).mkdir(exist_ok=True)
    hostname_clean = hostname.replace(".acme.com", "")
    hostname_json = hostname_clean + ".json"
    path_file = json_data_dir / hostname_json
    port_count_data = get_nw_task.run(
        task=netmiko_send_command,
        command_string=command_var,
        use_textfsm=True,
    )
    port_count_json = json.dumps(port_count_data.result, indent=2)
    str_data_json = str(port_count_json)
    if str_data_json != '""':
        print(
            hostname + ": Writing retrieved data into JSON..." + str(path_file)
        )
        get_nw_task.run(
            task=write_file,
            content=str(port_count_json),
            filename="" + str(path_file),
        )


def main():
    """Main Function"""
    # Variables
    config_path = Path("config/")
    defaults_file = "defaults.yml"
    defaults_path = config_path / defaults_file
    json_data_dir = Path("json_data/")
    csv_data_dir = Path("csv_data/")
    Path(csv_data_dir).mkdir(exist_ok=True)
    username = input("Username: ")
    password = getpass.getpass(prompt="Password: ", stream=None)
    defaults_dict = {"username": username, "password": password}

    # Create defaults for user id
    defaults_yaml = dump(defaults_dict, default_flow_style=False)
    def_yaml_init = "---\n\n" + defaults_yaml
    create_defaults(str(def_yaml_init))

    # Initialize Nornir
    print("Connecting to devices...")
    nr = InitNornir(config_file="config/config.yml")
    nr.run(name="Retrieving Data", task=get_nw_data)
    host_list = list(nr.inventory.hosts.keys())
    for host in host_list:
        host_json = host + ".json"
        host_json_path = json_data_dir / host_json
        host_csv = host + ".csv"
        host_csv_path = csv_data_dir / host_csv
        if host_json_path.is_file():
            print(
                host
                + ": Transforming JSON data into CSV..."
                + str(host_csv_path)
            )
            json_data = pd.read_json(host_json_path)
            json_data.to_csv(host_csv_path, index=None)
    # Delete Credentials File
    Path.unlink(defaults_path)
    print("End of Script...")


if __name__ == "__main__":
    main()
