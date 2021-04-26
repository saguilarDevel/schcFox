import json

logfilename = ''


def init_logging(logfile):
    global logfilename
    logfilename = logfile
    with open(logfile, 'w') as f:
        f.write("====START LOGGING====\n\n")


def log_debug(text):
    global logfilename
    print(text)
    with open(logfilename, 'w') as f:
        f.write("[DEBUG] {}\n".format(text))


def log_info(text):
    global logfilename
    print(text)
    with open(logfilename, 'w') as f:
        f.write("[INFO] {}\n".format(text))


def log_warning(text):
    global logfilename
    print(text)
    with open(logfilename, 'w') as f:
        f.write("[WARNING] {}\n".format(text))


def log_error(text):
    global logfilename
    print(text)
    with open(logfilename, 'w') as f:
        f.write("[ERROR] {}\n".format(text))


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
