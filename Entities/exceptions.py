class SCHCError(Exception):
    pass


class LengthMismatchError(SCHCError):
    pass


class SCHCTimeoutError(SCHCError):
    pass


class RuleSelectionError(SCHCError):
    print("ERROR: The SCHC packet cannot be fragmented in 2 ** M * WINDOW_SIZE fragments or less. A Rule ID cannot be "
          "selected.")
    pass


class SenderAbortError(SCHCError):
    pass


class ReceiverAbortError(SCHCError):
    pass


class UnrequestedACKError(SCHCError):
    pass


class BadProfileError(SCHCError):
    pass


class NetworkDownError(SCHCError):
    pass
