import time

import requests
from typing import List, Optional
from datetime import datetime
import enum
from pydantic import BaseModel, ValidationError, validator, Field, Json
from requests import Response
import json
import subprocess


def log_that(message: str):
    print(message)


datafile = open("data.json", "r")

# DATAFILE .................................................
try:
    datajson = json.load(datafile)
except ValueError as e:
    log_that("No configuration file found, exiting")
    exit(1)

try:
    token = datajson["token"]
    server_protocol = datajson["server_protocol"]
    server_domain_ip = datajson["server_domain_ip"]
    server_port = datajson["server_port"]
except ValueError as e:
    log_that("The configuration file is not valid, exiting")
    exit(1)
# ...........................................................
datafile.close()

server_url = server_protocol + server_domain_ip + ":" + str(server_port) + "/agents/query/" + token


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


def create_ssh_tunnel(tun: dict):
    port_to_tunnel: int = tun["port_to_tunnel"]
    timeout_time: datetime = tun["timeout_time"]
    temporaray_pubkey: str = tun["temporary_pubkey_for_agent_ssh"]
    domain_ip: str = tun["domain_ip"]
    temporary_tunnel_privkey: str = tun["temporary_tunnel_privkey"]
    reverse_port: int = tun["reverse_port"]
    remote_ssh_port: int = tun["remote_ssh_port"]

    if len(domain_ip) < 1:
        domain_ip = server_domain_ip

    for t in datajson["tunnels"]:
        if t["id"] == tun["id"]:
            newone = False


    log_that("Trying to create a tunnel to port {} with a reverse {} on {} ...".format(port_to_tunnel, reverse_port, domain_ip))

   # datajson["tunnels"].append(tun)
   # log_that("Appending tunnel to ")





def destroy_ssh_tunnel(id: int):
    pass


def create_tunnel(tun: dict):
    timeout_time: datetime = datetime.fromisoformat(tun["timeout_time"])
    if timeout_time <= datetime.utcnow():
        log_that("Tunnel already not valid")
        #return

    if tun["connection_type"] == ConnectionTypeEnum.ssh_tunnel:
        create_ssh_tunnel(tun)


def destroy_tunnel(id: int):
    pass


def parse_success_resp(resp: Response):
    j: dict = resp.json()
    keys = j.keys()
    if "message" in keys and len(j["message"]) > 0:
        log_that(j["message"])

    if "tunnels_requesting_action" in keys and len(j["tunnels_requesting_action"]) > 0:
        log_that("There are {} tunnels requesting action:".format(len(j["tunnels_requesting_action"])))
        for tun in j["tunnels_requesting_action"]:
            act_on_tunnel(tun)


def act_on_tunnel(tun: dict):
    log_that(tun)
    type: ConnectionTypeEnum = tun["connection_type"]
    state: ConnectionStateEnum = tun["connection_state"]
    port_to_tunnel: int = tun["port_to_tunnel"]
    timeout_time: datetime = tun["timeout_time"]
    temporaray_pubkey: str = tun["temporary_pubkey_for_agent_ssh"]
    domain_ip: str = tun["domain_ip"]
    temporary_tunnel_privkey: str = tun["temporary_tunnel_privkey"]
    reverse_port: int = tun["reverse_port"]
    remote_ssh_port: int = tun["remote_ssh_port"]

    remote_ssh_server: str = tun["remote_ssh_server"]
    if len(remote_ssh_server) < 1:
        remote_ssh_server = server_domain_ip
    if state == ConnectionStateEnum.connected:
        # first check what should we do:
        log_that("Requesting connection that should already be connected, ignore")
        return
    elif state == ConnectionStateEnum.requested:
        log_that("Requesting new connection, act upon that!")
        create_tunnel(tun)


def main():
    # Our small local "db" consisting of Tunnels which are active
    global datajson

    try:
        resp: Response = requests.get(server_url)
        if resp.status_code == 200:
            parse_success_resp(resp)
    except ValueError as e:
        log_that("Could not connect to server")

    datafile = open("data.json", "w")
    json.dump(datajson, datafile)
    datafile.close()


if __name__ == "__main__":
    # execute only if run as a script
    main()
