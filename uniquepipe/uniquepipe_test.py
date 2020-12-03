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


from uniquepipe import UniquePipe
import click

try:
    from icecream import ic  # https://github.com/gruns/icecream
except ImportError:
    import sys

    def eprint(*args, **kwargs):
        if 'file' in kwargs.keys():
            kwargs.pop('file')
        print(*args, file=sys.stderr, **kwargs)

from enumerate_input import enumerate_input


@click.command()
@click.argument("items", type=str, nargs=-1)
@click.option('--verbose', is_flag=True)
@click.option('--debug', is_flag=True)
@click.option("--printn", is_flag=True)
def cli(items,
        verbose,
        debug,
        printn,):

    null = not printn
    end = '\n'
    if null:
        end = '\x00'
    if sys.stdout.isatty():
        end = '\n'

    uniquepipe = UniquePipe()

    for index, item in enumerate_input(iterator=items,
                                       null=null,
                                       debug=debug,
                                       verbose=verbose,):
        if verbose:
            ic(index, item)

        if uniquepipe.filter(item):
            print(item, end=end)
