from util import lazy_split, field_from_base64
import base64


class Record:
    def __init__(self):
        self.content_type = None
        self.name = None
        self.encoding = None
        self.data = ""
        self.charset = None
        self.boundary = None
        self.records = []

    def get_text(self):
        result = ""
        if self.content_type.startswith("text"):
            if self.encoding == "base64":
                self.data = base64.b64decode(self.data).decode()
            return self.data
        for record in self.records:
            result = record.get_text()
            if result:
                return result
        return result

    def get_records(self):
        if (self.content_type.startswith("image") or
                self.content_type.endswith("octet-stream")):
            yield self
        for record in self.records:
            for r in record.get_records():
                yield r

    def parse_record(self, message, end):
        if not end:
            end = "."
        if self.content_type.startswith("multipart"):
            self.boundary = self.boundary.strip('"').rstrip('"').strip(';').rstrip(';')
            self.boundary = "--%s" % self.boundary
            line = next(message)
            while not line.startswith(self.boundary):
                line = next(message)
            while True:
                line = next(message)
                if line == end:
                    return
                field = lazy_split(line)
                field_type = next(field)
                new_record = Record()
                while True:
                    if field_type.lower() == "content-type:":
                        new_record.content_type = next(field).strip(";")
                        if new_record.content_type.startswith(
                                "multipart"):
                            new_record.boundary = next(field).split("=")[
                                                            1][1:-1]
                    if field_type.lower() == "content-transfer-encoding:":
                        new_record.encoding = next(field)
                    if field_type.lower() == "content-disposition:":
                        next(field)
                        new_record.name = field_from_base64(
                            next(field).split("=")[1].strip('"').rstrip('"'))
                    line = next(message)
                    if line == end:
                        return
                    if line == "":
                        break
                    field = lazy_split(line)
                    field_type = next(field)
                self.records.append(new_record)
                self.records[-1].parse_record(message, self.boundary)
        elif self.content_type.startswith("text"):
            while True:
                line = next(message)
                if (line.startswith(end) and end != ".") or (line == end and end == "."):
                    return
                self.data += line + "\n"
        else:
            while True:
                line = next(message)
                if line.startswith(end):
                    return
                self.data += line


class Mail:
    def __init__(self):
        self.date = ""
        self.subject = ""
        self.record = None
        self.sender = ""
        self.from_ = ""
        self.to = ""

    def get_text(self):
        result = ""
        for line in lazy_split(self.record.get_text(), ("\n",)):
            line = line.strip().rstrip()
            result += line + "\n"
        if result[:len(result) // 2] == result[len(result) // 2:]:
            result = result[:len(result) // 2]
        return result

    def get_all_records(self):
        return list(self.record.get_records())

    @staticmethod
    def split_message(message):
        last = None
        for line in map(lambda s: s[:-1], lazy_split(message, ("\n",))):
            if not line:
                if last != None:
                    yield last
                last = line
            elif line[0] == " " or line[0] == "\t":
                last += line
            else:
                if last != None:
                    yield last
                last = line
        yield last

    @staticmethod
    def mail_parser(message):
        mail = Mail()
        message = Mail.split_message(message)
        mail.record = Record()
        try:
            line = next(message)
            while line != "":
                field = lazy_split(line)
                field_type = next(field)
                if field_type.lower() == "return-path:":
                    mail.sender = " ".join(map(field_from_base64, field))
                elif field_type.lower() == "from:":
                    mail.from_ = " ".join(map(field_from_base64, field))
                elif field_type.lower() == "date:":
                    mail.date = " ".join(map(field_from_base64, field))
                elif field_type.lower() == "subject:":
                    mail.subject = " ".join(map(field_from_base64, field))
                elif field_type.lower() == "to:":
                    mail.to = " ".join(map(field_from_base64, field))
                elif field_type.lower() == "content-transfer-encoding:":
                    mail.record.encoding = next(field)
                elif field_type.lower() == "content-type:":
                    content_type = next(field)
                    if mail.record or content_type.startswith("text"):
                        if not mail.record:
                            mail.record = Record()
                            mail.record.content_type = "text"
                    mail.record.content_type = content_type.strip(";")
                    if mail.record.content_type.startswith("multipart"):
                        mail.record.boundary = next(field).split("=")[1]
                line = next(message)
            if not mail.record:
                mail.record = Record()
                mail.record.content_type = "text"
            mail.record.parse_record(message, mail.record.boundary)
        except (StopIteration, TypeError):
            pass
        return mail

