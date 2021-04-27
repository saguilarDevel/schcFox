from Messages.FragmentHeader import FragmentHeader
from schc_utils import zfill, is_monochar
import binascii


class Fragment:
    PROFILE = None
    HEADER = None
    PAYLOAD = None

    def __init__(self, profile, fragment):
        self.PROFILE = profile

        dtag_index = profile.RULE_ID_SIZE
        w_index = dtag_index + profile.T
        fcn_index = w_index + profile.M
        payload_index = fcn_index + profile.N

        header = zfill(str(bin(int.from_bytes(fragment[0], 'big')))[2:], profile.HEADER_LENGTH)
        payload = fragment[1]

        rule_id = str(header[:dtag_index])
        dtag = str(header[dtag_index:w_index])
        window = str(header[w_index:fcn_index])
        fcn = str(header[fcn_index:payload_index])

        self.HEADER = FragmentHeader(self.PROFILE, rule_id, dtag, window, fcn)
        self.PAYLOAD = payload

    def to_bytes(self):
        return self.HEADER.to_bytes() + self.PAYLOAD

    def to_string(self):
        return str(self.to_bytes())

    def to_hex(self):
        return binascii.hexlify(self.to_bytes())

    def is_all_1(self):
        fcn = self.HEADER.FCN
        payload = self.PAYLOAD.decode()
        return fcn[0] == '1' and is_monochar(fcn) and not (payload[0] == '0' and is_monochar(payload))

    def is_all_0(self):
        fcn = self.HEADER.FCN
        return fcn[0] == '0' and is_monochar(fcn)

    def expects_ack(self):
        return self.is_all_0() or self.is_all_1()

    def is_sender_abort(self):
        fcn = self.HEADER.FCN
        padding = self.PAYLOAD.decode()
        return fcn[0] == '1' and is_monochar(fcn) and padding[0] == '0' and is_monochar(padding)
