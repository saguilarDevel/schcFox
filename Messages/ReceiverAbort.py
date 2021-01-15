from Messages.Header import Header


class ReceiverAbort:
    profile = None
    header_length = 0
    rule_id_size = 0
    t = 0
    n = 0
    window_size = 0

    header = None
    padding = ''

    def __init__(self, profile, rule_id, dtag, w):
        self.profile = profile

        self.header = Header(profile=profile,
                             rule_id=rule_id,
                             dtag=dtag,
                             w=w,
                             fcn='',
                             c='1')

        # if the Header does not end at an L2 Word boundary, append bits set to 1 as needed to reach the next L2 Word boundary.
        while len(self.header.string + self.padding) % profile.L2_WORD_SIZE != 0:
            self.padding += '1'

        # append exactly one more L2 Word with bits all set to ones.
        self.padding += '1'*profile.L2_WORD_SIZE
