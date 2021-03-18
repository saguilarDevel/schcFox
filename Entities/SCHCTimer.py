from machine import Timer


class SCHCTimer:
    timeout = None

    def __init__(self, timeout):
        self.timeout = timeout

    def set_timeout(self, new_timeout):
        self.timeout = new_timeout

    def wait(self, timeout=None):
        if timeout:
            self.timeout = timeout
        chrono = Timer.Chrono()
        chrono.start()
        while True:
            if chrono.read() >= self.timeout:
                chrono.stop()
                return
