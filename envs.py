import os

SUBNET_PREFIX = "10"
WIREGUARD_PORT = 443 # change to 443 to avoid internet censorship
DNS_SERVER = "8.8.8.8"
KEEP_ALIVE = 30
ALLOWED_IPS = "0.0.0.0/0"

WIREGUARD_BASE = os.path.join(os.path.expanduser("~"), "wireguard")
# WIREGUARD_BASE = "/Users/wang/Documents/VPN-scripts-test-ground"
SUBSCRIPTION_DATA = WIREGUARD_BASE + "/subscriptions.json"
IP_MAPPING_FILE = WIREGUARD_BASE + "/ip_mapping.json"

WG_CONF = "/etc/wireguard/wg0.conf"
# WG_CONF = WIREGUARD_BASE + "/wg0.conf"
