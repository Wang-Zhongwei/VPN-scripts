import hashlib
import json

from envs import *
from manage_subscription import load_json, save_json


def load_json(filename) -> dict:
    try:
        with open(filename, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_json(filename, data):
    with open(filename, "w") as file:
        json.dump(data, file, indent=2)


def find_new_ip(mappings, username, device_name):
    for i in range(1, 255):
        # Generate a SHA-256 hash of the username, device name, and i
        hash_string = f"{username}{device_name}{i}"
        hash_hex = hashlib.sha256(hash_string.encode()).hexdigest()[:6]

        # Split the hash into three parts and convert from hexadecimal to decimal
        ip_parts = [int(hash_hex[j : j + 2], 16) for j in range(0, 6, 2)]

        # Avoid using 0, 1, and 255
        ip_parts = [
            2 if part in [0, 1] else 254 if part == 255 else part for part in ip_parts
        ]

        # Construct the full IP address
        full_ip = f"{SUBNET_PREFIX}.{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}"

        if full_ip not in mappings.values():
            # IP is not already assigned
            return full_ip

    # If function reaches this point, no IP was available
    raise ValueError("No available IP found")


def generate_unique_ip(username, device_name):
    # Return is_new_ip, ip

    # Load the current IP mappings
    mappings = load_json(IP_MAPPING_FILE)

    # Check if this user+device already has an assigned IP
    if username in mappings and device_name in mappings[username]:
        raise Exception(f"{username} - {device_name} already has an assigned IP")

    # No existing IP, so find a new one
    new_ip = find_new_ip(mappings, username, device_name)

    # Save the new mapping
    if username not in mappings:
        mappings[username] = {}

    mappings[username][device_name] = new_ip
    save_json(IP_MAPPING_FILE, mappings)

    # Return the newly assigned IP
    return new_ip


def get_ip(username, device):
    ip_mappings = load_json(IP_MAPPING_FILE)
    if username in ip_mappings and device in ip_mappings[username]:
        return ip_mappings[username][device]
    else:
        return generate_unique_ip(username, device)


if __name__ == "__main__":
    username = "testuser"
    device_name = "testdevice"
    print(generate_unique_ip(username, device_name))
