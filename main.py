import time
from datetime import datetime
from requests import Response
import json
import os
import TunnelSSH
import Helpers
import SettingsStorage
import sys



def create_tunnel(tun: dict):
    timeout_time: datetime = datetime.fromisoformat(tun["timeout_time"])
    if timeout_time <= datetime.utcnow():
        Helpers.log_that("Tunnel already not valid")
        return

    if tun["connection_type"] == Helpers.ConnectionTypeEnum.ssh_tunnel:
        TunnelSSH.create_ssh_tunnel(tun)


def destroy_tunnel(tun: dict):
    if tun["connection_type"] == Helpers.ConnectionTypeEnum.ssh_tunnel:
        TunnelSSH.destroy_ssh_tunnel(tun)


def destroy_expired_tunnels():
    for tun in SettingsStorage.datajson["tunnels"]:
        timeout_time: datetime = datetime.fromisoformat(tun["timeout_time"])
        if timeout_time <= datetime.utcnow():
            Helpers.log_that("A tunnel has expired, destroy")
            destroy_tunnel(tun)


def act_on_tunnel(tun: dict):
    Helpers.log_that(tun)
    tunnel_id: int = tun["id"]
    type: Helpers.ConnectionTypeEnum = tun["connection_type"]
    state: Helpers.ConnectionStateEnum = tun["connection_state"]
    port_to_tunnel: int = tun["port_to_tunnel"]
    timeout_time: datetime = tun["timeout_time"]
    temporaray_pubkey: str = tun["temporary_pubkey_for_agent_ssh"]
    remote_ssh_server: str = tun["remote_ssh_server"]
    remote_ssh_fingerprint: str = tun["remote_ssh_fingerprint"]
    remote_ssh_username: str = tun["remote_ssh_fingerprint"]
    reverse_port: int = tun["reverse_port"]
    remote_ssh_port: int = tun["remote_ssh_port"]
    temporary_tunnel_privkey: str = tun["temporary_tunnel_privkey"]

    if state == Helpers.ConnectionStateEnum.connected:
        # first check what should we do:
        Helpers.log_that("Requesting connection that should already be connected, ignore")
        return
    elif state == Helpers.ConnectionStateEnum.requested:
        Helpers.log_that("Requesting new connection, act upon that!")
        create_tunnel(tun)
    elif state == Helpers.ConnectionStateEnum.disconnect_requested:
        Helpers.log_that("Requesting to destroy the connection id {}".format(tunnel_id))
        destroy_tunnel(tun)


def parse_success_resp(resp: Response):
    j: dict = resp.json()
    keys = j.keys()
    if "message" in keys and len(j["message"]) > 0:
        Helpers.log_that(j["message"])

    if "tunnels_requesting_action" in keys and len(j["tunnels_requesting_action"]) > 0:
        Helpers.log_that("There are {} tunnels requesting action:".format(len(j["tunnels_requesting_action"])))
        for tun in j["tunnels_requesting_action"]:
            act_on_tunnel(tun)


def main():
    # Our small local "db" consisting of Tunnels which are active

    while True:  # Do this all the time
        try:
            # First check if this is installed, if not, send the installation data
            if not SettingsStorage.is_installed:
                resp: Response = Helpers.ReqSession.post(SettingsStorage.server_url + "/agents/agent_install",
                                               json=Helpers.get_install_json(), timeout=15)
                if resp.status_code == 200:
                    SettingsStorage.is_installed = True
                    SettingsStorage.datajson["is_installed"] = True
                    Helpers.log_that("Successfully Installed!")
                else:
                    msg = ""
                    if "detail" in resp.json().keys():
                        msg = resp.json()["detail"]
                    Helpers.log_that(
                        "Error when trying to install the agent. Code {}, with message {}".format(str(resp.status_code), msg))


            # First check if we have any Tunnel that should be disconnected TBD
            destroy_expired_tunnels()
            Helpers.remove_expired_ssh_auth_keys()
            resp: Response = Helpers.ReqSession.post(SettingsStorage.server_url + "/agents/query", json=Helpers.get_query_json(), timeout=15)
            if resp.status_code == 200:
                parse_success_resp(resp)
            else:
                msg = ""
                if "detail" in resp.json().keys():
                    msg = resp.json()["detail"]
                Helpers.log_that(
                    "Error when querying the API. Code {}, with message {}".format(str(resp.status_code), msg))
        except ValueError as e:
            Helpers.log_that("Could not process some value" + str(e.args))
        except Exception as e:
            Helpers.log_that("Could not connect to server " + str(e.args))

        datafile = open(os.path.join(sys.path[0], "data.json"), "w")
        json.dump(SettingsStorage.datajson, datafile)
        datafile.close()
        time.sleep(SettingsStorage.interval_seconds)


if __name__ == "__main__":
    # execute only if run as a script
    main()
