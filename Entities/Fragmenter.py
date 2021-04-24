# -*- coding: utf-8 -*-

from math import ceil, floor
from Messages.FragmentHeader import FragmentHeader
from schc_utils import zfill


class Fragmenter:
    PROFILE = None
    SCHC_PACKET = None

    def __init__(self, profile, schc_packet):
        self.PROFILE = profile
        self.SCHC_PACKET = schc_packet

    def fragment(self):
        payload_max_length = int((self.PROFILE.UPLINK_MTU - self.PROFILE.HEADER_LENGTH) / 8)
        message = self.SCHC_PACKET
        fragment_list = []
        n = self.PROFILE.N
        m = self.PROFILE.M
        number_of_fragments = int(ceil(float(len(message)) / payload_max_length))

        print("[FRGM] Fragmenting message into " + str(number_of_fragments) + " pieces...")

        # check if the packet size can be transmitted or not
        if len(fragment_list) > (2 ** self.PROFILE.M) * self.PROFILE.WINDOW_SIZE:
            print(len(fragment_list))
            print((2 ** self.PROFILE.M) * self.PROFILE.WINDOW_SIZE)
            print(
                "The SCHC packet cannot be fragmented in 2 ** M * WINDOW_SIZE fragments or less. A Rule ID cannot be "
                "selected.")
        # What does this mean?
        # Sending packet does not fit (should be tested in fragmentation)

        for i in range(number_of_fragments):
            w = zfill(bin(int(floor((i / (2 ** n - 1) % (2 ** m)))))[2:], self.PROFILE.M)
            fcn = zfill(bin((2 ** n - 2) - (i % (2 ** n - 1)))[2:], self.PROFILE.N)

            fragment_payload = message[i * payload_max_length:(i + 1) * payload_max_length]

            if len(self.SCHC_PACKET) <= 300:
                if len(fragment_payload) < payload_max_length or i == (len(range(number_of_fragments)) - 1):
                    header = FragmentHeader(self.PROFILE, rule_id="00", dtag="0", w=w, fcn="111")
                else:
                    header = FragmentHeader(self.PROFILE, rule_id="00", dtag="0", w=w, fcn=fcn)
            else:
                if len(fragment_payload) < payload_max_length or i == (len(range(number_of_fragments)) - 1):
                    header = FragmentHeader(self.PROFILE, rule_id="1111000", dtag="0", w=w, fcn="11111")
                else:
                    header = FragmentHeader(self.PROFILE, rule_id="1111000", dtag="0", w=w, fcn=fcn)
            fragment = [header.to_bytes(), fragment_payload]
            # print("[" + header.string + "]" + str(fragment_payload))
            fragment_list.append(fragment)

        print("[FRGM] Fragmentation complete.")

        return fragment_list
