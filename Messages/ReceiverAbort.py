from Messages.ACK import ACK


class ReceiverAbort(ACK):

    def __init__(self, profile, header):
        rule_id = header.RULE_ID
        dtag = header.DTAG
        w = header.W

        padding = ''
        # if the Header does not end at an L2 Word boundary,
        # append bits set to 1 as needed to reach the next L2 Word boundary.
        while len(rule_id + dtag + w + '1' + padding) % profile.L2_WORD_SIZE != 0:
            padding += '1'

        # append exactly one more L2 Word with bits all set to ones.
        padding += '1' * profile.L2_WORD_SIZE

        super().__init__(profile, rule_id, dtag, w, c='1', bitmap='', padding=padding)
