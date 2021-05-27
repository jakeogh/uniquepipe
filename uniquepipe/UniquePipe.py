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

import binascii
import hashlib
from pathlib import Path

import numpy
from hasher import rhash_file
from pyphash import hash_pdqhash

try:
    from icecream import ic  # https://github.com/gruns/icecream
except ImportError:
    import sys

    def eprint(*args, **kwargs):
        if 'file' in kwargs.keys():
            kwargs.pop('file')
        print(*args, file=sys.stderr, **kwargs)
    ic = eprint


def generate_truncated_string_hash(*,
                                   string: str,
                                   length: int,
                                   algorithm: str,
                                   verbose: bool,
                                   debug: bool,
                                   accept_empty: bool = False,
                                   ):
    string = str(string)  # todo
    assert algorithm is not None
    if not accept_empty:
        if len(string) == 0:
            raise ValueError('empty string')
    #if not isinstance(string, str):
    #    msg = "string must be type str, not type <{}>".format(type(string))
    #    raise TypeError(msg)
    #ic(algorithm)
    byte_string = string.encode('UTF-8')
    digest = getattr(hashlib, algorithm)(byte_string).digest()
    #hexdigest = digest.hex()
    #return hexdigest[0:length - 1]  # for sha3_256 this was cutting it in half from 256 to 128 if length == 32
    return digest[0:length - 1]


def generate_truncated_file_hash(*,
                                 string: str,
                                 length: int,
                                 algorithm: str,
                                 verbose: bool,
                                 debug: bool,
                                 accept_empty: bool = False,
                                 ):

    hexdigest = rhash_file(path=string,
                           algorithm=algorithm,
                           verbose=verbose,
                           debug=debug,)

    digest = binascii.unhexlify(hexdigest)
    return digest[0:length - 1]


def generate_truncated_pdqhash(*,
                               string: Path,
                               length: int,
                               algorithm: str,
                               verbose: bool,
                               debug: bool,
                               accept_empty: bool = False,
                               ):

    digest = hash_pdqhash(path=string,
                          rotations=False,  # todo
                          verbose=verbose,
                          debug=debug,)

    return digest[0:length - 1]


class UniquePipe():
    def __init__(self, *,
                 verbose: bool,
                 debug: bool,
                 accept_empty: bool,
                 paths: bool,
                 length: int = 32,
                 algorithm: str = 'sha3_256',):
        self.hashes = set()
        self.length = length
        self.algorithm = algorithm
        self.verbose = verbose
        self.debug = debug
        self.accept_empty = accept_empty
        if algorithm == 'pdqhash':
            assert paths
            self.algorithm_function = generate_truncated_pdqhash
        else:
            if paths:
                self.algorithm_function = generate_truncated_file_hash
            else:
                self.algorithm_function = generate_truncated_string_hash

    def filter(self, string):
        string_hash = self.algorithm_function(string=string,
                                              length=self.length,
                                              algorithm=self.algorithm,
                                              accept_empty=self.accept_empty,
                                              verbose=self.verbose,
                                              debug=self.debug,)
        if self.debug:
            ic(string_hash)
        if string_hash not in self.hashes:
            self.hashes.add(string_hash)
            return string_hash
        return None

    def remove(self, string):  # .pop() returns arb element
        string_hash = self.algorithm_function(string=string,
                                              length=self.length,
                                              algorithm=self.algorithm,
                                              accept_empty=self.accept_empty,
                                              verbose=self.verbose,
                                              debug=self.debug,)
        if self.verbose:
            ic(string_hash)
        self.hashes.remove(string_hash)

    def add(self, string):
        string_hash = self.algorithm_function(string=string,
                                              length=self.length,
                                              algorithm=self.algorithm,
                                              accept_empty=self.accept_empty,
                                              verbose=self.verbose,
                                              debug=self.debug,)
        if self.verbose:
            ic(string_hash)
        self.hashes.add(string_hash)

    def exists(self, string):
        string_hash = self.algorithm_function(string=string,
                                              length=self.length,
                                              algorithm=self.algorithm,
                                              accept_empty=self.accept_empty,
                                              verbose=self.verbose,
                                              debug=self.debug,)
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
