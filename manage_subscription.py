import datetime
import json
import re
import subprocess

from envs import *


def load_json(filename):
    try:
        with open(filename, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_json(filename, data):
    with open(filename, "w") as file:
        json.dump(data, file, indent=2)


def user_is_expired(username, subscriptions):
    today = datetime.date.today()
    if username not in subscriptions:
        return False

    expiry_date = subscriptions[username]
    expiry_date_obj = datetime.datetime.strptime(expiry_date, "%Y-%m-%d").date()
    return today > expiry_date_obj


def remove_expired_users():
    subscriptions = load_json(SUBSCRIPTION_DATA)
    ip_mappings = load_json(IP_MAPPING_FILE)

    restart_wireguard = False
    for user, _ in list(subscriptions.items()):
        if user_is_expired(user, subscriptions):
            # Remove expired user from ip_mappings
            if user in ip_mappings:
                ip_mappings.pop(user)
            remove_user_devices_from_wg(user)
            restart_wireguard = True

    # Save updated files
    save_json(IP_MAPPING_FILE, ip_mappings)

    if restart_wireguard:
        # Reload WireGuard configuration to apply changes
        subprocess.run(
            ["sudo", "systemctl", "restart", "wg-quick@wg0.service"], check=True
        )


def remove_user_devices_from_wg(username, devices=[], block_width=5):
    """remove user devices from wg0.conf

    Args:
        username (str): username
        devices (list, optional): list of user's devices. Defaults to [] means remove all devices
        block_width (int, optional): block_width of user's device content in the wg0.conf. Defaults to 5.
    """
    try:
        # Find and remove the section corresponding to the expired user
        new_lines = []

        if devices:
            devices_pattern = "|".join(map(re.escape, devices))
            peer_pattern = re.compile(
                r"#\s*" + re.escape(username) + r"\s*-\s*(" + devices_pattern + ")"
            )
        else:
            # remove all devices
            peer_pattern = re.compile(r"#\s*" + re.escape(username))

        # Read the current WireGuard configuration
        command = ['sudo', 'cat', WG_CONF]
        result = subprocess.run(command, capture_output=True, text=True)
        lines = result.stdout.split('\n')

        i, num_lines = 0, len(lines)
        while i < num_lines:
            if re.search(peer_pattern, lines[i]):
                i += block_width
                continue
            new_lines.append(lines[i])
            i += 1

        # Write the updated configuration back to the file
        new_config = '\n'.join(new_lines)
        command = ['sudo', 'bash', '-c', f'echo "{new_config}" > {WG_CONF}']
        subprocess.run(command, check=True)

        print(f"{username}'s {' '.join(devices)} removed from WireGuard configuration.")

    except Exception as e:
        print(f"Failed to remove user from WireGuard configuration: {e}")


def update_subscription(username, expiry_date):
    subscriptions = load_json(SUBSCRIPTION_DATA)
    subscriptions[username] = expiry_date
    save_json(SUBSCRIPTION_DATA, subscriptions)
    print(f"Subscription for {username} updated to {expiry_date}.")


if __name__ == "__main__":
    remove_expired_users()
