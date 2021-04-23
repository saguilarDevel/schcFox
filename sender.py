# -*- coding: utf-8 -*-
import getopt
import socket
import sys
import time
import filecmp
import requests
import json

from network import Sigfox

from Entities.Fragmenter import Fragmenter
from Entities.Sigfox import Sigfox_Entity
from Messages.Fragment import Fragment
from schc_utils import print_and_log


def start_session(payload, socket, chronometer=None, laps=None):
    # stats variables (for testing)
    current_fragment = {}
    fragments_info_array = []
    tx_status_ok = False

    # Initialize variables.
    total_size = len(payload)
    current_size = 0
    percent = 0
    ack = None
    last_ack = None
    i = 0
    current_window = 0
    header_bytes = 1 if total_size <= 300 else 2

    profile_uplink = Sigfox_Entity("UPLINK", "ACK ON ERROR", header_bytes)
    profile_downlink = Sigfox_Entity("DOWNLINK", "NO ACK", header_bytes)

    # Start Time
    chronometer.start()

    # Fragment the file.
    fragmenter = Fragmenter(profile_uplink, payload)
    fragment_list = fragmenter.fragment()

    # read elapsed time without stopping
    fragmentation_time = chronometer.read()
    print_and_log("fragmentation time -> {}".format(fragmentation_time), 'DEBUG')

    # The fragment sender MUST initialize the Attempts counter to 0 for that Rule ID and DTag value pair
    # (a whole SCHC packet)
    attempts = 0
    retransmitting = False
    fragment = None

    start_sending_time = chronometer.read()

    while i < len(fragment_list) and not tx_status_ok:
        current_fragment = {}
        laps.append(chronometer.read())
        print_and_log("laps - > {}".format(laps), "DEBUG")

        if not retransmitting:
            pycom.rgbled(0x7f7f00)  # yellow
            # A fragment has the format "fragment = [header, payload]".
            data = bytes(fragment_list[i][0] + fragment_list[i][1])
            # Convert to a Fragment class for easier manipulation.
            fragment = Fragment(profile_uplink, fragment_list[i])

            print_and_log("--------------------------\n" +
                          "{}th fragment:\n".format(i) +
                          "RuleID:{}, DTAG:{}, WINDOW:{}, FCN:{}\n".format(fragment.header.RULE_ID,
                                                                           fragment.header.DTAG,
                                                                           fragment.header.W,
                                                                           fragment.header.FCN) +
                          "SCHC Fragment: {}\n".format(data) +
                          "SCHC Fragment Payload: {}\n".format(fragment_list[i][1]),
                          "DEBUG")

            current_size += len(fragment_list[i][1])
            if total_size != 0:
                percent = round(float(current_size) / float(total_size) * 100, 2)
            wait_receive = False

            # Send the data.
            # If a fragment is an All-0 or an All-1:
            if fragment.is_all_0() or fragment.is_all_1():
                ack = None
                print_and_log('Preparing for sending All-0 or All-1', 'DEBUG')
                try:
                    ack = send_sigfox(socket,
                                      fragment,
                                      data,
                                      profile_uplink.RETRANSMISSION_TIMER_VALUE,
                                      profile_uplink,
                                      True,
                                      profile_downlink.MTU)
                except SCHCReceiverAbortReceived:
                    print('SCHC Receiver Abort Message Received')
                    break
            else:
                send_sigfox(socket,
                            fragment,
                            data,
                            profile_uplink.RETRANSMISSION_TIMER_VALUE,
                            False)

            pycom.rgbled(0x7f7f00)  # yellow

        if retransmitting or fragment.is_all_0() or fragment.is_all_1():
            # Reset ack-req attempts
            attempts = 0

            while attempts < profile_uplink.MAX_ACK_REQUESTS:
                print_and_log("attempts:{}".format(attempts), "DEBUG")

            # No ACK was received for the intermediate window
            if fragment.is_all_0() and ack is None:
                print('No ACK received, continue sending fragments')
                print("Proceeding to next window")
                resent = False
                retransmitting = False
                current_window += 1
                break
                # TODO: add logic if fragment are lost.

            elif ack is not None:
                print_and_log("ACK received. {}".format(ack), "INFO")
                index = profile_uplink.RULE_ID_SIZE + profile_uplink.T + profile_uplink.M + 1
                print_and_log('index:{}'.format(index), "DEBUG")
                bitmap = ack[index:index + profile_uplink.BITMAP_SIZE]
                ack_window = int(ack[profile_uplink.RULE_ID_SIZE + profile_uplink.T:index - 1], 2)
                print_and_log("ACK_WINDOW " + str(ack_window), "DEBUG")
                print_and_log("ack -> {}".format(ack), "DEBUG")
                print_and_log("bitmap -> {}".format(bitmap), "DEBUG")

                index_c = index - 1
                c = ack[index_c]
                print_and_log("c -> {}".format(c), "DEBUG")

                # If the C bit of the ACK is set to 1 and the fragment is an All-1 then we're done.
                if c == '1' and fragment.is_all_1():
                    if ack_window == current_window:
                        print_and_log("Last ACK received: Fragments reassembled successfully. End of transmission.",
                                      "INFO")
                        tx_status_ok = True
                        break
                    else:
                        print_and_log("Last ACK window {} does not correspond to last window {}".format(ack_window,
                                                                                                        current_window),
                                      "ERROR")
                        senderAbort = SenderAbort(profile_uplink,
                                                  fragment.header.RULE_ID,
                                                  fragment.header.DTAG,
                                                  fragment.header.W)
                        print_and_log("Generated Sender-Abort", "INFO")
                        print_and_log("--- senderAbort:{}".format(senderAbort.to_string()), "DEBUG")
                        print_and_log("--- senderAbort:{}".format(senderAbort.to_bytes()), "DEBUG")
                        send_sigfox(socket,
                                    senderAbort,
                                    bytes(senderAbort.to_bytes()),
                                    profile_uplink.RETRANSMISSION_TIMER_VALUE,
                                    profile_uplink,
                                    False)
                        break
                elif c == '1' and fragment.is_all_0():
                    print_and_log("You shouldn't be here. (All-0 with C = 1)", "WARNING")
                    senderAbort = SenderAbort(profile_uplink,
                                              fragment.header.RULE_ID,
                                              fragment.header.DTAG,
                                              fragment.header.W)
                    print_and_log("Generated Sender-Abort", "INFO")
                    print_and_log("--- senderAbort:{}".format(senderAbort.to_string()), "DEBUG")
                    print_and_log("--- senderAbort:{}".format(senderAbort.to_bytes()), "DEBUG")
                    send_sigfox(the_socket,
                                senderAbort,
                                bytes(senderAbort.to_bytes()),
                                profile_uplink.RETRANSMISSION_TIMER_VALUE,
                                profile_uplink,
                                False,
                                profile_downlink.MTU,
                                True)
                    break

                # If the C bit has not been set:
                elif c == '0':
                    print_and_log('c bit = 0, resent = False', 'DEBUG')
                    resent = False

                    for j in range(len(bitmap)):
                        # If the j-th bit of the bitmap is 0, then the j-th fragment was lost.
                        if bitmap[j] == '0':
                            print_and_log("The " + str(j) + "th of window " + str(ack_window) +
                                          " (" + str((2 ** profile_uplink.N - 1) * ack_window + j) +
                                          " / " + str(len(fragment_list)) + ") fragment was lost! Sending again...",
                                          "INFO")

                            # Try sending again the lost fragment.
                            try:
                                print_and_log("{}".format((2 ** profile_uplink.N - 1) * ack_window + j), "DEBUG")
                                data_to_be_resent = bytes(
                                    fragment_list[(2 ** profile_uplink.N - 1) * ack_window + j][0] +
                                    fragment_list[(2 ** profile_uplink.N - 1) * ack_window + j][1])

                                fragment_to_be_resent = Fragment(profile_uplink, fragment_list[
                                    (2 ** profile_uplink.N - 1) * ack_window + j])

                                print_and_log(
                                    "RuleID:{}, WINDOW:{}, FCN:{}".format(fragment_to_be_resent.header.RULE_ID,
                                                                          fragment_to_be_resent.header.W,
                                                                          fragment_to_be_resent.header.FCN), "DEBUG")
                                print_and_log("data_to_be_resent:{}".format(data_to_be_resent), "DEBUG")

                                if fragment_to_be_resent.is_all_1():
                                    attempts += 1
                                    print_and_log('fragment All-1 found', "DEBUG")
                                    print_and_log("request last ACK, sending All-1 again. attempts:{}".format(attempts),
                                                  "INFO")
                                    retransmitting = True
                                    last_ack = None
                                    ack = None
                                    try:
                                        last_ack = send_sigfox(the_socket,
                                                               fragment_to_be_resent,
                                                               data_to_be_resent,
                                                               profile_uplink.RETRANSMISSION_TIMER_VALUE,
                                                               profile_uplink,
                                                               True)
                                    except SCHCReceiverAbortReceived:
                                        print_and_log('SCHC Receiver Abort Message Received', "ERROR")
                                        break
                                    break
                                send_sigfox(the_socket,
                                            fragment_to_be_resent,
                                            data_to_be_resent,
                                            profile_uplink.RETRANSMISSION_TIMER_VALUE,
                                            profile_uplink,
                                            False)
                                resent = True

                            # If the fragment wasn't found, it means we're at the last window with no fragment
                            # to be resent. The last fragment received is an All-1.
                            except IndexError:
                                print_and_log("No fragment found.", "DEBUG")
                                pycom.rgbled(0x7f0000)  # red
                                resent = False
                                retransmitting = False
                                attempts += 1
                                print_and_log("IndexError, request last ACK, sending All-1 again. "
                                              "attempts:{}".format(attempts), "INFO")
                                print_and_log(
                                    "RuleID:{}, WINDOW:{}, FCN:{}".format(fragment.header.RULE_ID, fragment.header.W,
                                                                          fragment.header.FCN), "DEBUG")
                                print_and_log("resend and fragment.is_all_1()", "DEBUG")
                                ack = None
                                last_ack = None
                                try:
                                    last_ack = send_sigfox(the_socket,
                                                           fragment,
                                                           data,
                                                           profile_uplink.RETRANSMISSION_TIMER_VALUE,
                                                           profile_uplink,
                                                           True)
                                except SCHCReceiverAbortReceived:
                                    print_and_log('SCHC Receiver Abort Message Received', "ERROR")
                                    break
                                break

                    # After sending the lost fragments, if the last received fragment was an All-1 we need to receive
                    # the last ACK.
                    if fragment.is_all_1() or fragment_to_be_resent.is_all_1():
                        # Set the timeout for RETRANSMISSION_TIMER_VALUE
                        socket.settimeout(profile_uplink.RETRANSMISSION_TIMER_VALUE)
                        if last_ack:
                            print_and_log('last_ack', "INFO")
                            c = last_ack[index_c]

                            # If the C bit is set to 1 then we're done.
                            if c == '1':
                                print_and_log("{}".format(ack_window), "DEBUG")
                                print_and_log("{}".format(current_window), "DEBUG")
                                if ack_window == (current_window % 2 ** profile_uplink.M):
                                    print_and_log(
                                        "Last ACK received: Fragments reassembled successfully. End of transmission. "
                                        "(While retransmitting)", "INFO")
                                    pycom.rgbled(0x007f00)  # green
                                    tx_status_ok = True
                                    break
                                else:
                                    print_and_log("Last ACK window does not correspond to last window. "
                                                  "(While retransmitting)", "ERROR")
                                    senderAbort = SenderAbort(profile_uplink,
                                                              fragment.header.RULE_ID,
                                                              fragment.header.DTAG,
                                                              fragment.header.W)
                                    print_and_log("Generated Sender-Abort", "INFO")
                                    print_and_log("--- senderAbort:{}".format(senderAbort.to_string()), "DEBUG")
                                    print_and_log("--- senderAbort:{}".format(senderAbort.to_bytes()), "DEBUG")
                                    send_sigfox(the_socket,
                                                senderAbort,
                                                bytes(senderAbort.to_bytes()),
                                                profile_uplink.RETRANSMISSION_TIMER_VALUE,
                                                profile_uplink, False,
                                                profile_downlink.MTU, True)
                                    break
                            else:
                                print_and_log("Sending All-1 again.", "INFO")
                                attempts += 1
                                print_and_log("attempts:{}".format(attempts), "DEBUG")
                                print("RuleID:{}, WINDOW:{}, FCN:{}".format(fragment.header.RULE_ID,
                                                                            fragment.header.W,
                                                                            fragment.header.FCN),
                                      "DEBUG")
                                retransmitting = True
                                ack = None
                                try:
                                    ack = send_sigfox(the_socket,
                                                      fragment,
                                                      data,
                                                      profile_uplink.RETRANSMISSION_TIMER_VALUE,
                                                      profile_uplink,
                                                      True)
                                except SCHCReceiverAbortReceived:
                                    print_and_log('SCHC Receiver Abort Message Received', "ERROR")
                                    break
                                break

                        elif ack:
                            print_and_log('ack', "DEBUG")
                            c = ack[index_c]

                            # If the C bit is set to 1 then we're done.
                            if c == '1':
                                print_and_log("{}".format(ack_window), "DEBUG")
                                print_and_log("{}".format(current_window), "DEBUG")
                                if ack_window == (current_window % 2 ** profile_uplink.M):
                                    print_and_log("Last ACK received: "
                                                  "Fragments reassembled successfully. "
                                                  "End of transmission. "
                                                  "(While retransmitting)",
                                                  "INFO")
                                    pycom.rgbled(0x007f00)  # green
                                    tx_status_ok = True
                                    break
                                else:
                                    print_and_log("Last ACK window does not correspond to last window."
                                                  "(While retransmitting)",
                                                  "ERROR")
                                    senderAbort = SenderAbort(profile_uplink, fragment.header.RULE_ID,
                                                              fragment.header.DTAG, fragment.header.W)
                                    print_and_log("Generated Sender-Abort", "INFO")
                                    print_and_log("--- senderAbort:{}".format(senderAbort.to_string()), "DEBUG")
                                    print_and_log("--- senderAbort:{}".format(senderAbort.to_bytes()), "DEBUG")
                                    send_sigfox(the_socket,
                                                senderAbort,
                                                bytes(senderAbort.to_bytes()),
                                                profile_uplink.RETRANSMISSION_TIMER_VALUE,
                                                profile_uplink,
                                                False,
                                                profile_downlink.MTU,
                                                True)
                                    break
                            else:
                                print_and_log("Sending All-1 again.", "INFO")
                                attempts += 1
                                print_and_log("attempts:{}".format(attempts), "DEBUG")
                                print_and_log("RuleID:{}, WINDOW:{}, FCN:{}".format(fragment.header.RULE_ID,
                                                                                    fragment.header.W,
                                                                                    fragment.header.FCN),
                                              "DEBUG")
                                retransmitting = True
                                ack = None
                                try:
                                    ack = send_sigfox(the_socket,
                                                      fragment,
                                                      data,
                                                      profile_uplink.RETRANSMISSION_TIMER_VALUE,
                                                      profile_uplink,
                                                      True)
                                except SCHCReceiverAbortReceived:
                                    print_and_log('SCHC Receiver Abort Message Received', "ERROR")
                                    break
                                break

                        else:
                            # NO ACK was received after resending the All-1
                            # Or after sending al All-0 that was lost before.
                            continue

                print_and_log("Proceeding to next window", "INFO")
                resent = False
                retransmitting = False
                current_window += 1
                break

            else:
                print_and_log("NO ACK RECEIVED", "INFO")
                pycom.rgbled(0x7f0000)  # red
                attempts += 1
                if attempts < profile_uplink.MAX_ACK_REQUESTS:
                    print_and_log("Waiting for RETRANSMISSION_TIMER_VALUE time:{}".format(
                        profile_uplink.RETRANSMISSION_TIMER_VALUE), "INFO")
                    print_and_log("Attempt number: {}".format(attempts), "DEBUG")
                    print_and_log("No ACK received (RETRANSMISSION_TIMER_VALUE expired). "
                                  "Sending last SCHC fragment...", "INFO")
                    ack = None
                    print_and_log("RuleID:{}, WINDOW:{}, FCN:{}".format(fragment.header.RULE_ID,
                                                                fragment.header.W,
                                                                fragment.header.FCN),
                                  "DEBUG")
                    try:
                        ack = send_sigfox(the_socket,
                                          fragment,
                                          data,
                                          profile_uplink.RETRANSMISSION_TIMER_VALUE,
                                          profile_uplink,
                                          True,
                                          profile_downlink.MTU)
                    except SCHCReceiverAbortReceived:
                        print_and_log('SCHC Receiver Abort Message Received', "ERROR")
                        break

                else:
                    print_and_log("MAX_ACK_REQUESTS reached. Goodbye.", "ERROR")
                    print("A sender-abort MUST be sent...")
                    senderAbort = SenderAbort(profile_uplink,
                                              fragment.header.RULE_ID,
                                              fragment.header.DTAG,
                                              fragment.header.W)
                    print_and_log("Generated Sender-Abort", "INFO")
                    print_and_log("--- senderAbort:{}".format(senderAbort.to_string()), "DEBUG")
                    print_and_log("--- senderAbort:{}".format(senderAbort.to_bytes()), "DEBUG")
                    send_sigfox(the_socket,
                                senderAbort,
                                bytes(senderAbort.to_bytes()),
                                profile_uplink.RETRANSMISSION_TIMER_VALUE,
                                profile_uplink,
                                False,
                                profile_downlink.MTU,
                                True)

                    break

        # Continue to next fragment
        if not retransmitting:
            i += 1

    end_sending_time = chronometer.read()
    print_and_log('Stats', INFO)
    filename_stats = "stats/LoPy_stats_file_v7.1_{}_{}.json".format(total_size, repetition)
