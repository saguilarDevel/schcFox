# -*- coding: utf-8 -*-
# import socket
# import sys
# import time
# import filecmp

# Microphyton imports
import pycom
import binascii

from Entities.SCHCSender import SCHCSender
from config import exp_dict

pycom.heartbeat(True)


print("This is the SENDER script for a Sigfox Uplink transmission experiment")
input("Press enter to continue....")

pycom.heartbeat(False)


for filename in exp_dict.keys():
    input("Press enter to continue with filename {}...".format(filename))
    for repetition in range(exp_dict[filename]):

        pycom.rgbled(0x007f00)  # green
        # Read the file to be sent.
        pycom.rgbled(0x7f7f00)  # yellow

        with open(filename, "rb") as data:
            f = data.read()
            payload = bytearray(f)

        pycom.rgbled(0x007f00)  # green

        filename_stats = "stats/stats_{}_{}.json".format(
            filename[filename.find('/') + 1:filename.find('_')], repetition)

        sender = SCHCSender()
        sender.set_logging(filename="logs.log", json_file=filename_stats)
        sender.set_session("ACK ON ERROR", payload)

        sender.LOGGER.info("=====REPETITION {}=====".format(repetition))

        if repetition == 0:
            clean_msg = str(binascii.hexlify("CLEAN_ALL"))[2:-1]
        else:
            clean_msg = str(binascii.hexlify("CLEAN"))[2:-1]

        sender.LOGGER.debug("Sending {} message".format(binascii.unhexlify(clean_msg)))

        sender.send(binascii.unhexlify("{}a{}".format(sender.HEADER_BYTES, clean_msg)))

        # Wait for the cleaning function to end
        sender.TIMER.wait(30)
        sender.set_delay(20)
        sender.start_session()
