#!/usr/bin/env python3
# -*- coding: utf8 -*-

# pylint: disable=useless-suppression             # [I0021]
# pylint: disable=missing-docstring               # [C0111] docstrings are always outdated and wrong
# pylint: disable=fixme                           # [W0511] todo is encouraged
# pylint: disable=line-too-long                   # [C0301]
# pylint: disable=too-many-instance-attributes    # [R0902]
# pylint: disable=too-many-lines                  # [C0302] too many lines in module
# pylint: disable=invalid-name                    # [C0103] single letter var names, name too descriptive
# pylint: disable=too-many-return-statements      # [R0911]
# pylint: disable=too-many-branches               # [R0912]
# pylint: disable=too-many-statements             # [R0915]
# pylint: disable=too-many-arguments              # [R0913]
# pylint: disable=too-many-nested-blocks          # [R1702]
# pylint: disable=too-many-locals                 # [R0914]
# pylint: disable=too-few-public-methods          # [R0903]
# pylint: disable=no-member                       # [E1101] no member for base
# pylint: disable=attribute-defined-outside-init  # [W0201]
# pylint: disable=too-many-boolean-expressions    # [R0916] in if statement

from __future__ import annotations

import hashlib
import os
from math import inf
from pathlib import Path

from asserttool import ic
from bitstring import BitArray
from eprint import eprint
from hashtool import rhash_file
from pyphash import hash_pdqhash


class HashAlgorithmError(ValueError):
    pass


def hamming_distance(
    a,
    b,
    *,
    verbose: bool | int | float,
):
    distance = (BitArray(a) ^ BitArray(b)).count(True)
    if verbose:
        eprint(BitArray(a).bin)
        eprint(BitArray(b).bin, distance)

    return distance


def generate_truncated_string_hash(
    string: str | bytes,
    *,
    length: int,
    algorithm: str,
    verbose: bool | int | float,
    accept_empty: bool = False,
) -> bytes:
    string = str(string)  # todo
    assert algorithm is not None
    if not accept_empty:
        if len(string) == 0:
            raise ValueError("empty string")
    # if not isinstance(string, str):
    #    msg = "string must be type str, not type <{}>".format(type(string))
    #    raise TypeError(msg)
    # ic(algorithm)
    byte_string = string.encode("UTF-8")
    digest = getattr(hashlib, algorithm)(byte_string).digest()
    # hexdigest = digest.hex()
    # return hexdigest[0:length - 1]  # for sha3_256 this was cutting it in half from 256 to 128 if length == 32
    return digest[0:length]


def generate_truncated_file_hash(
    path: Path,
    *,
    length: int,
    algorithm: str,
    verbose: bool | int | float,
    accept_empty: bool = False,
):

    _path = Path(os.fsdecode(path)).resolve()
    digests = rhash_file(
        path=_path,
        algorithms=[algorithm],
        verbose=verbose,
        disable_locking=False,
    )
    digest = digests[algorithm]
    # digest = binascii.unhexlify(digest.digest)
    return digest.digest[0:length]


def generate_pdqhash(
    path: Path,
    *,
    length: int,
    algorithm: str,
    verbose: bool | int | float,
    accept_empty: bool = False,
):

    _path = Path(os.fsdecode(path)).resolve()
    digest = hash_pdqhash(
        path=_path,
        rotations=False,  # todo
        verbose=verbose,
    )

    if digest:
        return digest
    raise HashAlgorithmError(_path)


class UniquePipe:
    def __init__(
        self,
        *,
        verbose: bool | int | float,
        accept_empty: bool,
        paths: bool,
        distance: None | int = None,
        length: int = 32,
        algorithm: str = "sha3_256",
    ):

        self.hashes = set()
        self.length = length
        self.algorithm = algorithm
        self.verbose = verbose
        self.accept_empty = accept_empty
        self.distance = distance
        if algorithm == "pdqhash":
            assert paths
            self.algorithm_function = generate_pdqhash
        else:
            if paths:
                self.algorithm_function = generate_truncated_file_hash
            else:
                self.algorithm_function = generate_truncated_string_hash
        if self.verbose:
            ic(
                self.algorithm_function,
                self.accept_empty,
                paths,
                self.distance,
                self.algorithm,
            )

    def filter(self, string: str | bytes):
        # assert isinstance(string, str) or isinstance(string, bytes)
        string_hash = self.algorithm_function(
            string,
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
            return (
                False,
                None,
                string_hash,
            )  # needed to be able to --prepend to duplicates
        assert self.distance > 0
        for existing_hash in self.hashes:
            distance = hamming_distance(
                existing_hash, string_hash, verbose=self.verbose
            )
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
        string_hash = self.algorithm_function(
            string,
            length=self.length,
            algorithm=self.algorithm,
            accept_empty=self.accept_empty,
            verbose=self.verbose,
        )
        if self.verbose == inf:
            ic(string_hash)
        self.hashes.remove(string_hash)

    def add(self, string):
        string_hash = self.algorithm_function(
            string,
            length=self.length,
            algorithm=self.algorithm,
            accept_empty=self.accept_empty,
            verbose=self.verbose,
        )
        if self.verbose == inf:
            ic(string_hash)
        self.hashes.add(string_hash)

    def exists(self, string):
        string_hash = self.algorithm_function(
            string,
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
