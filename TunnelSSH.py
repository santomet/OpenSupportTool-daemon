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
import Helpers
import SettingsStorage

def create_ssh_tunnel(tun: dict):
    tunnel_id: int = tun["id"]
    port_to_tunnel: int = tun["port_to_tunnel"]
    timeout_time: datetime = tun["timeout_time"]
    temporaray_pubkey_to_accept: str = tun["temporary_pubkey_for_agent_ssh"]
    remote_ssh_server: str = tun["remote_ssh_server"]
    reverse_port: int = tun["reverse_port"]
    remote_ssh_port: int = tun["remote_ssh_port"]
    remote_ssh_fingerprint: str = tun["remote_ssh_fingerprint"]
    temporary_tunnel_privkey: str = tun["temporary_tunnel_privkey"]

    if len(remote_ssh_server) < 1:
        remote_ssh_server = SettingsStorage.server_domain_ip

    for t in SettingsStorage.datajson["tunnels"]:
        if t["id"] == tun["id"]:
            Helpers.log_that("The tunnel id {} is already running, this should not happened!".format(t["id"]))
            return

    # Fist of all, we need to add the server SSH pubkey to known_hosts
    Helpers.add_known_host(remote_ssh_server, remote_ssh_port, remote_ssh_fingerprint)

    # Ok now try to connect, the SSH server should have been prepared for a long time
    Helpers.log_that("Trying to create a tunnel to port {} with a reverse {} on {} ...".format(port_to_tunnel, reverse_port, remote_ssh_server))

    tf = tempfile.NamedTemporaryFile(mode="w", delete=False)
    tf.write(temporary_tunnel_privkey)
    tf.close()

    tunnel_process = subprocess.Popen(
        ["ssh", "-T", "-o ServerAliveInterval 30", "-o ServerAliveCountMax 3", "-o PasswordAuthentication=no",
         "-R" + str(reverse_port) + ":localhost:" + str(port_to_tunnel),
         "-i" + tf.name,
         remote_ssh_server,
         "-p" + str(remote_ssh_port)]
    )

    time.sleep(5)
    os.remove(tf.name)
    # if the process is alive, there is no poll. After 5 seconds this should only mean that the tunnel is a success
    if not tunnel_process.poll():
        Helpers.log_that("TUNNEL SUCCESSFULLY CREATED")
        tun["pid"] = tunnel_process.pid
        tun["connection_state"] = Helpers.ConnectionStateEnum.connected
        # Adding the tunnel so we can remember
        SettingsStorage.datajson["tunnels"].append(tun)
        # Send the confirmation to the API:
        resp: Response = Helpers.ReqSession.post(SettingsStorage.server_url + "/agents/tunnel_changed", json=Helpers.get_tunnel_changed_json(tunnel_id, Helpers.ConnectionStateEnum.connected))
        if resp.status_code == 200:
            Helpers.log_that("API now knows that the tunnel is connected")
        else:
            mes = ""
            if "detail" in resp.json().keys():
                mes = resp.json()["detail"]
            Helpers.log_that("ERROR: The API response for tunnel_connected {} with a message {}".format(resp.status_code, mes))

        # We can save the public key of a support personnel if any
        if len(temporaray_pubkey_to_accept) > 0:
            Helpers.set_ssh_auth_key(timeout_time, temporaray_pubkey_to_accept)
            Helpers.log_that("Auth key is set!!")

    else:
        Helpers.log_that("TUNNEL COULD NOT BE CREATED")





    #os.kill(tunnel_process.pid, signal.SIGTERM)

    # datajson["tunnels"].append(tun)
    # log_that("Appending tunnel to ")


def destroy_ssh_tunnel(tun: dict):
    # we want the tunnel from the storage:
    for t in SettingsStorage.datajson["tunnels"]:
        if t["id"] == tun["id"]:
            tun = t
            break

    Helpers.log_that("Trying to kill Tunnel id {}".format(tun["id"]))
    try:
        os.kill(int(tun["pid"]), signal.SIGTERM)
    except OSError as e:
            Helpers.log_that("Process not there")
    except KeyError as e:
            Helpers.log_that("Process ID not in the structure :O")

    SettingsStorage.datajson["tunnels"].remove(tun)
    resp: Response = Helpers.ReqSession.post(
        SettingsStorage.server_url + "/agents/tunnel_changed", json=Helpers.get_tunnel_changed_json(tun["id"], Helpers.ConnectionStateEnum.disconnected))

    if resp.status_code == 200:
        Helpers.log_that("API now knows that the tunnel is disconnected")
    else:
        mes = ""
        if "detail" in resp.json().keys():
            mes = resp.json()["detail"]
        Helpers.log_that(
            "ERROR: The API response for tunnel_connected {} with a message {}".format(resp.status_code, mes))