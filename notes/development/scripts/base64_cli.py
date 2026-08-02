import base64
from argparse import ArgumentParser
from pathlib import Path


def encode_file(input_file: Path, output_file: Path, verbose: int = 0):
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
    with open(input_file, 'rb') as f:
        decoded = base64.b64decode(f.read())
    ####
    with open(output_file, 'wb') as f:
        f.write(decoded)
    ####
    if verbose:
        print(f'{str(input_file)!r} -> {str(output_file)!r}')
    ####


####

if __name__ == "__main__":
    parser = ArgumentParser('Base64 tool')
    parser.add_argument(
        '-v', '--verbose',
        action='count',
        default=0,
        help="Increase verbosity level. Can be used multiple times."
    )
    parser.add_argument('action', choices=['encode', 'decode'])
    parser.add_argument('input', type=Path, help='Input file')
    parser.add_argument('output', type=Path, help='Input file')

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
    input_file = args.input
    output_file = args.output

    if action == 'encode':
        encode_file(input_file, output_file, verbose=verbose)
    elif action == 'decode':
        decode_file(input_file, output_file, verbose=verbose)
    else:
        raise RuntimeError(f'Invalid action: {args.action}')
    ####
####
