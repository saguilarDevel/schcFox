from Messages.Header import Header

def bitstring_to_bytes(s):
    return int(s, 2).to_bytes((len(s) + 7) // 8, byteorder='big')

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
        
        print(self.header.string + self.padding)

    def to_string(self):
        return self.header.string + self.padding

    def to_bytes(self):
        bitstring = self.header.string + self.padding
        abort_bytes = bytearray(0)
        for i in range(0,len(bitstring)/8):
            abort_bytes.append(int(bitstring[i*8:(i*8)+8],2))
        return abort_bytes
        