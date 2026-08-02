import argparse
import ast
import base64
import hashlib
import io
import os
import re
from logging import getLogger
from pathlib import Path
from typing import TextIO


MAX_LINE_LENGTH = 1024

log = getLogger(__name__)
_non_b64_rgx = re.compile(r'[^A-Za-z0-9+/=]')

def strip_non_b64(s: str) -> str:
    return _non_b64_rgx.sub('', s)
####

def get_md5_hash(file_path: Path) -> str:
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
        ####
    ####
    return hash_md5.hexdigest()
####

def write_tarball(directory: Path, tar: TextIO, encode_all: bool = True, verbose: bool = False) -> None:
    """Create a tarball from the directory containing text files."""
    # Ensure the output tarball path is a Path object
    directory = Path(directory)

    # Open the tarball for writing in 'w' mode (write)
    # Walk through the directory recursively
    for cur_path, dirname, files in os.walk(directory):
        cur_path = Path(cur_path)
        for file in files:
            filepath = cur_path / file
            is_base64 = False
            data = None
            try:
                if not encode_all:
                    try:
                        with open(filepath, 'r', newline='\n') as fin:
                            data = fin.read()
                        ####
                    except UnicodeDecodeError:
                        pass
                    ####
                ####
                if data is None:
                    with open(filepath, 'rb') as fin:
                        data = base64.b64encode(fin.read()).decode()
                    ####
                    is_base64 = True
                    data = '\n'.join(data[i:i + MAX_LINE_LENGTH] for i in range(0, len(data), MAX_LINE_LENGTH))
                ####
            except (FileNotFoundError, IOError):
                print(f'Could not open {str(filepath)!r}')
                continue
            ####
            num_lines = data.count('\n')
            has_trailing_newline = bool(data) and data[-1] == '\n'
            if not has_trailing_newline and data:
                num_lines += 1
            ####
            header_path = str(directory.name / filepath.relative_to(directory))
            header_data = {
                'path': header_path,
                'num_lines': num_lines,
                'is_base64': is_base64,
                'has_trailing_newline': has_trailing_newline,
                'file_size': filepath.stat().st_size,
                'md5': get_md5_hash(filepath),
            }
            header_line = '\t'.join(
                [repr(header_path), str(num_lines), str(int(is_base64)), str(int(has_trailing_newline)),
                 repr(header_data)])
            if verbose:
                print(f'{header_data}')
            ####
            if verbose > 1:
                print('\n'.join(f'{i}/{num_lines} {line!r}' for i, line in enumerate(data.splitlines(), start=1)))
            ####
            tar.write(f'{header_line}\n')
            if data:
                tar.write(data)
                if not has_trailing_newline:
                    tar.write('\n')
                ####
            ####
        ####
    ####
####

def extract_tarball(tar: TextIO, output_dirpath: Path, verbose: bool = False) -> None:
    """Extract the files from the tarball to the specified output directory."""
    output_dirpath = Path(output_dirpath)

    # Ensure the output directory exists
    output_dirpath.mkdir(parents=True, exist_ok=True)

    # Open the tarball for reading
    bad_files = []

    line_number = 0
    while True:
        line = None
        for line in tar:
            line_number += 1
            break
        ####
        if not line:
            break
        ####
        parts = line.split('\t')
        if len(parts) < 5:
            raise RuntimeError(f'Expected two parts. Got:' + repr(line[:100] + (
                '...' if len(line) > 100 else '')) + ". Is the input data encoded? If so, then add --decode")
        ####
        header_data = ast.literal_eval(parts[4])
        try:
            current_filepath = Path(header_data['path'])
            num_lines = int(header_data['num_lines'])
            is_base64 = bool(header_data['is_base64'])
            has_trailing_newline = bool(header_data['has_trailing_newline'])
            expected_size = int(header_data['file_size'])
            expected_md5 = header_data['md5']
        except (TypeError, KeyError,) as e:
            raise RuntimeError(f'@{line_number}: Invalid header line: {line!r}. With exception: {e!r}')
        ####
        if verbose:
            print(header_data)
        ####
        lines = []
        if num_lines > 0:
            for line in tar:
                line_number += 1
                lines.append(line)
                if verbose > 2:
                    print(f'{len(lines)}/{num_lines}: {line!r}')
                ####
                if len(lines) >= num_lines:
                    break
                ####
            ####
        ####
        if len(lines) != num_lines:
            raise RuntimeError(
                f'File: {str(current_filepath)!r} did not have all the expected lines. Expected: {num_lines}, Got: {len(lines)}')
        ####
        output_filepath = output_dirpath / current_filepath
        output_filepath.parent.mkdir(parents=True, exist_ok=True)
        txt_data = ''.join(lines)
        if not has_trailing_newline:
            txt_data = txt_data[:-1]
        ####
        if is_base64:
            with open(output_filepath, 'wb') as fout:
                # Remove newlines
                txt_data = ''.join(txt_data.splitlines())
                fout.write(base64.b64decode(txt_data))
            ####
        else:
            with open(output_filepath, 'w', newline='\n') as fout:
                fout.write(txt_data)
            ####
        ####
        got_file_size = os.stat(output_filepath).st_size
        had_error = False
        if got_file_size != expected_size:
            print(f'Expected size: {expected_size}, Got:{got_file_size}')
            had_error = True
        else:
            if verbose > 1:
                print(f' -- Sizes match')
            ####
        ####
        got_md5_hash = get_md5_hash(output_filepath)
        if got_md5_hash != expected_md5:
            print(f'Hashes did not match')
            had_error = True
        else:
            if verbose > 1:
                print(f' -- Hashes match')
            ####
        ####
        if had_error:
            bad_files.append(output_filepath)
        ####
    ####
    ####
    if bad_files:
        print(f'The following files had errors: {", ".join(str(x) for x in bad_files)}')
    ####
