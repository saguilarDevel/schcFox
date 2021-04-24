from Entities.exceptions import LengthMismatchError
from Messages.Header import Header


class ACKHeader(Header):
    C = ""

    def __init__(self, profile, rule_id, dtag, w, c):
        super().__init__(profile, rule_id, dtag, w)

        if len(c) != 1:
            raise LengthMismatchError("C bit must be of length 1")
        self.C = c

    def to_string(self):
        return "".join([super().to_string(), self.C])
