import base64
from argparse import ArgumentParser
from pathlib import Path


def _same_file(first: Path, second: Path) -> bool:
    """Detect path and existing hard-link aliases before writing output."""
    if first.resolve() == second.resolve():
        return True
    ####
    try:
        return first.samefile(second)
    except FileNotFoundError:
        return False
    ####
####


def _require_distinct(input_file: Path, output_file: Path) -> None:
    if _same_file(input_file, output_file):
        raise ValueError("input and output must refer to different files")
    ####
####


def encode_file(input_file: Path, output_file: Path, verbose: int = 0) -> None:
    _require_distinct(input_file, output_file)
    with open(input_file, 'rb') as f:
        encoded = base64.b64encode(f.read())
    ####
    with open(output_file, 'wb') as f:
        f.write(encoded)
    ####
    if verbose:
        print(f'{str(input_file)!r} -> {str(output_file)!r}')
    ####
####



def decode_file(input_file: Path, output_file: Path, verbose: int = 0) -> None:
    _require_distinct(input_file, output_file)
    with open(input_file, 'rb') as f:
        # Permit ordinary wrapped Base64, but reject other non-alphabet bytes.
        encoded = b''.join(f.read().split())
        decoded = base64.b64decode(encoded, validate=True)
    ####
    with open(output_file, 'wb') as f:
        f.write(decoded)
    ####
    if verbose:
        print(f'{str(input_file)!r} -> {str(output_file)!r}')
    ####
####



def main() -> None:
    parser = ArgumentParser('Base64 tool')
    parser.add_argument(
        '-v', '--verbose',
        action='count',
        default=0,
        help="Increase verbosity level. Can be used multiple times."
    )
    parser.add_argument('action', choices=['encode', 'decode'])
    parser.add_argument('input', type=Path, help='Input file')
    parser.add_argument('output', type=Path, help='Output file')

    # Parse the arguments
    args, unknown = parser.parse_known_args()
    verbose = args.verbose
    if verbose > 1:
        print(f'Arguments: {args}')
    ####
    if unknown:
        print(f'Unknown arguments: {unknown}')
    ####

    action = args.action
    source_file = args.input
    destination_file = args.output

    try:
        if action == 'encode':
            encode_file(source_file, destination_file, verbose=verbose)
        elif action == 'decode':
            decode_file(source_file, destination_file, verbose=verbose)
        else:
            raise RuntimeError(f'Invalid action: {args.action}')
        ####
    except ValueError as error:
        parser.error(str(error))
    ####
####


if __name__ == "__main__":
    main()
####
