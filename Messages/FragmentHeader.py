from Entities.exceptions import LengthMismatchError
from Messages.Header import Header


class FragmentHeader(Header):
    FCN = ''

    def __init__(self, profile, rule_id, dtag, w, fcn):
        super().__init__(profile, rule_id, dtag, w)

        if len(fcn) != profile.N:
            raise LengthMismatchError("FCN must be of length N")
        else:
            self.FCN = fcn

    def to_string(self):
        return "".join([super().to_string(), self.FCN])
