#!/usr/bin/python3

"""
SMTP Client written in Python
for sending e-mail in TCP/IP networks.
"""

# Product: PySMTP
# Copyright (C) 2015 LeMarck (https://github.com/LeMarck)
# Author: Petrov E.S.
# Contact: jeysonep@gmail.com

import argparse
import getpass
import os
import random
import socket
import ssl
import time
from struct import unpack
import sys
import re


__author__ = 'Evgeny Petrov'

__version__ = '1.6'


CRLF = b'\r\n'
ALPH = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"


def base_64(b_str):
    """

    :param b_str: - The input data
    :return:
    """
    if type(b_str) != bytes:
        b_str = b_str.encode()
    len_ = len(b_str)
    b64 = ''
    align = len_ % 3
    if align != 0:
        b_str += (3-align)*b'\x00'
    while len(b_str) != 0:
        int_ = unpack("BBB", b_str[:3])
        b_str = b_str[3:]
        bin_str = ''
        for i in int_:
            bin_lin = bin(i)[2:]
            bin_lin = (8-len(bin_lin))*'0' + bin_lin
            bin_str += bin_lin
        for i in range(4):
            b64 += ALPH[int(bin_str[i*6:(i+1)*6], 2)]
    if len_*8//6 != len(b64):
        control_len = len(b64) - (len_*8//6+1)
        b64 = b64[:-1*control_len] + control_len*"="
    return b64


class SMTP:
    """
    The class implements the SMTP Protocol for sending messages
    """
    def __init__(self, timeout=1, debug=False):
        self.timeout = timeout
        self.debug = debug
        self.boundary = self._boundary()
        self.pipelining = False
        self.bitmime = ''
        self.dsn = False

    def _boundary(self):
        boundary = ''
        random_ = random.Random()
        size = random_.randint(10, 20)
        for i in range(size):
            boundary += ALPH[random_.randint(0, 61)]
        return boundary

    def _create_connection(self, host, port):
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.settimeout(self.timeout)
        if port == 465:
            self.connection = ssl.wrap_socket(self.connection,
                                              ssl_version=ssl.PROTOCOL_SSLv23)
        self.connection.connect((host, port))
        answer = self.connection.recv(512)[:-2]
        if not answer:
            raise ConnectionAbortedError
        if self.debug:
            print(answer)

    def connect(self, host):
        self._create_connection(host, 25)

    def ssl_connect(self, host):
        self._create_connection(host, 465)

    def recv(self):
        self.answer = b''
        try:
            while True:
                answer = self.connection.recv(512)[:-2]
                if not answer:
                    break
                self.answer += answer + b'\n'
        except socket.timeout:
            if self.debug:
                print(self.answer.decode())
            else:
                pass

    def send(self, msg):
        self.connection.send(msg.encode() + CRLF)

    def request(self, msg):
        self.send(msg)
        self.recv()

    def getAnswer(self):
        return self.answer.decode()

    def ehlo(self):
        self.request('EHLO HI')
        if b'PIPELINING' in self.answer:
            self.pipelining = True
        if b'8BITMIME' in self.answer:
            self.bitmime = ' BODY=8BITMIME'
        if b'DSN' in self.answer:
            self.dsn = True

    def auth_login(self, addr, pass_=None):
        matcher = re.match(r'^(([\w.-_]+ )*)([\w.-_]+@[\w.]+)', addr)
        self.name = ''
        if matcher.group(1):
            self.name = '=?utf-8?B?{}?='.format(
                base_64(matcher.group(1)[:-1]))
        self.addr = matcher.group(3)
        if pass_:
            self.request("AUTH LOGIN")
            self.request(base_64(self.addr))
            self.request(base_64(pass_))

    def mail_from(self):
        if self.debug and self.dsn:
            self.bitmime += ' RET=HDRS ENVID={}'.format(self._boundary())
        self.request('MAIL FROM: {}<{}>{}'.format(self.name, self.addr,
                                                  self.bitmime))

    def rcpt_to(self, addr):
        dsn = ''
        if self.debug and self.dsn:
            dsn = ' NOTIFY=SUCCESS,FAILURE ORCPT=rfc822;{}'.format(addr)
        if self.pipelining:
            self.send('RCPT TO: <{}>{}'.format(addr, dsn))
        else:
            self.request('RCPT TO: <{}>{}'.format(addr, dsn))

    def data(self):
        self.request('DATA')

    def date(self):
        self.send('DATE: ' + time.strftime('%d %b %y %H:%M:%S'))

    def from_(self):
        self.send('FROM: {}<{}>'.format(self.name, self.addr))

    def to(self, addr):
        self.send('TO: <{}>'.format(addr))

    def sudject(self, theme):
        self.send('SUBJECT: =?utf-8?B?{}?='.format(base_64(theme)))

    def mime(self):
        self.send('MIME-Version: 1.0')
        self.send('Content-Type: multipart/mixed; '
                  'boundary={}; charset=utf-8'.format(self.boundary))

    def text(self, msg):
        self.send('--{}'.format(self.boundary))
        self.send('Content-Type: text/plain; charset=utf-8')
        self.send('Content-Transfer-Encoding: base64')
        self.send('')
        self.send(base_64(msg))

    def file(self, filename, data):
        self.send('--{}'.format(self.boundary))
        self.send('Content-Type: application/octet-stream; '
                  'name="{}";'.format(filename))
        self.send('Content-Transfer-Encoding: base64')
        self.send('Content-Disposition: attachment; '
                  'filename="{}";'.format(filename))
        self.send('')
        message = base_64(data)
        size = len(message)//1000
        for i in range(size):
            self.send(message[:1000])
            message = message[1000:]

    def end(self):
        self.send('--{}--'.format(self.boundary))
        self.request('.')

    def quit(self):
        self.request('QUIT')


def main(args):
    """

    :param args: - Date from Console
    :return:
    """
    smtp = SMTP(debug=args.debug)

    try:
        smtp.ssl_connect(args.host)
    except socket.timeout:
        smtp.connect(args.host)
    except Exception as e:
        smtp.connection.close()
        print(e)

    smtp.ehlo()

    if not args.not_login:
        addr = input('От: ')
        pass_ = getpass.getpass('Пароль: ')
        smtp.auth_login(addr, pass_)
        if not re.match(r'^235', smtp.getAnswer()):
            print("\nОшибка авторизации, попробуйте снова\n")
            smtp.quit()
            main(args)
    else:
        addr = input('От: ')
        smtp.auth_login(addr)

    smtp.mail_from()
    addresses = input('Кому: ')
    addresses = addresses.split(' ')
    for addr in addresses:
        while not re.match(r'[\d\w\.\-_]+@(.*)', addr):
            addr = input('{} изменить на: '.format(addr))
        smtp.rcpt_to(addr)

    theme = input('Тема: ')

    print('')
    message = ''
    while True:
        msg = input()
        if not msg:
            break
        message += msg + '\n'

    files = []
    while True:
        file = input('+')
        if not file:
            break
        if os.path.exists(file):
            if os.path.isdir(file):
                for f in os.listdir(file):
                    files.append('{}/{}'.format(file, f))
            else:
                files.append(file)

    if not message and not files:
        smtp.quit()
        sys.exit()

    smtp.data()
    smtp.date()
    smtp.from_()
    for addr in addresses:
        smtp.to(addr)
    smtp.sudject(theme)
    smtp.mime()

    if message:
        message += '\n\n-----\n' \
                   'Отправленно с помощью PySMTP\n' \
                   'https://github.com/LeMarck/smtp'
        smtp.text(message)

    if files:
        for f in files:
            with open(f, 'rb') as file:
                smtp.file(os.path.split(f)[1], file.read())

    smtp.end()
    if re.match(r'^250', smtp.getAnswer()):
        print('\nСообщение отправлено')
    smtp.quit()
    sys.exit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        usage='''%(prog)s [-h] [-nl] [-d] host\n
    От: [имя] e-mail
    Пароль: пароль              # не используется с флагом -nl
    Кому: e-mails               # через пробел
    Тема: тема

    [Текстовое_сообщение]       # двойное нажатие на Enter
    ...                         # переводит на следующий пункт

    +[Имя_файла]                # двойное нажатие на Enter
    +...                        # отправляет сообщение

!!! Пустые сообщения не отправляются
    ''',
        epilog='''(C) 2015 LeMarck (https://github.com/LeMarck)''',
        add_help=False)
    parser.add_argument('host', type=str, help='Имя SMTP-сервера, '
                                               'к которому вы подключаетесь')
    parser.add_argument("-nl", "--not-login", action='store_true',
                        help="Отключение авторизации")
    parser.add_argument("-d", "--debug", action='store_true',
                        help="Отладочный режим")
    parser.add_argument('-h', '--help', action='help', help='Справка')

    args = parser.parse_args()

    try:
        main(args)
    except KeyboardInterrupt:
        sys.exit("\n\nСоединение разорвано")
    except socket.timeout:
        pass
    except Exception as e:
        print(e)
