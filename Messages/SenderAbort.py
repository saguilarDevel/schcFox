from Messages.Header import Header


class SenderAbort:
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
                             fcn="1"*profile.N,
                             c="")

        while len(self.header.string + self.padding) < profile.MTU:
            self.padding += '0'
