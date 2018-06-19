#!/usr/bin/python3


import base64
import quopri


def lazy_split(string, seps=(" ", "\t")):
    while True:
        min_sep_pos = 10 ** 8
        for sep in seps:
            sep_pos = string.find(sep)
            if sep_pos != -1 and sep_pos < min_sep_pos:
                min_sep_pos = sep_pos
        if min_sep_pos != 10 ** 8:
            yield string[:min_sep_pos]
            try:
                while string[min_sep_pos] in seps:
                    min_sep_pos += 1
            except IndexError:
                break
            string = string[min_sep_pos:]
        else:
            break
    yield string


def field_from_encoding(field):
    try:
        if field[0] == field[-1] == '"':
            field = field[1:-1]
        field = field.strip()
        if field.startswith("=?") and field.endswith("?="):
            field = field.split("?")
            if field[2].lower() == "b":
                decode_field = base64.b64decode
            else:
                decode_field = quopri.decodestring
            return decode_field(field[3]).decode(field[1].lower())
    except Exception:
        pass
    return field


if __name__ == '__main__':
    pass

