from Entities.Protocol import Protocol


class SigfoxProfile(Protocol):
    direction = None
    mode = None

    def __init__(self, direction, mode, header_bytes):

        self.NAME = "SIGFOX"
        self.direction = direction
        self.mode = mode
        self.RETRANSMISSION_TIMER_VALUE = 45  # (45) enough to let a downlink message to be sent if needed
        self.INACTIVITY_TIMER_VALUE = 60  # (60) for demo purposes

        self.SIGFOX_DL_TIMEOUT = 20  # This is to be tested

        self.L2_WORD_SIZE = 8   # The L2 word size used by Sigfox is 1 byte

        self.N = 0

        self.HEADER_LENGTH = 0

        self.MESSAGE_INTEGRITY_CHECK_SIZE = None  # TBD
        self.RCS_ALGORITHM = None  # TBD

        self.UPLINK_MTU = 12*8
        self.DOWNLINK_MTU = 8*8

        if direction == "UPLINK":
            # if mode == "NO ACK":
            #     self.HEADER_LENGTH = 8
            #     self.RULE_ID_SIZE = 2  # recommended
            #     self.T = 2  # recommended
            #     self.N = 4  # recommended
            #     self.M = 0

            if mode == "ACK ALWAYS":
                pass  # TBD

            if mode == "ACK ON ERROR":
                if header_bytes == 1:
                    self.HEADER_LENGTH = 8
                    self.RULE_ID_SIZE = 2
                    self.T = 1
                    self.N = 3
                    self.M = 2  # recommended to be single
                    self.WINDOW_SIZE = 2 ** self.N - 1
                    self.BITMAP_SIZE = 2 ** self.N - 1  # from excel
                    self.MAX_ACK_REQUESTS = 3  # SHOULD be 2
                    self.MAX_WIND_FCN = 6  # SHOULD be

                elif header_bytes == 2:
                    self.HEADER_LENGTH = 16
                    self.RULE_ID_SIZE = 7
                    self.T = 1
                    self.N = 5
                    self.M = 3  # recommended to be single
                    self.WINDOW_SIZE = 2 ** self.N - 1
                    self.BITMAP_SIZE = 2 ** self.N - 1  # from excel
                    self.MAX_ACK_REQUESTS = 3  # SHOULD be 2
                    self.MAX_WIND_FCN = 6  # SHOULD be

        if direction == "DOWNLINK":
            if mode == "NO ACK":
                self.HEADER_LENGTH = 8
                self.RULE_ID_SIZE = 2
                self.T = 1
                self.M = 2
                self.N = 3
            if mode == "ACK ALWAYS":
                self.HEADER_LENGTH = 8
                self.RULE_ID_SIZE = 2  # recommended
                self.T = 2  # recommended
                self.N = 3  # recommended
                self.M = 1  # MUST be present, recommended to be single
                self.MAX_ACK_REQUESTS = 3  # SHOULD be 2
                self.MAX_WIND_FCN = 6  # SHOULD be

            # Sigfox downlink frames have a fixed length of 8 bytes, which means
            #    that default SCHC algorithm for padding cannot be used.  Therefore,
            #    the 3 last bits of the fragmentation header are used to indicate in
            #    bytes the size of the padding.  A size of 000 means that the full
            #    ramaining frame is used to carry payload, a value of 001 indicates
            #    that the last byte contains padding, and so on.

            else:
                pass