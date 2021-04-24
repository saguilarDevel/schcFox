# -*- coding: utf-8 -*-
# import socket
# import sys
# import time
# import filecmp

import json
import socket

# Microphyton imports
import pycom
import ubinascii
# Chronometers for testing
from machine import Timer
from network import Sigfox

import sender
from Entities.Fragmenter import Fragmenter
from Entities.SCHCTimer import SCHCTimer
from Entities.Sigfox import Sigfox_Entity
from Error.errors import SCHCReceiverAbortReceived
from Messages.Fragment import Fragment
from Messages.ReceiverAbort import ReceiverAbort
from Messages.SenderAbort import SenderAbort
from schc_utils import *

timer = SCHCTimer(0)

pycom.heartbeat(True)
log_info("This is the SENDER script for a Sigfox Uplink transmission experiment")
input("Press enter to continue....")

exp_dict = {'Packets/77_bytes.txt': 20,
            'Packets/150_bytes.txt': 10,
            'Packets/231_bytes.txt': 10,
            'Packets/512_bytes.txt': 10}

pycom.heartbeat(False)

for filename in exp_dict.keys():
    input("Press enter to continue with filename {}...".format(filename))
    for repetition in range(exp_dict[filename]):
        print("=====REPETITION {}=====".format(repetition))
        pycom.rgbled(0x007f00)  # green
        # Read the file to be sent.
        pycom.rgbled(0x7f7f00)  # yellow
        print("Reading file {}".format(filename))

        with open(filename, "rb") as data:
            f = data.read()
            payload = bytearray(f)

        pycom.rgbled(0x007f00)  # green

        sigfox = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ4)
        the_socket = socket.socket(socket.AF_SIGFOX, socket.SOCK_RAW)
        the_socket.setblocking(True)

        sender.start_session(socket=the_socket, message=payload, repetition=repetition, protocol=sigfox, logging=True)