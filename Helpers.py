
import time

import requests
from typing import List, Optional
from datetime import datetime
import enum
from pydantic import BaseModel, ValidationError, validator, Field, Json
from requests import Response
import json
import subprocess
import os
import signal
import tempfile
import TunnelSSH
import SettingsStorage
import re
import psutil

# Enums -----------------------------------------------------

class ConnectionTypeEnum(enum.IntEnum):
    """
        Types of connections:
        SSH Tunnel = 0
        WebRTC = 1 (Not implemented yet)
        """
    ssh_tunnel = 0
    webrtc = 1  # Reserved TODO


class ConnectionStateEnum(enum.IntEnum):
    """
        Connection states:
        Disconnected - Finished and archived = 0
        Requested = 1
        Agent responded, Connection in progress = 2
        Disconnect Has been requested = 3
        """
    disconnected = 0
    requested = 1
    connected = 2  # this means that the agent acknowledges connection
    disconnect_requested = 3  # this means that agent is requested to close the connectio

# Create JSON
def get_query_json():
    return {
        "token": SettingsStorage.token,
        "last_cpu_percent": psutil.cpu_percent(),
        "last_memory_percent": psutil.virtual_memory().percent
    }


def get_tunnel_changed_json(tunnel_id: int, new_state: ConnectionStateEnum):
    return {
        "token": SettingsStorage.token,
        "tunnel_id": tunnel_id,
        "new_state": int(new_state)
    }

def get_install_json():
    return {
        "token": SettingsStorage.token,
        "agent_user_name": SettingsStorage.user_name
    }

# Log
def log_that(message: str):
    print(message)

# Known_hosts management --------------------------------------------------

def remove_known_host(fingerprint: str):
    f = open(SettingsStorage.ssh_known_hosts_path, mode="r")
    lines = f.readlines()

    fingerprint_found_flag = False

    newlines = []

    # Filter out all the appearances of that machine ID we are dealing with
    for l in lines:
        if fingerprint in l:
            fingerprint_found_flag = True
        else:
            newlines.append(l)

    if fingerprint_found_flag:
        # Ok now just create the file
        f = open(SettingsStorage.ssh_known_hosts_path, mode="w")
        for l in newlines:
            f.write(l)

        f.close()


def add_known_host(domain_ip: str, port: int, fingerprint: str):
    # remove if there is fingerprint:
    remove_known_host(fingerprint)

    # create file if does not exist
    f = open(SettingsStorage.ssh_known_hosts_path, mode="a")

    #f.write("\n")
    auth_key = "[{}]:{} {}".format(domain_ip, port, fingerprint)

    f.write(auth_key)
    f.close()

# Auth keys manager

def remove_expired_ssh_auth_keys():

    f = open(SettingsStorage.ssh_authorized_keys_path, mode="r")
    lines = f.readlines()

    id_found_flag = False

    newlines = []

    # Filter out all the appearances of that machine ID we are dealing with
    for l in lines:
        matchobj = re.match(r'timeout:(.*)$', l)
        if matchobj:
            to = datetime.fromisoformat(matchobj.group(1))
            if to < datetime.utcnow():
                id_found_flag = True
        else:
            newlines.append(l)

    if id_found_flag:
        #Ok now just create the file
        f = open(SettingsStorage.ssh_authorized_keys_path, mode="w")
        for l in newlines:
            f.write(l)

        f.close()


def remove_particular_ssh_auth_key(pubkey: str):

    f = open(SettingsStorage.ssh_authorized_keys_path, mode="r")
    lines = f.readlines()

    id_found_flag = False

    newlines = []

    # Filter out all the appearances of that machine ID we are dealing with
    for l in lines:
        if pubkey in l:
            id_found_flag = True
        else:
            newlines.append(l)

    if id_found_flag:
        #Ok now just create the file
        f = open(SettingsStorage.ssh_authorized_keys_path, mode="w")
        for l in newlines:
            f.write(l)

        f.close()


def set_ssh_auth_key(timeout: datetime, pubkey: str):

    # create the comment for auth_keys identification
    comment = "timeout:{0}".format(timeout.isoformat())

    # create file if does not exist
    f = open(SettingsStorage.ssh_authorized_keys_path, mode="a")

    auth_key = "{0} {1}".format(pubkey, comment)

    f.write("\n")
    f.write(auth_key)
    f.close()