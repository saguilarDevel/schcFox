from Entities.Sigfox import SigfoxProfile
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

    @staticmethod
    def extract_data(foldername, stats_file, output, spreadsheet):
        import pandas as pd
        from math import ceil, isnan
        pd.set_option('display.max_columns', None)
        path = f"{foldername}/{stats_file}"
        current_experiment = int(stats_file[stats_file.rfind("_") + 1:stats_file.rfind(".")])
        current_column = 5 + current_experiment
        packet_size = int(stats_file[stats_file.find("_") + 1:stats_file.rfind("_")])
        fer = foldername[foldername.find("_") + 1:]
        sheet = spreadsheet[f'Case {packet_size} FER {fer}']
        sheet["E1"] = packet_size
        header_bytes = 1 if packet_size <= 300 else 2
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", header_bytes)
        fragments = ceil((packet_size * 8) / (profile.UPLINK_MTU - profile.HEADER_LENGTH))
        sheet["E2"] = fragments
        windows = ceil(fragments / profile.WINDOW_SIZE)
        sheet["E3"] = windows
        output.write(f"-------------- RESULTS FOR {foldername}/{stats_file} --------------\n\n")
        with open(path, encoding='ISO-8859-1') as json_file:
            data = json.load(json_file)
        assert data['fragments']
        df1 = pd.read_json(str(json.dumps(data['fragments'], sort_keys=True)))
        df1_transposed = df1.T  # or df1.transpose()
        print(df1_transposed)
        df1_transposed.astype({"RULE_ID": str,
                               "W": str,
                               "FCN": str,
                               "data": str,     # or bytes?
                               "fragment_size": int,
                               "abort": bool,
                               "sending_start": float,
                               "sending_end": float,
                               "send_time": float,
                               "downlink_enable": bool,
                               "timeout": int,
                               "ack_received": bool,
                               "ack": str,  # or bytes?
                               "rssi": int,
                               "receiver_abort_received": bool,
                               "receiver_abort_message": str,   # or bytes?
                               })
        df_nowait = df1_transposed[df1_transposed['downlink_enable'].isin([False])]
        output.write(f"Regular Fragments (nowait)\n"
                     # f"send_time =\n{df_nowait['send_time']}"
                     f"count: {df_nowait['send_time'].count()}\n"
                     f"sum: {df_nowait['send_time'].sum(axis=0, skipna=True)}\n"
                     f"mean: {df_nowait['send_time'].mean(axis=0, skipna=True)}\n"
                     f"std: {df_nowait['send_time'].std(axis=0, skipna=True)}\n"
                     f"\n")
        sheet.cell(row=6, column=current_column).value = df_nowait['send_time'].count()
        sheet.cell(row=8, column=current_column).value = df_nowait['send_time'].sum(axis=0, skipna=True)
        sheet.cell(row=9, column=current_column).value = df_nowait['send_time'].mean(axis=0, skipna=True)
        sheet.cell(row=10, column=current_column).value = df_nowait['send_time'].std(axis=0, skipna=True) if not isnan(
            df_nowait['send_time'].std(axis=0, skipna=True)) else 0
        df_wait = df1_transposed[df1_transposed['downlink_enable'].isin([True])]

        if len(df_wait[df_wait['RULE_ID'] == "00"]) != 0:
            df_all0 = df_wait[df_wait['FCN'].isin(['000'])]
            df_all1 = df_wait[df_wait['FCN'].isin(['111'])]
        else:
            df_all0 = df_wait[df_wait['FCN'].isin(['00000'])]
            df_all1 = df_wait[df_wait['FCN'].isin(['11111'])]
        output.write(f"Fragments - downlink requested - ALL 0\n"
                     f"data =\n{df_all0}\n"
                     f"send_time =\n{df_all0['send_time']}"
                     f"count: {df_all0['send_time'].count()}\n"
                     f"ul_errors: {df_all0[df_all0['ack_received'].isin([False])]['ack_received'].count()}\n"
                     f"all0_received: {df_all0[df_all0['ack_received'].isin([True])]['ack_received'].count()}\n"
                     f"sum: {df_all0['send_time'].sum(axis=0, skipna=True)}\n"
                     f"mean: {df_all0['send_time'].mean(axis=0, skipna=True)}\n"
                     f"std: {df_all0['send_time'].std(axis=0, skipna=True)}\n"
                     f"\n")
        sheet.cell(row=12, column=current_column).value = df_all0['send_time'].count()
        sheet.cell(row=13, column=current_column).value = df_all0[df_all0['ack_received'].isin([False])][
            'ack_received'].count()
        sheet.cell(row=15, column=current_column).value = df_all0[df_all0['ack_received'].isin([True])][
            'ack_received'].count()
        sheet.cell(row=16, column=current_column).value = df_all0['send_time'].sum(axis=0, skipna=True)
        sheet.cell(row=17, column=current_column).value = df_all0['send_time'].mean(axis=0, skipna=True) if not isnan(
            df_all0['send_time'].mean(axis=0, skipna=True)) else 0
        sheet.cell(row=18, column=current_column).value = df_all0['send_time'].std(axis=0, skipna=True) if not isnan(
            df_all0['send_time'].std(axis=0, skipna=True)) else 0
        output.write(f"Fragments - downlink requested - ALL 1\n"
                     f"data =\n{df_all1}\n"
                     f"send_time =\n{df_all1['send_time']}"
                     f"count: {df_all1['send_time'].count()}\n"
                     f"ul_errors: {df_all1[df_all1['ack_received'].isin([False])]['ack_received'].count()}\n"
                     f"all1_received: {df_all1[df_all1['ack_received'].isin([True])]['ack_received'].count()}\n"
                     f"sum: {df_all1['send_time'].sum(axis=0, skipna=True)}\n"
                     f"mean: {df_all1['send_time'].mean(axis=0, skipna=True)}\n"
                     f"std: {df_all1['send_time'].std(axis=0, skipna=True)}\n"
                     f"\n")
        sheet.cell(row=20, column=current_column).value = df_all1['send_time'].count()
        sheet.cell(row=21, column=current_column).value = df_all1[df_all1['ack_received'].isin([False])][
            'ack_received'].count()
        sheet.cell(row=23, column=current_column).value = df_all1[df_all1['ack_received'].isin([True])][
            'ack_received'].count()
        sheet.cell(row=24, column=current_column).value = df_all1['send_time'].sum(axis=0, skipna=True)
        sheet.cell(row=25, column=current_column).value = df_all1['send_time'].mean(axis=0, skipna=True)
        sheet.cell(row=26, column=current_column).value = df_all1['send_time'].std(axis=0, skipna=True) if not isnan(
            df_all1['send_time'].std(axis=0, skipna=True)) else 0
        # df1_transposed.to_excel('test_stats_2.2.xlsx', engine='xlsxwriter')
        output.write(
            f"Transmission Time (excluding code overhead): {df1_transposed['send_time'].sum(axis=0, skipna=True)}\n\n")
        sheet.cell(row=27, column=current_column).value = df1_transposed['send_time'].sum(axis=0, skipna=True)
