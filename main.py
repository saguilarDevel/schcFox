# -*- coding: utf-8 -*-
# import socket
# import sys
# import time
# import filecmp

# Microphyton imports
import pycom
import ubinascii

from Entities.SCHCSender import SCHCSender
from config import exp_dict
from schc_utils import *

pycom.heartbeat(True)
log_info("This is the SENDER script for a Sigfox Uplink transmission experiment")
input("Press enter to continue....")

pycom.heartbeat(False)

init_logging("logs.log")

for filename in exp_dict.keys():
    input("Press enter to continue with filename {}...".format(filename))
    for repetition in range(exp_dict[filename]):
        log_info("=====REPETITION {}=====".format(repetition))
        pycom.rgbled(0x007f00)  # green
        # Read the file to be sent.
        pycom.rgbled(0x7f7f00)  # yellow
        log_debug("Reading file {}".format(filename))

        with open(filename, "rb") as data:
            f = data.read()
            payload = bytearray(f)

        pycom.rgbled(0x007f00)  # green

        filename_stats = "stats/stats_{}_{}.json".format(
            filename[filename.find('_') + 1:filename.find('_')], repetition)

        sender = SCHCSender()
        sender.set_logging(filename_stats)
        sender.set_session("ACK ON ERROR", payload)

        log_debug("Sending CLEAN message")
        if repetition == 0:
            clean_msg = str(ubinascii.hexlify("CLEAN_ALL"))[2:-1]
        else:
            clean_msg = str(ubinascii.hexlify("CLEAN"))[2:-1]

        sender.send(ubinascii.unhexlify("{}a{}".format(sender.HEADER_BYTES, clean_msg)))

        # Wait for the cleaning function to end
        sender.TIMER.wait(30)
        sender.set_delay(20)
        sender.start_session()
