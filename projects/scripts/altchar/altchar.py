""" Inserts characters every other input stream character.
However, it reads line by line (so assumes text) and does not insert after the ending newline character.
"""
from argparse import ArgumentParser
from itertools import tee
from pathlib import Path
from typing import Iterator, Iterable


def file_char_generator_by_line(filepath: Path, verbose: int = 0) -> Iterator[str]:
    with open(filepath, 'r') as fin:
        for i, line in enumerate(fin):
            if verbose > 1:
                print(f'line {i}: {line!r}')
            ####
            yield from line
        ####
    ####
####

def insert_char_every_other(stream: Iterable[str], ch: str, verbose: int = 0) -> Iterable[str]:
    for i, s in enumerate(stream):
        if verbose > 1:
            print(f'{i}: {s=} {ch=}')
        ####
        yield s
        if s == '\n' or s == '\r':
            continue
        ####
        yield ch
    ####
####

def skip_n_chars(stream: Iterable[str], n: int, verbose: int = 0) -> Iterable[str]:
    itr = iter(stream)
    num = 0
    while True:
        try:
            out = next(itr)
            yield out
            skipped = [next(itr) for _ in range(n)]
            if verbose > 1:
                print(f'{num}: {out=} {skipped=}')
            ####
            num += 1
        except StopIteration:
            break
        ####
    ####
####

def remove_inserted_markers(
    stream: Iterable[str],
    marker: str,
    verbose: int = 0,
) -> Iterable[str]:
    """Remove the exact marker inserted after each non-newline character."""
    if not marker:
        raise ValueError("marker must not be empty")
    ####

    itr = iter(stream)
    for index, character in enumerate(itr):
        yield character
        if character in "\r\n":
            continue
        ####
        for expected in marker:
            try:
                removed = next(itr)
            except StopIteration as error:
                raise ValueError(
                    f"input ended before marker at character {index}"
                ) from error
            ####
            if removed != expected:
                raise ValueError(
                    f"expected marker {marker!r} after character {index}, "
                    f"got {removed!r}"
                )
            ####
            if verbose > 1:
                print(f'{index}: removed {removed=}')
            ####
        ####
    ####
####

def main() -> None:
    parser = ArgumentParser('Alternate character inserter/remover')
    parser.add_argument(
        '-v', '--verbose',
        action='count',
        default=0,
        help="Increase verbosity level. Can be used multiple times."
    )
    parser.add_argument('action', choices=['insert', 'remove', 'test'], help='Command to insert or remove characters')
    parser.add_argument('input', type=Path, help="Input file")
    parser.add_argument('--output', default=None, type=Path, help="Output file")
    parser.add_argument('--char', type=str, default='A', help="Character to insert/remove")

    args, unknown = parser.parse_known_args()
    verbose = args.verbose
    if verbose:
        print(f'{args=}')
    ####
    if unknown:
        print(f'Unknown arguments: {unknown}')
    ####

    action = args.action
    ch = args.char
    input_file = args.input
    output_file = args.output

    in_stream = file_char_generator_by_line(input_file, verbose=verbose)
    if action == 'insert':
        out_suffix = '.a'
        in_stream = insert_char_every_other(in_stream, ch, verbose=verbose)
    elif action == 'remove':
        out_suffix = '.rem'
        in_stream = remove_inserted_markers(in_stream, ch, verbose=verbose)
    elif action == 'test':
        in_stream, alt_stream = tee(in_stream, 2)
        alt_stream = remove_inserted_markers(insert_char_every_other(alt_stream, ch), ch)
        all_same = all((lhs == rhs) for lhs, rhs in zip(in_stream, alt_stream))
        assert all_same
        print(f'Cycled data was the same. Test passed.')
        input_data = 'abcd'
        expected = 'aAbAcAdA'
        got = ''.join(insert_char_every_other((ch for ch in input_data), 'A'))
        assert got == expected, f'Expected {expected}, Got {got}'
        print(f'Hardcode data insert was the same. Test passed.')
        input_data, expected = expected, input_data
        got = ''.join(skip_n_chars((ch for ch in input_data),len( 'A')))
        assert got == expected, f'Expected {expected}, Got {got}'
        print(f'Hardcode data remove was the same. Test passed.')
        return
    else:
        raise RuntimeError(f'Invalid action: {action}')
    ####
    default_output = output_file is None
    if output_file is None:
        output_file = input_file.parent / (input_file.name + out_suffix)
    ####

    # The input stream is lazy, so reject aliases before opening the output.
    if input_file.resolve() == output_file.resolve():
        parser.error("input and output must refer to different files")
    ####
    input_file.stat()
    try:
        output_file.stat()
    except FileNotFoundError:
        pass
    else:
        if input_file.samefile(output_file):
            parser.error("input and output must refer to different files")
        ####
    ####

    if default_output and output_file.exists():
        print(f'Output file {str(output_file)!r} already exists. Overwriting.')
    ####
    with open(output_file, 'w') as fout:
        for i, s in enumerate(in_stream):
            if verbose > 1:
                print(f'o{i}: {s=}')
            ####
            fout.write(s)
        ####
    ####
    print(f'Output written to {str(output_file)!r}')
####

if __name__ == '__main__':
    main()
####