####

def main():
    parser = argparse.ArgumentParser(description="Create or extract tarballs.")
    parser.add_argument(
        '-v', '--verbose',
        action='count',
        default=0,
        help="Increase verbosity level. Can be used multiple times."
    )

    # Define subcommands
    subparsers = parser.add_subparsers(dest='action', required=True)

    # Subcommand for creating a tarball
    create_parser = subparsers.add_parser('create', help='Create a tarball')
    create_parser.add_argument('directory', type=str, help='The directory to include in the tarball')
    create_parser.add_argument('tarball_filename', type=str, help='The name of the tarball file to create')
    create_parser.add_argument('--encode', action='store_true', help='Encodes the output in base64.')
    create_parser.add_argument(
        '--obfuscate', nargs='?', const=5, type=int, default=0,
        help=(
            'Obfuscates base64 output with non-b64 characters. '
            'If --obfuscate is provided without a value, it defaults to 5. '
            'The number specifies how often a non-base64 character is inserted. '
            'Default is 0 if not given.'
        ),
    )
    create_parser.add_argument('--text', action='store_true', help='Allows for pure-text to be non-encoded.')

    # Subcommand for extracting a tarball
    extract_parser = subparsers.add_parser('extract', help='Extract a tarball')
    extract_parser.add_argument('tarball_filename', type=str, help='The tarball file to extract')
    extract_parser.add_argument('output_directory', type=str, help='The directory to extract files to')
    extract_parser.add_argument('--decode', action='store_true', help='Decodes the input from base64.')

    # Parse the arguments
    args, unknown = parser.parse_known_args()
    verbose = args.verbose
    if verbose > 1:
        print(f'Arguments: {args}')
    ####
    if unknown:
        print(f'Unknown arguments: {unknown}')
    ####

    # Perform the action based on the subcommand
    if args.action == 'create':
        tarball_path = Path(args.tarball_filename)
        if not tarball_path.is_file():
            raise RuntimeError(f"Invalid tarball file: {str(tarball_path)!r}")
        ####
        input_directory = Path(args.directory)
        if not input_directory.is_dir():
            raise RuntimeError(f"Invalid directory path: {str(input_directory)!r}")
        ####
        allow_text = bool(args.text)
        encode = bool(args.encode)
        obfuscate = max(0, int(args.obfuscate))

        tarball_io = io.StringIO()
        write_tarball(input_directory, tarball_io, verbose=verbose, encode_all=not allow_text)
        tarball_io.seek(0)
        text = tarball_io.read()

        out_filepath = tarball_path
        if encode:
            text = base64.b64encode(text.encode()).decode()
            out_filepath = out_filepath.parent / (out_filepath.name + '.b64')
            if obfuscate > 0:
                text = ''.join(f'{text[i:i+obfuscate]}~' for i in range(0, len(text), obfuscate))
                out_filepath = out_filepath.parent / (out_filepath.name + '.obs')
            ####
        ####
        out_filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(out_filepath, 'w') as fout:
            fout.write(text)
        ####
        print(f'Wrote {str(out_filepath)!r} ' + ('as encoded' if encode else ''))
    elif args.action == 'extract':
        tarball_path = Path(args.tarball_filename)
        if tarball_path.is_file():
            log.warning(f'Output file {str(tarball_path)!r} already exists. Overwriting.')
        ####
        decode = bool(args.decode)
        with open(tarball_path, 'r') as fin:
            data = fin.read()
        ####
        if decode:
            data = strip_non_b64(data)  # Just go ahead and strip non-b64
            data = base64.b64decode(data.encode()).decode()
        ####
        output_dirpath = Path(args.output_directory)
        extract_tarball(io.StringIO(data), output_dirpath, verbose=verbose)
        print(f"Tarball {str(tarball_path)!r} extracted to {str(output_dirpath)!r}.")
    else:
        raise RuntimeError(f'Invalid action: {args.action}')
    ####
####

if __name__ == "__main__":
    main()
####
