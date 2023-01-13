import configparser
import requests
import re

config = configparser.ConfigParser()
config.read("config.ini")


def get(path: str) -> dict:
    headers = {'x-auth-token': config['librenms']['token']}
    return requests.get(config['librenms']['url'] + path, headers=headers).json()


def get_switches() -> list[dict]:
    devices = get('/api/v0/devices')['devices']
    devices = filter(lambda device: 'sw' in device['hostname'], devices)
    return devices


def get_ports(hostname: str) -> list[dict]:
    ports = get(f'/api/v0/devices/{hostname}/ports?columns=ifName,ifAlias')['ports']
    ports = filter(lambda port: re.match('^(gei|Gigabit).*', port['ifName']), ports)
    return ports
