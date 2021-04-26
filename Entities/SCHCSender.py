from network import Sigfox
import socket as s
from machine import Timer

from Entities.Fragmenter import Fragmenter
from Entities.SCHCLogger import SCHCLogger
from Entities.SCHCTimer import SCHCTimer
from Entities.Sigfox import SigfoxProfile
from Entities.exceptions import *
from Messages.ACK import ACK
from Messages.Fragment import Fragment
from Messages.SenderAbort import SenderAbort


class SCHCSender:
    PROTOCOL = None
    PROFILE = None
    SOCKET = None
    MESSAGE = ''
    FRAGMENTS = []
    ATTEMPTS = None
    FRAGMENT_IDEX = None
    CURRENT_WINDOW = None
    LAST_WINDOW = None
    TIMER = None
    HEADER_BYTES = None
    DELAY = None

    LOGGER = None

    def __init__(self):
        self.PROTOCOL = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ4)
        self.SOCKET = s.socket(s.AF_SIGFOX, s.SOCK_RAW)
        self.SOCKET.setblocking(True)
        self.FRAGMENT_INDEX = 0
        self.TIMER = SCHCTimer(0)
        self.DELAY = 0

    def set_logging(self, filename, json_file):
        self.LOGGER = SCHCLogger(filename, json_file)

    def set_delay(self, delay):
        self.DELAY = delay

    def send(self, message):
        self.SOCKET.setsockopt(s.SOL_SIGFOX, s.SO_RX, False)
        self.SOCKET.send(message)

    def send_and_recv(self, message):
        self.SOCKET.setsockopt(s.SOL_SIGFOX, s.SO_RX, True)
        self.SOCKET.send(message)
        return self.SOCKET.recv(self.PROFILE.DOWNLINK_MTU // 8)

    def set_session(self, mode, message):
        self.HEADER_BYTES = 1 if len(message) <= 300 else 2
        self.PROFILE = SigfoxProfile("UPLINK", mode, self.HEADER_BYTES)

        if self.LOGGER is not None:
            self.LOGGER.CHRONO = Timer.Chrono()
            self.LOGGER.CHRONO.start()

        self.MESSAGE = message
        fragmenter = Fragmenter(self.PROFILE, message)
        self.FRAGMENTS = fragmenter.fragment()

        if self.LOGGER is not None:
            self.LOGGER.FRAGMENTATION_TIME = self.LOGGER.CHRONO.read()
            self.LOGGER.debug("fragmentation time -> {}".format(self.LOGGER.FRAGMENTATION_TIME))

        if len(self.FRAGMENTS) > (2 ** self.PROFILE.M) * self.PROFILE.WINDOW_SIZE:
            raise RuleSelectionError

        self.LAST_WINDOW = (len(self.FRAGMENTS) - 1) // self.PROFILE.WINDOW_SIZE
        self.ATTEMPTS = 0

    def start_session(self):
        self.CURRENT_WINDOW = 0

        total_size = len(self.MESSAGE)
        current_size = 0

        if self.LOGGER is not None:
            self.LOGGER.START_SENDING_TIME = self.LOGGER.CHRONO.read()
            self.LOGGER.TOTAL_SIZE = total_size

        while self.FRAGMENT_INDEX < len(self.FRAGMENTS):
            fragment = Fragment(self.PROFILE, self.FRAGMENTS[self.FRAGMENT_INDEX])

            if self.LOGGER is not None:
                self.LOGGER.info("Sending...")
                self.LOGGER.LAPS.append(self.LOGGER.CHRONO.read())
                self.LOGGER.debug("laps - > {}".format(self.LOGGER.LAPS))

                self.LOGGER.debug("--------------------------")
                self.LOGGER.debug("{}th fragment:".format(self.FRAGMENT_INDEX))
                self.LOGGER.debug("RuleID:{}, DTAG:{}, WINDOW:{}, FCN:{}".format(fragment.HEADER.RULE_ID,
                                                                                 fragment.HEADER.DTAG,
                                                                                 fragment.HEADER.W,
                                                                                 fragment.HEADER.FCN))
                self.LOGGER.debug("SCHC Fragment: {}".format(fragment.to_string()))
                self.LOGGER.debug("SCHC Fragment Payload: {}".format(fragment.PAYLOAD))

            current_size += len(self.FRAGMENTS[self.FRAGMENT_INDEX][1])
            percent = round(float(current_size) / float(total_size) * 100, 2)
            self.LOGGER.debug("{} / {}, {}%".format(current_size,
                                                    total_size,
                                                    percent))

            try:
                self.schc_send(fragment)
            except SCHCError:
                break

        if self.LOGGER is not None:
            self.LOGGER.END_SENDING_TIME = self.LOGGER.CHRONO.read()
            self.LOGGER.save()

    def schc_send(self, fragment_sent, retransmit=False):

        ack = None
        current_fragment = {}
        logging = self.LOGGER is not None

        self.TIMER.wait(self.DELAY)

        if logging:
            self.LOGGER.START_SENDING_TIME += self.DELAY
            current_fragment = {'RULE_ID': fragment_sent.HEADER.RULE_ID,
                                'W': fragment_sent.HEADER.W,
                                'FCN': fragment_sent.HEADER.FCN,
                                'data': fragment_sent.to_bytes(),
                                'abort': False,
                                'receiver_abort_message': "",
                                'receiver_abort_received': False}

        if fragment_sent.is_all_0() and not retransmit:
            self.LOGGER.debug("[POST] This is an All-0. Using All-0 SIGFOX_DL_TIMEOUT.")
            self.SOCKET.settimeout(self.PROFILE.SIGFOX_DL_TIMEOUT)
            if logging:
                current_fragment["timeout"] = self.PROFILE.SIGFOX_DL_TIMEOUT
        elif fragment_sent.is_all_1():
            self.LOGGER.debug("[POST] This is an All-1. Using RETRANSMISSION_TIMER_VALUE. Increasing ACK attempts.")
            self.ATTEMPTS += 1
            self.SOCKET.settimeout(self.PROFILE.RETRANSMISSION_TIMER_VALUE)
            if logging:
                current_fragment["timeout"] = self.PROFILE.RETRANSMISSION_TIMER_VALUE
        else:
            self.SOCKET.settimeout(None)
            if logging:
                current_fragment["timeout"] = None

        data = fragment_sent.to_bytes()

        self.LOGGER.info("[POST] Posting fragment {} ({})".format(fragment_sent.HEADER.to_string(),
                                                                  fragment_sent.to_hex()))

        if fragment_sent.expects_ack() and not retransmit:
            self.SOCKET.setsockopt(s.SOL_SIGFOX, s.SO_RX, True)
        else:
            self.SOCKET.setsockopt(s.SOL_SIGFOX, s.SO_RX, False)

        try:
            if logging:
                current_fragment['sending_start'] = self.LOGGER.CHRONO.read()

            self.SOCKET.send(data)

            if fragment_sent.expects_ack():
                if logging:
                    current_fragment['downlink_enable'] = True
                    current_fragment['ack_received'] = False
                    current_fragment['fragment_size'] = len(data)

                ack = self.SOCKET.recv(self.PROFILE.DOWNLINK_MTU // 8)

            if logging:
                current_fragment['sending_end'] = self.LOGGER.CHRONO.read()
                current_fragment['send_time'] = current_fragment['sending_end'] - current_fragment['sending_start']
                current_fragment['rssi'] = self.PROTOCOL.rssi()
                self.LOGGER.debug("Response received at: {}: ".format(self.LOGGER.CHRONO.read()))
                self.LOGGER.debug('ack -> {}'.format(ack))
                self.LOGGER.debug('message RSSI: {}'.format(self.PROTOCOL.rssi()))

            if fragment_sent.is_sender_abort():
                if logging:
                    self.LOGGER.debug("--- senderAbort:{}".format(fragment_sent.to_string()))
                    self.LOGGER.debug("--- senderAbort:{}".format(fragment_sent.to_bytes()))
                    current_fragment['abort'] = True
                self.LOGGER.error("Sent Sender-Abort. Goodbye")
                self.LOGGER.FRAGMENTS_INFO_ARRAY.append(current_fragment)
                raise SenderAbortError

            if not fragment_sent.expects_ack() and not retransmit:
                self.LOGGER.FRAGMENTS_INFO_ARRAY.append(current_fragment)
                self.FRAGMENT_INDEX += 1
                return

            if ack is not None:
                if logging:
                    current_fragment['ack'] = ack
                    current_fragment['ack_received'] = True
                self.LOGGER.info("[ACK] Bytes: {}. Ressetting attempts counter to 0.".format(ack))
                self.ATTEMPTS = 0

                # Parse ACK
                ack_object = ACK.parse_from_bytes(self.PROFILE, ack)

                if ack_object.is_receiver_abort():
                    self.LOGGER.error("ERROR: Receiver Abort received. Aborting communication.")

                    if logging:
                        current_fragment['receiver_abort_message'] = ack
                        current_fragment['receiver_abort_received'] = True

                    raise ReceiverAbortError

                if not fragment_sent.expects_ack():
                    self.LOGGER.error("ERROR: ACK received but not requested ({}).".format(ack))
                    raise UnrequestedACKError

                # Extract data from ACK
                ack_window = ack_object.HEADER.W
                ack_window_number = ack_object.HEADER.WINDOW_NUMBER
                c = ack_object.HEADER.C
                bitmap = ack_object.BITMAP
                self.LOGGER.debug("ACK: {}".format(ack))
                self.LOGGER.debug("ACK window: {}".format(ack_window))
                self.LOGGER.debug("ACK bitmap: {}".format(bitmap))
                self.LOGGER.debug("ACK C bit: {}".format(c))
                self.LOGGER.debug("last window: {}".format(self.LAST_WINDOW))

                # If the W field in the SCHC ACK corresponds to the last window of the SCHC Packet:
                if ack_window_number == self.LAST_WINDOW:
                    # If the C bit is set, the sender MAY exit successfully.
                    if c == '1':
                        self.LOGGER.info("Last ACK received, fragments reassembled successfully. End of transmission.")
                        if logging:
                            self.LOGGER.FRAGMENTS_INFO_ARRAY.append(current_fragment)
                            self.LOGGER.FINISHED = True
                        self.FRAGMENT_IDEX += 1
                        return
                    # Otherwise,
                    else:
                        # If the Profile mandates that the last tile be sent in an All-1 SCHC Fragment
                        # (we are in the last window), .is_all_1() should be true:
                        if fragment_sent.is_all_1():
                            # This is the last bitmap, it contains the data up to the All-1 fragment.
                            last_bitmap = bitmap[:len(self.FRAGMENTS) % self.PROFILE.WINDOW_SIZE]
                            self.LOGGER.debug("last bitmap {}".format(last_bitmap))
                            # If the SCHC ACK shows no missing tile at the receiver, abort.
                            # (C = 0 but transmission complete)
                            if last_bitmap[0] == '1' and all(last_bitmap):
                                self.LOGGER.error("ERROR: SCHC ACK shows no missing tile at the receiver.")
                                self.schc_send(SenderAbort(fragment_sent.PROFILE, fragment_sent.HEADER))

                            # Otherwise (fragments are lost),
                            else:
                                # Check for lost fragments.
                                for j in range(len(last_bitmap)):
                                    # If the j-th bit of the bitmap is 0, then the j-th fragment was lost.
                                    if last_bitmap[j] == '0':
                                        self.LOGGER.info("The {}th ({} / {}) fragment was lost! "
                                                         "Sending again...".format(j,
                                                                                   self.PROFILE.WINDOW_SIZE * ack_window_number + j,
                                                                                   len(self.FRAGMENTS)))
                                        # Try sending again the lost fragment.
                                        fragment_to_be_resent = Fragment(self.PROFILE,
                                                                         self.FRAGMENTS[
                                                                             self.PROFILE.WINDOW_SIZE * ack_window + j])
                                        self.LOGGER.debug("Lost fragment: {}".format(fragment_to_be_resent.to_string()))
                                        self.schc_send(fragment_to_be_resent, retransmit=True)

                                # Send All-1 again to end communication or check again for lost data.
                                self.schc_send(fragment_sent)

                        else:
                            self.LOGGER.error("ERROR: While being at the last window, the ACK-REQ was not an All-1. "
                                              "This is outside of the Sigfox scope.")
                            raise BadProfileError
                # Otherwise, there are lost fragments in a non-final window.
                else:
                    # Check for lost fragments.
                    for j in range(len(bitmap)):
                        # If the j-th bit of the bitmap is 0, then the j-th fragment was lost.
                        if bitmap[j] == '0':
                            self.LOGGER.info("The {}th ({} / {}) fragment was lost! "
                                             "Sending again...".format(j,
                                                                       self.PROFILE.WINDOW_SIZE * ack_window_number + j,
                                                                       len(self.FRAGMENTS)))
                            # Try sending again the lost fragment.
                            fragment_to_be_resent = Fragment(self.PROFILE,
                                                             self.FRAGMENTS[
                                                                 self.PROFILE.WINDOW_SIZE * ack_window_number + j])
                            self.LOGGER.debug("Lost fragment: {}".format(fragment_to_be_resent.to_string()))
                            self.schc_send(fragment_to_be_resent, retransmit=True)
                    if fragment_sent.is_all_1():
                        # Send All-1 again to end communication.
                        self.schc_send(fragment_sent)
                    elif fragment_sent.is_all_0():
                        # Continue with next window
                        self.FRAGMENT_INDEX += 1
                        self.CURRENT_WINDOW += 1

        except OSError as e:
            if logging:
                current_fragment['sending_end'] = self.LOGGER.CHRONO.read()
                current_fragment['send_time'] = current_fragment['sending_end'] - current_fragment['sending_start']
                current_fragment['rssi'] = self.PROTOCOL.rssi()
                current_fragment['ack'] = ""
                current_fragment['ack_received'] = False
                self.LOGGER.info("Error at: {}: ".format(self.LOGGER.CHRONO.read()))
                self.LOGGER.info('Error number {}, {}'.format(e.args[0], e))

            # If an ACK was expected
            if fragment_sent.is_all_1():
                # If the attempts counter is strictly less than MAX_ACK_REQUESTS, try again
                if logging:
                    self.LOGGER.debug("attempts:{}".format(self.ATTEMPTS))
                if self.ATTEMPTS < self.PROFILE.MAX_ACK_REQUESTS:
                    self.LOGGER.info("SCHC Timeout reached while waiting for an ACK. Sending the ACK Request again...")
                    self.schc_send(fragment_sent, retransmit=False)
                # Else, exit with an error.
                else:
                    self.LOGGER.error("ERROR: MAX_ACK_REQUESTS reached. Sending Sender-Abort.")
                    abort = SenderAbort(self.PROFILE, fragment_sent.HEADER)
                    self.schc_send(abort)

            # If the ACK can be not sent (Sigfox only)
            if fragment_sent.is_all_0():
                self.LOGGER.info("All-0 timeout reached. Proceeding to next window.")
                self.FRAGMENT_INDEX += 1
                self.CURRENT_WINDOW += 1

            # Else, Sigfox communication failed.
            else:
                self.LOGGER.error("ERROR: Timeout reached.")
                raise NetworkDownError
