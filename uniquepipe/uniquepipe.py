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
from typing import Union

import click
from asserttool import ic
from clicktool import click_add_options
from clicktool import click_global_options
from clicktool import tv
from eprint import eprint
# from colorama import Fore
# from colorama import Style
from mptool import output
from mptool import unmp

from uniquepipe import UniquePipe
from uniquepipe.UniquePipe import HashAlgorithmError


def str_list(line):
    line = [str(thing) for thing in line]  # angryfiles...
    if len(line) == 1:
        return line[0]
    line = " ".join(line)
    return line


def perhaps_invert(thing, *, invert):
    if invert:
        return not thing


# def print_list(*, output_list, end, stderr,):
#    output_list = str_list(output_list)
#    if stderr:
#        eprint(output_list, end=end)
#    else:
#        print(output_list, end=end)
#
#


@click.command()
@click.argument("items", type=str, nargs=-1)
@click.option("--duplicates", is_flag=True)
@click.option("--paths", is_flag=True, help="hash file contents")
@click.option("--images", "--image", is_flag=True)
@click.option("--count", is_flag=True)
@click.option("--prepend", is_flag=True)
@click.option("--accept-empty", is_flag=True)
@click.option("--length", type=int, default=32)
@click.option("--distance", type=int)
@click.option("--show-closest-distance", is_flag=True)
@click.option("--show-skipped", is_flag=True)
@click.option("--algorithm", type=str, default="sha3_256")
@click.option("--exit-on-collision", is_flag=True)
@click.option(
    "--preload",
    "preloads",
    type=click.Path(
        exists=True,
        dir_okay=False,
        file_okay=True,
        path_type=str,
        allow_dash=True,
    ),
    multiple=True,
)
@click_add_options(click_global_options)
@click.pass_context
def cli(
    ctx,
    items,
    duplicates: bool,
    preloads,
    verbose: Union[bool, int, float],
    verbose_inf: bool,
    count: int,
    exit_on_collision: bool,
    length: int,
    show_closest_distance: int,
    show_skipped: int,
    distance: int,
    accept_empty: bool,
    algorithm: str,
    paths: bool,
    images: bool,
    prepend: bool,
    dict_input: bool,
):

    tty, verbose = tv(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
    )
    if images:
        algorithm = "pdqhash"

    ic(algorithm)
    if algorithm == "pdqhash":
        paths = True
        if not distance:
            distance = 8
            eprint("Warning: using default distance:", distance)

    uniquepipe = UniquePipe(
        algorithm=algorithm,
        length=length,
        accept_empty=accept_empty,
        distance=distance,
        paths=paths,
        verbose=verbose,
    )
    for preload in preloads:
        if verbose:
            ic(preload)
        with open(preload, "rb") as fh:
            for index, item in enumerate(fh):
                if verbose:
                    ic("preload:", index, item)
                try:
                    uniquepipe.filter(item)
                except HashAlgorithmError as e:
                    if verbose:
                        ic(e)
                    continue
        if verbose:
            ic("preloaded:", len(uniquepipe))

    unique_count = 0
    duplicate_count = 0
    # bytes_read = 0
    if items:
        iterator = items
    else:
        iterator = unmp(
            verbose=verbose,
            valid_types=[
                str,
                bytes,
            ],
        )

    for index, item in enumerate(iterator):
        new = False
        distance = None
        digest = None
        if verbose:
            ic(index, item)

        if len(item) == 0:
            ic("empty value found:", index, item, accept_empty)

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
                    output(
                        item,
                        reason=None,
                        dict_input=dict_input,
                        tty=tty,
                        verbose=verbose,
                    )
                    # print_result(digest=digest,
                    #             distance=distance,
                    #             item=item,
                    #             prepend=prepend,
                    #             show_closest_distance=show_closest_distance,
                    #             end=b'\n',
                    #             skipped=False,
                    #             stderr=False,
                    #             verbose=verbose,
                    #             )
        else:
            duplicate_count += 1
            if exit_on_collision:
                ic(item)
                ic(unique_count)
                ic(uniquepipe.__sizeof__())
                ic(sys.getsizeof(uniquepipe))
                raise ValueError("collision: {}".format(item))
            if duplicates:
                output(
                    item,
                    reason=None,
                    dict_input=dict_input,
                    tty=tty,
                    verbose=verbose,
                )
                # print_result(digest=digest,
                #             distance=distance,
                #             item=item,
                #             prepend=prepend,
                #             show_closest_distance=show_closest_distance,
                #             end=b'\n',
                #             skipped=False,
                #             verbose=verbose,
                #             stderr=False,
                #             )
            if show_skipped:
                output(
                    item,
                    reason=None,
                    dict_input=dict_input,
                    tty=tty,
                    verbose=verbose,
                )
                # print_result(digest=digest,
                #             distance=distance,
                #             item=item,
                #             prepend=prepend,
                #             show_closest_distance=show_closest_distance,
                #             end=b'\n',
                #             skipped=True,
                #             verbose=verbose,
                #             stderr=True,
                #             )

    if count:
        if duplicates:
            output(
                duplicate_count,
                reason=None,
                dict_input=dict_input,
                tty=tty,
                verbose=verbose,
            )
        else:
            output(
                unique_count,
                reason=None,
                dict_input=dict_input,
                tty=tty,
                verbose=verbose,
            )
