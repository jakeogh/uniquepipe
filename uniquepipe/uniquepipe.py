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

import sys
from collections.abc import Sequence

import click
from asserttool import ic
from clicktool import click_add_options
from clicktool import click_global_options
from clicktool import tv
from eprint import eprint
from mptool import output
from unmp import unmp

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


@click.command()
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
    duplicates: bool,
    preloads,
    verbose: bool | int | float,
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
    dict_output: bool,
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
            iterator = unmp(
                file_handle=fh,
                valid_types=[
                    bytes,
                ],
                verbose=verbose,
            )
            for index, item in enumerate(iterator):
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

    # could/should operate over the raw seralized messagepacked objects instead
    iterator: Sequence[dict | bytes | str] = unmp(
        verbose=verbose,
        valid_types=[
            str,
            bytes,
            dict,
        ],
        single_type=True,
    )

    for index, item in enumerate(iterator):
        if isinstance(item, dict):
            assert len(list(item.items())) == 1
            for _k, _v in item.items():
                assert isinstance(_k, (str, bytes))
                assert isinstance(_v, (str, bytes))
            item = str(item)
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
                        dict_output=dict_output,
                        tty=tty,
                        verbose=verbose,
                    )
        else:
            duplicate_count += 1
            if exit_on_collision:
                ic(item)
                ic(unique_count)
                ic(uniquepipe.__sizeof__())
                ic(sys.getsizeof(uniquepipe))
                raise ValueError(f"collision: {item}")
            if duplicates:
                output(
                    item,
                    reason=None,
                    dict_output=dict_output,
                    tty=tty,
                    verbose=verbose,
                )
            if show_skipped:
                output(
                    item,
                    reason=None,
                    dict_output=dict_output,
                    tty=tty,
                    verbose=verbose,
                )
    # if count:
    #    assert False
    #    if duplicates:
    #        output(
    #            duplicate_count,
    #            reason=None,
    #            dict_output=dict_output,
    #            tty=tty,
    #            verbose=verbose,
    #        )
    #    else:
    #        output(
    #            unique_count,
    #            reason=None,
    #            dict_output=dict_output,
    #            tty=tty,
    #            verbose=verbose,
    #        )
