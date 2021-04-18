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
import getpass
import sys

user_name = getpass.getuser()
ssh_known_hosts_path = os.path.expanduser("~") + "/.ssh/known_hosts"
ssh_authorized_keys_path = os.path.expanduser("~") + "/.ssh/authorized_keys"

# Create the files if do not exist
open(ssh_known_hosts_path, "a").close()
open(ssh_authorized_keys_path, "a").close()


datafile = open(os.path.join(sys.path[0], "data.json"), "r")


# DATAFILE .................................................
try:
    datajson = json.load(datafile)
except ValueError as e:
    Helpers.log_that("No configuration file found, exiting")
    exit(1)

try:
    token = datajson["token"]
    server_protocol = datajson["server_protocol"]
    server_domain_ip = datajson["server_domain_ip"]
    server_port = datajson["server_port"]
    is_installed = datajson["is_installed"]
    interval_seconds = datajson["interval_seconds"]
    # TBD certificate?
    datafile.close()
    server_url = server_protocol + server_domain_ip + ":" + str(server_port)
except ValueError as e:
    Helpers.log_that("The configuration file is not valid, exiting")
    exit(1)
# ...........................................................
