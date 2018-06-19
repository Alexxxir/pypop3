#!/usr/bin/python3

import socket
import ssl
import sys
import argparse
import getpass
from parser_mail import Mail
import os
import base64
import random


class IncorrectAnswer(Exception):
    pass


def create_parser():
    parser = argparse.ArgumentParser(
        description="Клиент для получения почты по pop3"
    )
    parser.add_argument("email", help="Логин", nargs='?')
    parser.add_argument("password", help="Пароль", nargs='?')
    return parser.parse_args()


def send(sock, command, error="", message_len=-1):
    sock.sendall(b"%s\n" % command.encode())
    data = b""
    if message_len == -1:
        data = sock.recv(1024)
    else:
        try:
            while True:
                data += sock.recv()
                if data.endswith(b"\r\n.\r\n"):
                    break
        except Exception:
            raise IncorrectAnswer(error)
    if not data:
        raise IncorrectAnswer(error)
    if data.startswith(b"-ERR"):
        raise IncorrectAnswer(error + "\n" + data.decode())
    return data.decode()


def output_headers(i, letter):
    print("Номер: ", i)
    print("Отправитель: ", letter.from_)
    print("Кому: ", letter.to)
    print("Тема: ", letter.subject)
    print("Дата: ", letter.date)


def output_all_headers(count):
    for i in range(count):
        letter = Mail.mail_parser(send(
            sock, "TOP %s 0" % str(i + 1), message_len=1))
        output_headers(i + 1, letter)
        print("—————————————————————————————————————")


def output_message(num):
    mail = Mail.mail_parser(send(sock, "RETR %s" % str(num), message_len=1))
    output_headers(num, mail)
    print("Текст письма:")
    print(mail.get_text())
    print("\n")
    records = mail.get_all_records()
    if len(records) >= 1:
        ask = input("Письмо содержит %d вложений, загрузить в "
                    "текущую директорию?(y/n): " % len(records))
        if ask.lower() in {"y", "yes", "да", ''}:
            if not os.path.exists("investments"):
                os.mkdir("investments")
            for record in records:
                if not record.name:
                    record.name = "file"
                record.name = record.name.split("/")[-1]
                while os.path.exists(
                        "investments/%s" % record.name.split("/")[-1]):
                    record.name += str(random.randint(0, 10))
                with open("investments/%s" % record.name, "wb") as file:
                    file.write(base64.b64decode(record.data.encode()))
                    print("Файл %s сохранён" % record.name)
    print("—————————————————————————————————————")


if __name__ == '__main__':
    parser = create_parser()
    if not parser.email:
        parser.email = input("Логин: ")
    if not parser.password:
        parser.password = getpass.getpass('Пароль: ')
    sock = None
    try:
        sock = socket.socket()
        sock.connect(("pop.yandex.ru", 995))
        sock = ssl.wrap_socket(sock, ssl_version=ssl.PROTOCOL_SSLv23)
        sock.recv(100)
        send(sock, "USER %s" % parser.email)
        send(sock, "PASS %s" % parser.password, "Неправильный логин или пароль")
        count_messages = int(send(sock, "STAT").split()[1])
        print("У вас %d писем" % count_messages)
        print("0 - вывести заголовки всех сообщений")
        print("[1-%d] - показать сообщение с указанным номером" % count_messages)
        print("end, exit, e, close - выйти\n")
        while True:
            while True:
                command = input("Введите команду: ")
                try:
                    command = int(command)
                except ValueError:
                    if command in {"end", "exit", "e", "close"}:
                        sys.exit(0)
                    print("Введите число\n")
                    continue
                if command > count_messages or command < 0:
                    print("Введите число в диапозоне [0-%d]" % count_messages)
                    continue
                break
            if command == 0:
                output_all_headers(count_messages)
            else:
                output_message(command)
    except IncorrectAnswer as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    except socket.error as e:
        print(f"Не удалось подключиться, {e}", file=sys.stderr)
        sys.exit(2)
    finally:
        if sock:
            sock.close()
