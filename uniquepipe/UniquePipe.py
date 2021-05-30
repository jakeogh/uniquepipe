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
import sys
from pathlib import Path

import numpy
from bitstring import BitArray
from hasher import rhash_file


def eprint(*args, **kwargs):
    if 'file' in kwargs.keys():
        kwargs.pop('file')
    print(*args, file=sys.stderr, **kwargs)


try:
    from icecream import ic  # https://github.com/gruns/icecream
except ImportError:
    ic = eprint



def hamming_distance(a, b, *,
                     verbose: bool = False,
                     ):
    distance = (BitArray(a) ^ BitArray(b)).count(True)
    if verbose:
        eprint(BitArray(a).bin)
        eprint(BitArray(b).bin, distance)

    return distance


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
    return digest[0:length]


def generate_truncated_file_hash(*,
                                 string: str,
                                 length: int,
                                 algorithm: str,
                                 verbose: bool,
                                 debug: bool,
                                 accept_empty: bool = False,
                                 ):

    path = Path(string).resolve()
    hexdigest = rhash_file(path=path,
                           algorithm=algorithm,
                           verbose=verbose,
                           debug=debug,)

    digest = binascii.unhexlify(hexdigest)
    return digest[0:length]


def generate_truncated_pdqhash(*,
                               string: str,
                               length: int,
                               algorithm: str,
                               verbose: bool,
                               debug: bool,
                               accept_empty: bool = False,
                               ):

    digest = hash_pdqhash(path=Path(string),
                          rotations=False,  # todo
                          verbose=verbose,
                          debug=debug,)

    return digest[0:length]


class UniquePipe():
    def __init__(self, *,
                 verbose: bool,
                 debug: bool,
                 accept_empty: bool,
                 paths: bool,
                 distance: int = None,
                 length: int = 32,
                 algorithm: str = 'sha3_256',):
        self.hashes = set()
        self.length = length
        self.algorithm = algorithm
        self.verbose = verbose
        self.debug = debug
        self.accept_empty = accept_empty
        self.distance = distance
        if algorithm == 'pdqhash':
            assert paths
            from pyphash import hash_pdqhash
            self.algorithm_function = generate_truncated_pdqhash
        else:
            if paths:
                self.algorithm_function = generate_truncated_file_hash
            else:
                self.algorithm_function = generate_truncated_string_hash
        if verbose:
            ic(self.algorithm_function)

    def filter(self, string):
        string_hash = self.algorithm_function(string=string,
                                              length=self.length,
                                              algorithm=self.algorithm,
                                              accept_empty=self.accept_empty,
                                              verbose=self.verbose,
                                              debug=self.debug,)
        distance = None
        if self.debug:
            ic(string_hash)
        if self.distance is None:
            if string_hash not in self.hashes:
                self.hashes.add(string_hash)
                return True, None, string_hash
            return False, None, string_hash   # needed to be able to --prepend to duplicates
        else:
            assert self.distance > 0
            for existing_hash in self.hashes:
                distance = hamming_distance(existing_hash, string_hash)
                if self.verbose:
                    eprint(string_hash.hex())
                    eprint(existing_hash.hex(), distance)
                if distance <= self.distance:
                    if self.verbose:
                        ic(distance)
                    # it's close to something in the set, so add it to the set, and return False
                    self.hashes.add(string_hash)
                    return False, distance, string_hash

            # by here, it's not close to something already in the set, so add it and return True
            # if the set was empty, then there is no distance, so None is returned
            self.hashes.add(string_hash)
            return True, distance, string_hash

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
