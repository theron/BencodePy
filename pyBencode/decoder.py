__author__ = 'eric.weast'

from pyBencode.exceptions import DecodingError
import collections


class Decoder:
    def __init__(self, data):

        self.tokens = {
            b'd': self.__parse_dict,
            b'l': self.__parse_list,
            b'i': self.__parse_int,
            b'e':  self.__parse_terminator
        }

        self.view = memoryview(data)
        self.length = len(data)
        self.idx = 0

        self.decoded_dict = collections.OrderedDict()
        self.active_targets = list()
        self.current_key = None

    def __read(self, i):
        b = self.view[self.idx: self.idx + i].tobytes()
        self.idx += i
        if self.idx > self.length:
            raise DecodingError('Unexpected EOF.')
        return b

    @property
    def __current_target(self):
        return self.active_targets[-1]

    def __new_target(self, obj):
        self.active_targets.append(obj)

    def decode(self) -> collections.OrderedDict:
        while self.idx < self.length:
            char = self.__read(1)
            if char.decode('utf-8').isdigit():
                self.__parse_str(char)
            elif char in self.tokens:
                self.tokens[char].__call__()
            else:
                raise DecodingError('Invalid token character at position ' + str(self.idx) + '.')
        return self.decoded_dict

    def __parse_dict(self):
        if not self.active_targets:
            self.active_targets.append(self.decoded_dict)
        elif isinstance(self.__current_target, dict):
            if self.current_key:
                key_name = self.current_key
            else:
                raise DecodingError('Internal error at __parse_dict(self) for token at index ' + str(self.idx) + '.')
            self.__current_target[key_name] = collections.OrderedDict()
            self.__new_target(self.__current_target[key_name])
            self.current_key = None
        elif isinstance(self.__current_target, list):
            d = collections.OrderedDict()
            self.__current_target.append(d)
            self.__new_target(d)
        else:
            raise DecodingError('Internal error at __parse_dict(self) for token at index ' + str(self.idx) + '.')

    def __parse_list(self):
        if isinstance(self.__current_target, dict):
            if self.current_key:
                key_name = self.current_key
            else:
                raise DecodingError('Invalid dictionary key name at index ' + str(self.idx) + '.')
            self.__current_target[key_name] = list()
            self.__new_target(self.__current_target[key_name])
            self.current_key = None
        elif isinstance(self.__current_target, list):
            self.__new_target(list())
        else:
            raise DecodingError('Internal error at __parse_list(self) for token at index ' + str(self.idx) + '.')

    def __parse_terminator(self):
        try:
            self.active_targets.pop()
        except IndexError:
            raise DecodingError('Invalid terminator token ("e") at index ' + str(self.idx) + '.')

    def __parse_str(self, char):
        frame = char
        while True:
            b = self.__read(1)
            if b':' not in b:
                frame += b
            else:
                break
        string = self.__read(int(frame))
        self.__add_data(string)

    def __parse_int(self):
        frame = b''
        while True:
            b = self.__read(1)
            if b'e' not in b:
                frame += b
            else:
                break
        self.__add_data(int(frame))

    def __add_data(self, val):
        if isinstance(self.__current_target, dict):
            self.__append_dict(val)
        elif isinstance(self.__current_target, list):
            self.__append_list(val)

    def __append_list(self, data):
        self.__current_target.append(data)

    def __append_dict(self, value):
        if self.current_key:
            self.__current_target[self.current_key] = value
            self.current_key = None
        else:
            self.current_key = value


def decode_from_file(path: str):
    with open('path', 'rb') as f:
        b = f.read()
    decoder = Decoder(b)
    return decoder.decode()


def decode(data: bytes):
    decoder = Decoder(data)
    return decoder.decode()