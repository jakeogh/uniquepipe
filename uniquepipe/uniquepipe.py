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


import sys

import click
from enumerate_input import enumerate_input

from uniquepipe import UniquePipe
from uniquepipe.UniquePipe import HashAlgorithmError


def eprint(*args, **kwargs):
    if 'file' in kwargs.keys():
        kwargs.pop('file')
    print(*args, file=sys.stderr, **kwargs)


try:
    from icecream import ic  # https://github.com/gruns/icecream
except ImportError:
    ic = eprint


def perhaps_invert(thing, *, invert):
    if invert:
        return not thing


@click.command()
@click.argument("items", type=str, nargs=-1)
@click.option('--duplicates', is_flag=True)
@click.option('--paths', is_flag=True)
@click.option('--verbose', is_flag=True)
@click.option('--debug', is_flag=True)
@click.option('--count', is_flag=True)
@click.option("--printn", is_flag=True)
@click.option("--prepend", is_flag=True)
@click.option("--accept-empty", is_flag=True)
@click.option("--length", type=int, default=32)
@click.option("--distance", type=int)
@click.option("--show-closest-distance", is_flag=True)
@click.option("--algorithm", type=str, default='sha3_256')
@click.option("--exit-on-collision", is_flag=True)
@click.option("--preload", "preloads",
              type=click.Path(exists=True,
                              dir_okay=False,
                              file_okay=True,
                              path_type=str,
                              allow_dash=True,),
              multiple=True)
@click.option("--preload-delim-null", "--preload-null", is_flag=True)
def cli(items,
        duplicates: bool,
        preloads,
        preload_delim_null: bool,
        verbose: bool,
        count: int,
        exit_on_collision: bool,
        length: int,
        show_closest_distance: int,
        distance: int,
        accept_empty: bool,
        algorithm: str,
        debug: bool,
        paths: bool,
        printn: bool,
        prepend: bool,
        ):

    null = not printn
    end = '\n'
    if null:
        end = '\x00'
    if sys.stdout.isatty():
        end = '\n'

    preload_null = False
    if preload_delim_null:
        preload_null = True

    if algorithm == 'pdqhash':
        paths = True

    uniquepipe = UniquePipe(algorithm=algorithm,
                            length=length,
                            accept_empty=accept_empty,
                            distance=distance,
                            paths=paths,
                            verbose=verbose,
                            debug=debug,)
    for preload in preloads:
        if verbose:
            ic(preload, preload_delim_null, preload_null)
        with open(preload, 'rb') as fh:
            for index, item in enumerate_input(iterator=fh,
                                               head=False,
                                               skip=False,
                                               tail=False,
                                               null=preload_null,
                                               disable_stdin=True,
                                               debug=debug,
                                               verbose=verbose,
                                               ):
                if verbose:
                    ic('preload:', index, item)
                try:
                    uniquepipe.filter(item)
                except HashAlgorithmError as e:
                    if verbose:
                        ic(e)
                    continue
        if verbose:
            ic('preloaded:', len(uniquepipe))

    unique_count = 0
    duplicate_count = 0
    #bytes_read = 0
    for index, item in enumerate_input(iterator=items,
                                       head=False,
                                       skip=False,
                                       tail=False,
                                       null=null,
                                       debug=debug,
                                       verbose=verbose,):
        new = False
        distance = None
        digest = None
        if verbose:
            ic(index, item)

        if len(item) == 0:
            ic('empty value found:', index, item, accept_empty)

        try:
            new, distance, digest = uniquepipe.filter(item)
        except HashAlgorithmError as e:
            if verbose:
                ic(e)
            continue

        if new:
            unique_count += 1
            if not count:
                if not duplicates:
                    if prepend:
                        if show_closest_distance:
                            print(digest.hex(), distance, item, end=end)
                        else:
                            print(digest.hex(), item, end=end)
                    else:
                        print(item, end=end)
        else:
            duplicate_count += 1
            if exit_on_collision:
                ic(item)
                ic(unique_count)
                ic(uniquepipe.__sizeof__())
                ic(sys.getsizeof(uniquepipe))
                raise ValueError("collision: {}".format(item))
            if duplicates:
                if prepend:
                    if show_closest_distance:
                        print(digest.hex(), distance, item, end=end)
                    else:
                        print(digest.hex(), item, end=end)
                else:
                    print(item, end=end)

    if count:
        if duplicates:
            print(duplicate_count, end=end)
        else:
            print(unique_count, end=end)
