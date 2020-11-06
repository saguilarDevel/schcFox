class ACK:

    profile = None
    rule_id = None
    dtag = None
    w = None
    bitmap = None
    c = None
    header = ''
    padding = bytes(0)

    def __init__(self, profile, rule_id, dtag, w, bitmap, c):
        self.profile = profile
        # self.header = Header(profile, message.header.RULE_ID, message.header.DTAG.zfill(2), message.header.W[-1],
        # fcn="", c="0")		# [-1]: the least significant bit

        self.rule_id = rule_id
        self.dtag = dtag
        self.w = w
        self.bitmap = bitmap
        self.c = c

        self.header = bytearray((self.rule_id + self.dtag + self.w + self.c + self.bitmap).encode())

        # print("Applying padding for ACK...")
        # print(profile.MTU)

        while len(self.header + self.padding) < profile.MTU:
            # print(len(self.header + self.padding))
            self.padding += bytes(0)

        # print("ACK is now " + str(len(self.header + self.padding)) + " bits long")


    def to_bytes(self):
        return self.header + self.padding
