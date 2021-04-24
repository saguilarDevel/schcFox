import json
import logging as log


def init_logging(logfile):
    log.basicConfig(filename=logfile,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=log.DEBUG)


def log_debug(text):
    print(text)
    log.debug(text)


def log_info(text):
    print(text)
    log.info(text)


def log_warning(text):
    print(text)
    log.warning(text)


def log_error(text):
    print(text)
    log.error(text)


def zfill(string, width):
    if len(string) < width:
        return ("0" * (width - len(string))) + string
    else:
        return string


def insert_index(ls, pos, elmt):
    while len(ls) < pos:
        ls.append([])
    ls.insert(pos, elmt)


def replace_bit(string, position, value):
    return '%s%s%s' % (string[:position], value, string[position + 1:])


def find(string, character):
    return [i for i, ltr in enumerate(string) if ltr == character]


def bitstring_to_bytes(s):
    return int(s, 2).to_bytes(len(s) // 8, byteorder='big')


def is_monochar(s):
    return len(set(s)) == 1


def send_ack(request, ack):
    device = request["device"]
    print(f"ack string -> {ack.to_string()}")
    response_dict = {device: {'downlinkData': ack.to_bytes().hex()}}
    response_json = json.dumps(response_dict)
    print(f"response_json -> {response_json}")
    return response_json
