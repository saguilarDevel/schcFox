import json

from Entities.SigfoxProfile import SigfoxProfile
from schc_utils import *


class SCHCLogger:
    FILENAME = None
    JSON_FILE = None
    TOTAL_SIZE = None
    CHRONO = None
    LAPS = []
    FRAGMENTS_INFO_ARRAY = []
    FRAGMENTATION_TIME = None
    START_SENDING_TIME = None
    END_SENDING_TIME = None
    LOGGING_TIME = None
    FINISHED = False

    def __init__(self, filename, json_file):
        from network import Sigfox
        import socket as s
        from machine import Timer

        self.FILENAME = filename
        self.JSON_FILE = json_file
        self.TOTAL_SIZE = 0
        self.CHRONO = Timer.Chrono()
        self.CHRONO.start()
        self.LOGGING_TIME = 0
        self.LAPS = []
        self.FRAGMENTS_INFO_ARRAY = []
        self.FRAGMENTATION_TIME = 0
        self.START_SENDING_TIME = 0
        self.END_SENDING_TIME = 0
        self.LOGGING_TIME = 0
        self.FINISHED = False

        # with open(self.FILENAME, 'a') as f:
        #     f.write("====START LOGGING====\n\n")

    def debug(self, text):
        print(self, "[DEBUG] {}".format(text))

        # t_i = 0

        # if self.START_SENDING_TIME is not None and self.END_SENDING_TIME is None:
        #     t_i = self.CHRONO.read()

    #
    # with open(self.FILENAME, 'a') as f:
    #     f.write("[DEBUG] {}\n".format(text))
    #
    # if self.START_SENDING_TIME is not None and self.END_SENDING_TIME is None:
    #     t_f = self.CHRONO.read()
    #     self.LOGGING_TIME += t_f - t_i

    def info(self, text):
        print(self, "[INFO] {}".format(text))

        # t_i = 0

    #
    # if self.START_SENDING_TIME is not None and self.END_SENDING_TIME is None:
    #     t_i = self.CHRONO.read()
    #
    # with open(self.FILENAME, 'a') as f:
    #     f.write("[INFO] {}\n".format(text))
    #
    # if self.START_SENDING_TIME is not None and self.END_SENDING_TIME is None:
    #     t_f = self.CHRONO.read()
    #     self.LOGGING_TIME += t_f - t_i

    def warning(self, text):
        print(self, "[WARNING] {}".format(text))

        # t_i = 0

        # if self.START_SENDING_TIME is not None and self.END_SENDING_TIME is None:
        #     t_i = self.CHRONO.read()

        # with open(self.FILENAME, 'a') as f:
        #     f.write("[WARNING] {}\n".format(text))

        # if self.START_SENDING_TIME is not None and self.END_SENDING_TIME is None:
        #     t_f = self.CHRONO.read()
        #     self.LOGGING_TIME += t_f - t_i

    def error(self, text):
        print(self, "[ERROR] {}".format(text))

        # t_i = 0

        # if self.START_SENDING_TIME is not None and self.END_SENDING_TIME is None:
        #     t_i = self.CHRONO.read()

        # with open(self.FILENAME, 'a') as f:
        #     f.write("[ERROR] {}\n".format(text))

        # if self.START_SENDING_TIME is not None and self.END_SENDING_TIME is None:
        #     t_f = self.CHRONO.read()
        #     self.LOGGING_TIME += t_f - t_i

    def save(self):
        self.debug('Stats')
        self.debug("Writing to file {}".format(self.JSON_FILE))

        with open(self.JSON_FILE, "w") as j:
            results_json = {}
            for index, fragment in enumerate(self.FRAGMENTS_INFO_ARRAY):
                if fragment['downlink_enable'] and not fragment['receiver_abort_received']:
                    self.debug('{} - W:{}, FCN:{}, TT:{}s, '
                               'DL(E):{}, ack(R):{}'.format(index,
                                                            fragment['W'],
                                                            fragment['FCN'],
                                                            fragment['send_time'],
                                                            fragment['downlink_enable'],
                                                            fragment['ack_received']))
                elif fragment['abort']:
                    self.debug('{} - W:{}, FCN:{}, TT:{}s, '
                               'SCHC Sender Abort '.format(index,
                                                           fragment['W'],
                                                           fragment['FCN'],
                                                           fragment['send_time'],
                                                           fragment['downlink_enable'],
                                                           fragment['ack_received']))
                elif fragment['receiver_abort_received']:
                    self.debug('{} - W:{}, FCN:{}, TT:{}s, DL(E):{}, ack(R):{} '
                               'SCHC Receiver Abort '.format(index,
                                                             fragment['W'],
                                                             fragment['FCN'],
                                                             fragment['send_time'],
                                                             fragment['downlink_enable'],
                                                             fragment['ack_received']))
                else:
                    self.debug('{} - W:{}, FCN:{}, TT:{}s'.format(index,
                                                                  fragment['W'],
                                                                  fragment['FCN'],
                                                                  fragment['send_time']))

                results_json["{}".format(index)] = fragment

            self.debug("TT: Transmission Time, DL (E): Downlink enable, ack (R): ack received")

            total_transmission_results = {'fragments': results_json,
                                          'fragmentation_time': self.FRAGMENTATION_TIME,
                                          'total_transmission_time': self.END_SENDING_TIME - self.START_SENDING_TIME - self.LOGGING_TIME,
                                          'total_number_of_fragments': len(self.FRAGMENTS_INFO_ARRAY),
                                          'payload_size': self.TOTAL_SIZE,
                                          'tx_status_ok': self.FINISHED}

            self.debug("fragmentation time: {}".format(self.FRAGMENTATION_TIME))
            self.debug(
                "total sending time: {}".format(self.END_SENDING_TIME - self.START_SENDING_TIME - self.LOGGING_TIME))
            self.debug("total number of fragments sent: {}".format(len(self.FRAGMENTS_INFO_ARRAY)))
            self.debug('tx_status_ok: {}'.format(self.FINISHED))
            # print("total_transmission_results:{}".format(total_transmission_results))
            j.write(json.dumps(total_transmission_results))
