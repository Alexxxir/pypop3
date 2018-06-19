#!/usr/bin/python3


import base64


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


def field_from_base64(field):
    try:
        if field[0] == field[-1] == '"':
            field = field[1:-1]
        if field.strip().lower().startswith("=?utf-8?"):
            return base64.b64decode(field[10:-2]).decode()
    except Exception:
        pass
    return field


if __name__ == '__main__':
    pass

