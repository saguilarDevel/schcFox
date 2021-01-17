# define Python user-defined exceptions
class Error(Exception):
    """Base class for other exceptions"""
    pass


class SCHCReceiverAbortReceived(Error):
    """Raised when the SCHC Receiver Abort is Received"""
    pass