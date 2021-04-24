from Messages.ACKHeader import ACKHeader
from schc_utils import bitstring_to_bytes, is_monochar, zfill


class ACK:
    PROFILE = None
    BITMAP = None
    HEADER = None
    PADDING = None

    def __init__(self, profile, rule_id, dtag, w, c, bitmap, padding=''):
        self.PROFILE = profile
        self.BITMAP = bitmap
        self.PADDING = padding

        # Bitmap may or may not be carried
        self.HEADER = ACKHeader(profile, rule_id, dtag, w, c)

        while len(self.HEADER.to_string() + self.BITMAP + self.PADDING) < profile.DOWNLINK_MTU:
            self.PADDING += '0'

    def to_string(self):
        return self.HEADER.to_string() + self.BITMAP + self.PADDING

    def to_bytes(self):
        return bitstring_to_bytes(self.to_string())

    def length(self):
        return len(self.to_string())

    def is_receiver_abort(self):
        ack_string = self.to_string()
        l2_word_size = self.PROFILE.L2_WORD_SIZE
        header_length = len(self.HEADER.RULE_ID + self.HEADER.DTAG + self.HEADER.W + self.HEADER.C)
        header = ack_string[:header_length]
        padding = ack_string[header_length:ack_string.rfind('1') + 1]
        padding_start = padding[:-l2_word_size]
        padding_end = padding[-l2_word_size:]

        if padding_end == "1" * l2_word_size:
            if padding_start != '' and len(header) % l2_word_size != 0:
                return is_monochar(padding_start) and padding_start[0] == '1'
            else:
                return len(header) % l2_word_size == 0
        else:
            return False

    @staticmethod
    def parse_from_hex(profile, h):
        ack = zfill(bin(int(h, 16))[2:], profile.DOWNLINK_MTU)
        ack_index_dtag = profile.RULE_ID_SIZE
        ack_index_w = ack_index_dtag + profile.T
        ack_index_c = ack_index_w + profile.M
        ack_index_bitmap = ack_index_c + 1
        ack_index_padding = ack_index_bitmap + profile.BITMAP_SIZE

        return ACK(profile,
                   ack[:ack_index_dtag],
                   ack[ack_index_dtag:ack_index_w],
                   ack[ack_index_w:ack_index_c],
                   ack[ack_index_c],
                   ack[ack_index_bitmap:ack_index_padding],
                   ack[ack_index_padding:])

    @staticmethod
    def parse_from_bytes(profile, b):
        ack = ''.join("{:08b}".format(int(byte)) for byte in b)

        ack_index_dtag = profile.RULE_ID_SIZE
        ack_index_w = ack_index_dtag + profile.T
        ack_index_c = ack_index_w + profile.M
        ack_index_bitmap = ack_index_c + 1
        ack_index_padding = ack_index_bitmap + profile.BITMAP_SIZE

        return ACK(profile,
                   ack[:ack_index_dtag],
                   ack[ack_index_dtag:ack_index_w],
                   ack[ack_index_w:ack_index_c],
                   ack[ack_index_c],
                   ack[ack_index_bitmap:ack_index_padding],
                   ack[ack_index_padding:])
