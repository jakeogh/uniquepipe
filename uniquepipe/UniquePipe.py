#!/usr/bin/env python3

# pylint: disable=C0111  # docstrings are always outdated and wrong
# pylint: disable=W0511  # todo is encouraged
# pylint: disable=C0301  # line too long
# pylint: disable=R0902  # too many instance attributes
# pylint: disable=C0302  # too many lines in module
# pylint: disable=C0103  # single letter var names, func name too descriptive
# pylint: disable=R0911  # too many return statements
# pylint: disable=R0912  # too many branches
# pylint: disable=R0915  # too many statements
# pylint: disable=R0913  # too many arguments
# pylint: disable=R1702  # too many nested blocks
# pylint: disable=R0914  # too many local variables
# pylint: disable=R0903  # too few public methods
# pylint: disable=E1101  # no member for base
# pylint: disable=W0201  # attribute defined outside __init__
# pylint: disable=R0916  # Too many boolean expressions in if statement

import hashlib

try:
    from icecream import ic  # https://github.com/gruns/icecream
except ImportError:
    import sys

    def eprint(*args, **kwargs):
        if 'file' in kwargs.keys():
            kwargs.pop('file')
        print(*args, file=sys.stderr, **kwargs)
    ic = eprint


def generate_truncated_string_hash(string: str,
                                   length: int,
                                   algorithm: str,
                                   verbose: bool,
                                   debug: bool,):
    string = str(string)  # todo
    #if not isinstance(string, str):
    #    msg = "string must be type str, not type <{}>".format(type(string))
    #    raise TypeError(msg)
    byte_string = string.encode('UTF-8')
    digest = getattr(hashlib, algorithm)(byte_string).digest()
    hexdigest = digest.hex()
    return hexdigest[0:length - 1]


class UniquePipe():
    def __init__(self,
                 length: str = 32,
                 algorithm: str = 'sha3_256',
                 verbose=False,):
        self.hashes = set()
        self.length = length
        self.algorithm = algorithm
        self.verbose = verbose

    def filter(self, string):
        string_hash = generate_truncated_string_hash(string=string,
                                                     length=self.length,
                                                     algorithm=self.algorithm,
                                                     verbose=self.verbose,
                                                     debug=self.debug,)
        if self.verbose:
            ic(string_hash)
        if string_hash not in self.hashes:
            self.hashes.add(string_hash)
            return True
        return False

    def remove(self, string):  # .pop() returns arb element
        string_hash = generate_truncated_string_hash(string=string,
                                                     length=self.length,
                                                     algorithm=self.algorithm,)
        if self.verbose:
            ic(string_hash)
        self.hashes.remove(string_hash)

    def add(self, string):
        string_hash = generate_truncated_string_hash(string=string,
                                                     length=self.length,
                                                     algorithm=self.algorithm,)
        if self.verbose:
            ic(string_hash)
        self.hashes.add(string_hash)

    def exists(self, string):
        string_hash = generate_truncated_string_hash(string=string,
                                                     length=self.length,
                                                     algorithm=self.algorithm,)
        if self.verbose:
            ic(string_hash)
        if string_hash in self.hashes:
            return True
        return False

    def __sizeof__(self):
        return len(self) * self.length

    def __len__(self):
        return len(self.hashes)

    def __contains__(self, match):
        if self.exists(match):
            return True
        return False
