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

#import binascii
import hashlib
#import sys
from math import inf
from pathlib import Path
from typing import Optional
from typing import Union

from asserttool import ic
from asserttool import increment_debug
#import numpy
from bitstring import BitArray
from eprint import eprint
from hashtool import rhash_file
from pyphash import hash_pdqhash

#from typing import Sequence
#from typing import Union


class HashAlgorithmError(ValueError):
    pass


def hamming_distance(a, b, *,
                     verbose: Union[bool, int, float],
                     ):
    distance = (BitArray(a) ^ BitArray(b)).count(True)
    if verbose:
        eprint(BitArray(a).bin)
        eprint(BitArray(b).bin, distance)

    return distance


@increment_debug
def generate_truncated_string_hash(*,
                                   string: str,
                                   length: int,
                                   algorithm: str,
                                   verbose: Union[bool, int, float],
                                   accept_empty: bool = False,
                                   ) -> bytes:
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
                                 verbose: Union[bool, int, float],
                                 accept_empty: bool = False,
                                 ):

    path = Path(string).resolve()
    hexdigests = rhash_file(path=path,
                            algorithms=[algorithm],
                            verbose=verbose,
                            )
    digest = hexdigests[algorithm]

    #digest = binascii.unhexlify(digest.digest)
    return digest.digest[0:length]


def generate_pdqhash(*,
                     string: str,
                     length: int,
                     algorithm: str,
                     verbose: Union[bool, int, float],
                     accept_empty: bool = False,
                     ):

    digest = hash_pdqhash(path=Path(string),
                          rotations=False,  # todo
                          verbose=verbose,
                          )

    if digest:
        return digest
    raise HashAlgorithmError(string)


class UniquePipe():
    @increment_debug
    def __init__(self, *,
                 verbose: Union[bool, int, float],
                 accept_empty: bool,
                 paths: bool,
                 distance: Optional[int] = None,
                 length: int = 32,
                 algorithm: str = 'sha3_256',
                 ):

        self.hashes = set()
        self.length = length
        self.algorithm = algorithm
        self.verbose = verbose
        self.accept_empty = accept_empty
        self.distance = distance
        if algorithm == 'pdqhash':
            assert paths
            self.algorithm_function = generate_pdqhash
        else:
            if paths:
                self.algorithm_function = generate_truncated_file_hash
            else:
                self.algorithm_function = generate_truncated_string_hash
        if self.verbose:
            ic(self.algorithm_function, self.accept_empty, paths, self.distance, self.algorithm)

    def filter(self, string):
        assert (isinstance(string, str) or isinstance(string, bytes))
        string_hash = self.algorithm_function(string=string,
                                              length=self.length,
                                              algorithm=self.algorithm,
                                              accept_empty=self.accept_empty,
                                              verbose=self.verbose,
                                              )
        distance = None
        if self.verbose == inf:
            ic(string_hash)
        if self.distance is None:
            if string_hash not in self.hashes:
                self.hashes.add(string_hash)
                return True, None, string_hash
            return False, None, string_hash   # needed to be able to --prepend to duplicates
        assert self.distance > 0
        for existing_hash in self.hashes:
            distance = hamming_distance(existing_hash, string_hash, verbose=self.verbose)
            if self.verbose == inf:
                eprint(string_hash.hex())
                eprint(existing_hash.hex(), distance)
            if distance <= self.distance:
                if self.verbose == inf:
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
                                              )
        if self.verbose == inf:
            ic(string_hash)
        self.hashes.remove(string_hash)

    def add(self, string):
        string_hash = self.algorithm_function(string=string,
                                              length=self.length,
                                              algorithm=self.algorithm,
                                              accept_empty=self.accept_empty,
                                              verbose=self.verbose,
                                              )
        if self.verbose == inf:
            ic(string_hash)
        self.hashes.add(string_hash)

    def exists(self, string):
        string_hash = self.algorithm_function(string=string,
                                              length=self.length,
                                              algorithm=self.algorithm,
                                              accept_empty=self.accept_empty,
                                              verbose=self.verbose,
                                              )
        if self.verbose == inf:
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
