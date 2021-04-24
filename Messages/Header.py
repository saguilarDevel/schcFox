from Entities.exceptions import LengthMismatchError


class Header:
    PROFILE = None
    RULE_ID = ""
    DTAG = ""
    W = ""
    WINDOW_NUMBER = None

    def __init__(self, profile, rule_id, dtag, w):
        self.profile = profile

        if len(rule_id) != profile.RULE_ID_SIZE:
            raise LengthMismatchError("RULE must be of length RULE_ID_SIZE")
        else:
            self.RULE_ID = rule_id

        if profile.T == "0":
            self.DTAG = ""
        elif len(dtag) != profile.T:
            raise LengthMismatchError("DTAG must be of length T")
        else:
            self.DTAG = dtag

        if len(w) != profile.M:
            raise LengthMismatchError("W must be of length M")
        else:
            self.W = w
            self.WINDOW_NUMBER = int(self.W, 2)

    def to_string(self):
        return "".join([self.RULE_ID, self.DTAG, self.W])

    def to_bytes(self):
        s = self.to_string()
        return bytes(int(s[i:i + 8], 2) for i in range(0, len(s), 8))
