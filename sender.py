# -*- coding: utf-8 -*-

# Microphyton imports
import ubinascii
# Chronometers for testing
from machine import Timer

from Entities.Fragmenter import Fragmenter
from Entities.SCHCTimer import SCHCTimer
from Entities.SigfoxProfile import SigfoxProfile
from Entities.exceptions import *
from Messages.ACK import ACK
from Messages.Fragment import Fragment
from Messages.SenderAbort import SenderAbort
from schc_utils import *

sent = 0
received = 0
retransmitted = 0
i = 0
current_window = 0

# Init Chrono
chrono = Timer.Chrono()
timer = SCHCTimer(0)
current_fragment = {}

fragment_list = []


def post(socket, fragment_sent, protocol, retransmit=False):
    global current_fragment, seqNumber, attempts, current_window, last_window, i, sent, received, retransmitted, fragment_list

    profile = fragment_sent.PROFILE
    ack = None

    current_fragment = {'RULE_ID': fragment_sent.HEADER.RULE_ID,
                        'W': fragment_sent.HEADER.W,
                        'FCN': fragment_sent.HEADER.FCN,
                        'data': fragment_sent.to_bytes(),
                        'abort': False,
                        'receiver_abort_message': "",
                        'receiver_abort_received': False}

    if fragment_sent.is_all_0() and not retransmit:
        log_debug("[POST] This is an All-0. Using All-0 SIGFOX_DL_TIMEOUT.")
        socket.settimeout(profile.SIGFOX_DL_TIMEOUT)
        current_fragment["timeout"] = profile.SIGFOX_DL_TIMEOUT
    elif fragment_sent.is_all_1():
        log_debug("[POST] This is an All-1. Using RETRANSMISSION_TIMER_VALUE. Increasing ACK attempts.")
        attempts += 1
        socket.settimeout(profile.RETRANSMISSION_TIMER_VALUE)
        current_fragment["timeout"] = profile.RETRANSMISSION_TIMER_VALUE
    else:
        socket.settimeout(None)
        current_fragment["timeout"] = None

    data = fragment_sent.to_bytes()

    log_info("[POST] Posting fragment {} ({})".format(fragment_sent.HEADER.to_string(),
                                                      fragment_sent.to_hex()))

    if fragment_sent.expects_ack() and not retransmit:
        socket.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, True)
    else:
        socket.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, False)

    try:
        current_fragment['sending_start'] = chrono.read()
        socket.send(data)
        if fragment_sent.expects_ack():
            current_fragment['downlink_enable'] = True
            current_fragment['ack_received'] = False
            current_fragment['fragment_size'] = len(data)

            ack = socket.recv(profile.DOWNLINK_MTU // 8)

        current_fragment['sending_end'] = chrono.read()
        current_fragment['send_time'] = current_fragment['sending_end'] - current_fragment['sending_start']
        current_fragment['rssi'] = protocol.rssi()
        log_debug("Response received at: {}: ".format(chrono.read()))
        log_debug('ack -> {}'.format(ack))
        log_debug('message RSSI: {}'.format(protocol.rssi()))

        if fragment_sent.is_sender_abort():
            log_error("Sent Sender-Abort. Goodbye")
            raise SenderAbortError

        seqNumber += 1
        sent += 1
        if retransmit:
            retransmitted += 1

        if not fragment_sent.expects_ack() and not retransmit:
            i += 1
            return

        # the fragment was posted and an ACK has been received.
        if ack is not None:

            current_fragment['ack'] = ack
            current_fragment['ack_received'] = True

            log_info("[ACK] Bytes: {}. Ressetting attempts counter to 0.".format(ack))

            received += 1
            attempts = 0

            # Parse ACK
            ack_object = ACK.parse_from_bytes(profile, ack)

            if ack_object.is_receiver_abort():
                log_error("ERROR: Receiver Abort received. Aborting communication.")

                current_fragment['receiver_abort_message'] = ack
                current_fragment['receiver_abort_received'] = True

                raise ReceiverAbortError

            if not fragment_sent.expects_ack():
                log_error("ERROR: ACK received but not requested ({}).".format(ack))
                raise UnrequestedACKError

            # Extract data from ACK
            ack_window = ack_object.HEADER.W
            ack_window_number = ack_object.HEADER.WINDOW_NUMBER
            c = ack_object.HEADER.C
            bitmap = ack_object.BITMAP
            log_debug("ACK: {}".format(ack))
            log_debug("ACK window: {}".format(ack_window))
            log_debug("ACK bitmap: {}".format(bitmap))
            log_debug("ACK C bit: {}".format(c))
            log_debug("last window: {}".format(last_window))

            window_size = profile.WINDOW_SIZE

            # If the W field in the SCHC ACK corresponds to the last window of the SCHC Packet:
            if ack_window_number == last_window:
                # If the C bit is set, the sender MAY exit successfully.
                if c == '1':
                    log_info("Last ACK received, fragments reassembled successfully. End of transmission.")
                    return
                # Otherwise,
                else:
                    # If the Profile mandates that the last tile be sent in an All-1 SCHC Fragment
                    # (we are in the last window), .is_all_1() should be true:
                    if fragment_sent.is_all_1():
                        # This is the last bitmap, it contains the data up to the All-1 fragment.
                        last_bitmap = bitmap[:len(fragment_list) % window_size]
                        log_debug("last bitmap {}".format(last_bitmap))

                        # If the SCHC ACK shows no missing tile at the receiver, abort.
                        # (C = 0 but transmission complete)
                        if last_bitmap[0] == '1' and all(last_bitmap):
                            log_error("ERROR: SCHC ACK shows no missing tile at the receiver.")
                            post(socket, SenderAbort(fragment_sent.PROFILE, fragment_sent.HEADER), protocol)

                        # Otherwise (fragments are lost),
                        else:
                            # Check for lost fragments.
                            for j in range(len(last_bitmap)):
                                # If the j-th bit of the bitmap is 0, then the j-th fragment was lost.
                                if last_bitmap[j] == '0':
                                    log_info("The {}th ({} / {}) fragment was lost! "
                                             "Sending again...".format(j,
                                                                       window_size * ack_window_number + j,
                                                                       len(fragment_list)))
                                    # Try sending again the lost fragment.
                                    fragment_to_be_resent = Fragment(profile,
                                                                     fragment_list[window_size * ack_window + j])
                                    log_debug("Lost fragment: {}".format(fragment_to_be_resent.to_string()))
                                    post(socket, fragment_to_be_resent, protocol, retransmit=True)

                            # Send All-1 again to end communication.
                            post(socket, fragment_sent, protocol)

                    else:
                        log_error("ERROR: While being at the last window, the ACK-REQ was not an All-1. "
                                  "This is outside of the Sigfox scope.")
                        raise BadProfileError

            # Otherwise, there are lost fragments in a non-final window.
            else:
                # Check for lost fragments.
                for j in range(len(bitmap)):
                    # If the j-th bit of the bitmap is 0, then the j-th fragment was lost.
                    if bitmap[j] == '0':
                        log_info("The {}th ({} / {}) fragment was lost! "
                                 "Sending again...".format(j,
                                                           window_size * ack_window_number + j,
                                                           len(fragment_list)))
                        # Try sending again the lost fragment.
                        fragment_to_be_resent = Fragment(profile,
                                                         fragment_list[window_size * ack_window_number + j])
                        log_debug("Lost fragment: {}".format(fragment_to_be_resent.to_string()))
                        post(socket, fragment_to_be_resent, protocol, retransmit=True)
                if fragment_sent.is_all_1():
                    # Send All-1 again to end communication.
                    post(socket, fragment_sent, protocol)
                elif fragment_sent.is_all_0():
                    # Continue with next window
                    i += 1
                    current_window += 1

    # If the timer expires
    except OSError as e:

        current_fragment['sending_end'] = chrono.read()
        current_fragment['send_time'] = current_fragment['sending_end'] - current_fragment['sending_start']
        current_fragment['rssi'] = protocol.rssi()
        current_fragment['ack'] = ""
        current_fragment['ack_received'] = False
        log_info("Error at: {}: ".format(chrono.read()))
        log_info('Error number {}, {}'.format(e.args[0], e))

        # If an ACK was expected
        if fragment_sent.is_all_1():
            # If the attempts counter is strictly less than MAX_ACK_REQUESTS, try again
            log_debug("attempts:{}".format(attempts))
            if attempts < profile.MAX_ACK_REQUESTS:
                log_info("SCHC Timeout reached while waiting for an ACK. Sending the ACK Request again...")
                post(socket, fragment_sent)
            # Else, exit with an error.
            else:
                log_error("ERROR: MAX_ACK_REQUESTS reached. Sending Sender-Abort.")
                header = fragment_sent.HEADER
                abort = SenderAbort(profile, header)
                post(socket, abort, protocol)

        # If the ACK can be not sent (Sigfox only)
        if fragment_sent.is_all_0():
            log_info("All-0 timeout reached. Proceeding to next window.")
            i += 1
            current_window += 1

        # Else, Sigfox communication failed.
        else:
            log_error("ERROR: Timeout reached.")
            raise NetworkDownError


def start_session(socket, message, repetition, protocol, logging=False):
    global current_fragment, seqNumber, attempts, current_window, last_window, i, sent, received, retransmitted, fragment_list

    laps = []
    start_sending_time = 0
    end_sending_time = 0

    # stats variables (for testing)
    current_fragment = {}
    fragments_info_array = []
    tx_status_ok = False

    # Initialize variables.
    total_size = len(message)
    current_size = 0
    i = 0
    current_window = 0
    header_bytes = 1 if total_size <= 300 else 2
    log_debug("total_size = {} and header_bytes = {}".format(total_size, header_bytes))
    profile = SigfoxProfile("UPLINK", "ACK ON ERROR", header_bytes)
    window_size = profile.WINDOW_SIZE

    # Send the "CLEAN" message
    log_debug("Sending CLEAN message")
    clean_msg = str(ubinascii.hexlify("CLEAN_ALL"))[2:-1] if repetition == 0 else str(ubinascii.hexlify("CLEAN"))[2:-1]
    socket.send(ubinascii.unhexlify("{}a{}".format(header_bytes, clean_msg)))

    # Wait for the cleaning function to end
    timer.wait(30)

    # Start Time
    chrono.start()

    # Fragment the file.
    fragmenter = Fragmenter(profile, message)
    fragment_list = fragmenter.fragment()

    fragmentation_time = chrono.read()
    log_debug("fragmentation time -> {}".format(fragmentation_time))

    last_window = (len(fragment_list) - 1) // window_size

    # The fragment sender MUST initialize the Attempts counter to 0 for that Rule ID and DTag value pair
    # (a whole SCHC packet)
    attempts = 0

    if len(fragment_list) > (2 ** profile.M) * window_size:
        raise RuleSelectionError

    start_sending_time = chrono.read()

    # Start sending fragments.
    while i < len(fragment_list):
        # Convert to a Fragment class for easier manipulation.
        fragment = Fragment(profile, fragment_list[i])

        # Send the data.
        log_info("Sending...")

        laps.append(chrono.read())
        log_debug("laps - > {}".format(laps))

        log_debug("--------------------------")
        log_debug("{}th fragment:".format(i))
        log_debug("RuleID:{}, DTAG:{}, WINDOW:{}, FCN:{}".format(fragment.HEADER.RULE_ID,
                                                                 fragment.HEADER.DTAG,
                                                                 fragment.HEADER.W,
                                                                 fragment.HEADER.FCN))
        log_debug("SCHC Fragment: {}".format(fragment.to_string()))
        log_debug("SCHC Fragment Payload: {}".format(fragment.PAYLOAD))

        current_size += len(fragment_list[i][1])
        percent = round(float(current_size) / float(total_size) * 100, 2)
        log_debug("{} / {}, {}%".format(current_size,
                                        total_size,
                                        percent))

        current_fragment = {}

        # On All-0 fragments, this function will wait for SIGFOX_DL_TIMER to expire
        # On All-1 fragments, this function will enter retransmission phase.
        post(socket, fragment, protocol)

        print("current_fragment:{}".format(current_fragment))
        fragments_info_array.append(current_fragment)

        # timer = SCHCTimer(profile.INACTIVITY_TIMER_VALUE * 2)
        # timer.wait()

    end_sending_time = chrono.read()
    log_debug('Stats')
    filename_stats = "stats/LoPy_stats_file_v7.1_{}_{}.json".format(total_size, repetition)
    log_debug("Writing to file {}".format(filename_stats))

    with open(filename_stats, "w") as f:
        results_json = {}
        for index, fragment in enumerate(fragments_info_array):
            if fragment['downlink_enable'] and not fragment['receiver_abort_received']:
                log_debug('{} - W:{}, FCN:{}, TT:{}s, '
                          'DL(E):{}, ack(R):{}'.format(index,
                                                       fragment['W'],
                                                       fragment['FCN'],
                                                       fragment['send_time'],
                                                       fragment['downlink_enable'],
                                                       fragment['ack_received']))
            elif fragment['abort']:
                log_debug('{} - W:{}, FCN:{}, TT:{}s, '
                          'SCHC Sender Abort '.format(index,
                                                      fragment['W'],
                                                      fragment['FCN'],
                                                      fragment['send_time'],
                                                      fragment['downlink_enable'],
                                                      fragment['ack_received']))
            elif fragment['receiver_abort_received']:
                log_debug('{} - W:{}, FCN:{}, TT:{}s, DL(E):{}, ack(R):{} '
                          'SCHC Receiver Abort '.format(index,
                                                        fragment['W'],
                                                        fragment['FCN'],
                                                        fragment['send_time'],
                                                        fragment['downlink_enable'],
                                                        fragment['ack_received']))
            else:
                log_debug('{} - W:{}, FCN:{}, TT:{}s'.format(index,
                                                             fragment['W'],
                                                             fragment['FCN'],
                                                             fragment['send_time']))

            results_json["{}".format(index)] = fragment

        log_debug("TT: Transmission Time, DL (E): Downlink enable, ack (R): ack received")

        total_transmission_results = {'fragments': results_json,
                                      'fragmentation_time': fragmentation_time,
                                      'total_transmission_time': end_sending_time - start_sending_time,
                                      'total_number_of_fragments': len(fragments_info_array),
                                      'payload_size': total_size,
                                      'tx_status_ok': tx_status_ok}

        log_debug("fragmentation time: {}".format(fragmentation_time))
        log_debug("total sending time: {}".format(end_sending_time - start_sending_time))
        log_debug("total number of fragments sent: {}".format(len(fragments_info_array)))
        log_debug('tx_status_ok: {}'.format(tx_status_ok))
        # print("total_transmission_results:{}".format(total_transmission_results))
        f.write(json.dumps(total_transmission_results))

        socket.close()
        timer.wait(30)
