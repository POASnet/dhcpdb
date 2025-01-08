import configparser
import requests
import re
from urllib import parse

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
    ports = filter(lambda port: re.match('^(gei|Gigabit|GE).*', port['ifName']), ports)
    return ports

def get_location(hostname: str) -> str:
    location = get(f'/api/v0/devices/{hostname}')['devices'][0]['location']
    return location

def get_ifalias(hostname: str, ifname: str) -> str:
    ifname = parse.quote_plus(ifname)
    port = get(f'/api/v0/devices/{hostname}/ports/{ifname}?columns=ifName,ifAlias')['port']
    ifalias = port['ifAlias'].startswith(port['ifName']) and port['ifAlias'].split(' ', 1)[1] or port['ifAlias']
    return ifalias
