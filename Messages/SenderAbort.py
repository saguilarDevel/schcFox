from Messages.Fragment import Fragment
from schc_utils import bitstring_to_bytes


class SenderAbort(Fragment):

    def __init__(self, profile, header):
        rule_id = header.RULE_ID
        dtag = header.DTAG
        w = header.W
        fcn = "1" * profile.N
        new_header = rule_id + dtag + w + fcn
        payload = ''
        payload_max_length = int((profile.UPLINK_MTU - profile.HEADER_LENGTH) / 8)

        while len(payload) < payload_max_length:
            payload += '0'

        super().__init__(profile, [bitstring_to_bytes(new_header), payload.encode()])
