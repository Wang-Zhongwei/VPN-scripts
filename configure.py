import os
import subprocess

from envs import *
from manage_ip import generate_unique_ip, get_ip
from manage_subscription import (remove_user_devices_from_wg,
                                 update_subscription)


def get_key_dir(username, device_name):
    return WIREGUARD_BASE + "/users/" + username + "/" + device_name


def configure_server(username, device_name):
    key_dir = get_key_dir(username, device_name)
    os.makedirs(key_dir, exist_ok=True)
    os.chdir(key_dir)

    # Extract the generated public key
    with open("public.key", "r") as file:
        client_public_key = file.read().strip()

    # Assign a unique IP address
    try:
        client_ip = generate_unique_ip(username, device_name)
    except Exception:
        print(f"Skip server configuration for {username} on {device_name}")
        return

    # Append the necessary information to the WireGuard configuration file
    peer_config = f"\n# {username} - {device_name}\n[Peer]\nAllowedIPs = {client_ip}/32\nPublicKey = {client_public_key}\n"
    subprocess.run(f"echo '{peer_config}' | sudo tee -a {WG_CONF}", shell=True)
    subprocess.run(["sudo", "systemctl", "restart", "wg-quick@wg0.service"], check=True)

    print(f"Server configuration for {username} on {device_name} created successfully.")


def configure_client(username, device_name):
    key_dir = get_key_dir(username, device_name)
    os.makedirs(key_dir, exist_ok=True)

    client_conf = f"{key_dir}/client.conf"

    # get private key from client
    os.chdir(key_dir)
    with open("private.key", "r") as file:
        client_private_key = file.read().strip()

    # Prepare the [Interface] section to prepend to the client configuration
    content = f"[Interface]\nPrivateKey = {client_private_key}\n"
    client_ip = get_ip(username, device_name)
    content += f"Address = {client_ip}/32\nDNS = {DNS_SERVER}\n"

    # Write the updated configuration back to the file
    with open(client_conf, "w") as file:
        file.write(content)

    print(f"Client configuration for {username} on {device_name} created successfully.")


def generate_keys(username, device_name):
    key_dir = get_key_dir(username, device_name)
    os.makedirs(key_dir, exist_ok=True)
    os.chdir(key_dir)
    os.umask(0o077)
    subprocess.run("wg genkey | tee private.key | wg pubkey > public.key", shell=True)
    print(f"Keys for {username} on {device_name} created successfully.")


def add_user_devices(username, devices):
    for device in devices:
        key_dir = get_key_dir(username, device)
        # configure keys if user-device not existed before
        if not os.path.exists(key_dir):
            generate_keys(username, device)

        # configure server
        configure_server(username, device)

        # configure client
        configure_client(username, device)

        # update subscription
        update_subscription(username, expiry_date)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Configure WireGuard tunnels for a user's devices"
    )

    parser.add_argument("username", help="Username")
    parser.add_argument("devices", nargs="+", help="Device names")
    parser.add_argument("--expiry_date", help="Expiry date of the subscription")
    parser.add_argument(
        "-rm", "--remove", help="Remove user from nodes", action="store_true"
    )

    args = parser.parse_args()
    username = args.username
    devices = args.devices
    expiry_date = args.expiry_date
    to_remove = args.remove


    if to_remove:
        remove_user_devices_from_wg(username, devices)
    else:
        add_user_devices(username, devices)
