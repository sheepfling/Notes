import argparse
import ast
import base64
import codecs
import hashlib
import io
import os
import re
from logging import getLogger
from pathlib import Path
from typing import TextIO


MAX_LINE_LENGTH = 1024
FORMAT_MAGIC = 'NOTES-TEXTBALL/1'

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


def _encode_text(value: str, encoding: str | None) -> bytes:
    """Encode exactly as the selected text stream would, before touching output."""
    buffer = io.BytesIO()
    with io.TextIOWrapper(buffer, encoding=encoding, newline='\n') as writer:
        writer.write(value)
        writer.flush()
        return buffer.getvalue()
    ####
####


def write_tarball(
    directory: Path,
    tar: TextIO,
    encode_all: bool = True,
    verbose: bool = False,
    protected_output: Path | None = None,
    encoding: str | None = None,
) -> None:
    """Create a tarball from the directory containing text files."""
    # Ensure the output tarball path is a Path object
    directory = Path(directory)

    source_root = directory.resolve(strict=True)
    output = protected_output.resolve() if protected_output is not None else None
    if output is not None and output.is_relative_to(source_root):
        raise RuntimeError('Output must be outside the input directory')
    ####

    def fail_walk(error: OSError) -> None:
        raise error
    ####

    # Make the custom stream self-identifying before writing any records.
    tar.write(f'{FORMAT_MAGIC}\n')
    # Walk through the directory recursively
    for cur_path, dirname, files in os.walk(directory, onerror=fail_walk, followlinks=False):
        cur_path = Path(cur_path)
        for name in dirname:
            if (cur_path / name).is_symlink():
                raise RuntimeError(f'Directory symlink cannot be archived: {str(cur_path / name)!r}')
            ####
        ####
        for file in files:
            filepath = cur_path / file
            if filepath.is_symlink():
                resolved = filepath.resolve(strict=True)
                if not resolved.is_relative_to(source_root):
                    raise RuntimeError(f'File symlink leaves input directory: {str(filepath)!r}')
                ####
            ####
            if output is not None:
                try:
                    aliases_output = filepath.samefile(output)
                except FileNotFoundError:
                    # A missing output is normal, but a missing input is not.
                    filepath.stat()
                    aliases_output = False
                ####
                if aliases_output:
                    raise RuntimeError(f'Output aliases an input file: {str(filepath)!r}')
                ####
            ####
            is_base64 = False
            data = None
            # Capture each member once so metadata describes the bytes archived.
            with open(filepath, 'rb') as fin:
                source_bytes = fin.read()
            ####
            if not encode_all:
                try:
                    with io.TextIOWrapper(io.BytesIO(source_bytes), encoding=encoding, newline='\n') as fin:
                        data = fin.read()
                    ####
                    # Some codecs can decode bytes but do not reproduce them
                    # exactly when encoding (for example, a BOM-less UTF-8
                    # stream read using utf-8-sig). Preserve those as bytes.
                    if _encode_text(data, encoding) != source_bytes:
                        data = None
                    ####
                except UnicodeError:
                    data = None
                ####
            ####
            if data is None:
                data = base64.b64encode(source_bytes).decode()
                is_base64 = True
                data = '\n'.join(data[i:i + MAX_LINE_LENGTH] for i in range(0, len(data), MAX_LINE_LENGTH))
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
                'file_size': len(source_bytes),
                'md5': hashlib.md5(source_bytes).hexdigest(),
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

def _safe_output_path(output_dirpath: Path, stored_path: str) -> Path:
    relative_path = Path(stored_path)
    if relative_path.is_absolute() or relative_path.drive or '..' in relative_path.parts:
        raise RuntimeError(f'Unsafe path in textball header: {stored_path!r}')
    ####
    output_root = output_dirpath.resolve()
    output_path = (output_root / relative_path).resolve()
    if output_path != output_root and output_root not in output_path.parents:
        raise RuntimeError(f'Unsafe path in textball header: {stored_path!r}')
    ####
    return output_path
####


def extract_tarball(
    tar: TextIO,
    output_dirpath: Path,
    verbose: bool = False,
    allow_legacy: bool = False,
    protected_source: Path | None = None,
    encoding: str | None = None,
) -> None:
    """Extract the files from the tarball to the specified output directory."""
    output_dirpath = Path(output_dirpath)

    line_number = 0
    first_line = tar.readline()
    line_number += 1
    if first_line.rstrip('\r\n') != FORMAT_MAGIC:
        if not allow_legacy:
            raise RuntimeError(
                f'Unsupported textball format: expected {FORMAT_MAGIC!r}; '
                'pass --legacy only for trusted historical files'
            )
        ####
        line = first_line
    else:
        line = None
    ####

    while True:
        if line is None:
            line = tar.readline()
            if line:
                line_number += 1
            ####
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
        output_filepath = _safe_output_path(output_dirpath, str(current_filepath))
        if protected_source is not None:
            aliases_source = output_filepath == protected_source.resolve()
            if not aliases_source:
                try:
                    aliases_source = output_filepath.samefile(protected_source)
                except FileNotFoundError:
                    pass
                ####
            ####
            if aliases_source:
                raise RuntimeError(f'Output aliases the input textball: {str(current_filepath)!r}')
            ####
        ####
        txt_data = ''.join(lines)
        if is_base64:
            candidates = [base64.b64decode(''.join(txt_data.splitlines()))]
        else:
            # Older Windows archives may have translated their framing and
            # member newlines while writing. Accept a variant only when both
            # the original size and checksum identify it unambiguously.
            variants = [txt_data]
            if not has_trailing_newline and txt_data:
                variants = [txt_data[:-1]]
                if txt_data.endswith('\r\n'):
                    variants.append(txt_data[:-2])
                ####
            ####
            variants.extend(value.replace('\r\n', '\n') for value in tuple(variants))
            candidates = [_encode_text(value, encoding) for value in variants]
        ####
        matching_size = [value for value in candidates if len(value) == expected_size]
        if not matching_size:
            raise RuntimeError(
                f'Invalid size for {str(current_filepath)!r}: expected {expected_size}, got {len(candidates[0])}'
            )
        ####
        payload = next((value for value in matching_size if hashlib.md5(value).hexdigest() == expected_md5), None)
        if payload is None:
            raise RuntimeError(f'Checksum mismatch for {str(current_filepath)!r}')
        ####
        if verbose > 1:
            print(' -- Size and checksum match')
        ####
        output_dirpath.mkdir(parents=True, exist_ok=True)
        output_filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(output_filepath, 'wb') as fout:
            fout.write(payload)
        ####
        line = None
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
    create_parser.add_argument('--encoding', help='Text codec for members and archive; default is the locale codec.')

    # Subcommand for extracting a tarball
    extract_parser = subparsers.add_parser('extract', help='Extract a tarball')
    extract_parser.add_argument('tarball_filename', type=str, help='The tarball file to extract')
    extract_parser.add_argument('output_directory', type=str, help='The directory to extract files to')
    extract_parser.add_argument('--decode', action='store_true', help='Decodes the input from base64.')
    extract_parser.add_argument('--encoding', help='Text codec used when creating the archive; default is the locale codec.')
    extract_parser.add_argument(
        '--legacy',
        action='store_true',
        help='Accept the unversioned historical format; use only for trusted input.',
    )

    # Parse the arguments
    args, unknown = parser.parse_known_args()
    if args.encoding is not None:
        try:
            codecs.lookup(args.encoding)
        except LookupError:
            parser.error(f'unknown text encoding: {args.encoding}')
        ####
    ####
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

        out_filepath = tarball_path
        if encode:
            out_filepath = out_filepath.parent / (out_filepath.name + '.b64')
            if obfuscate > 0:
                out_filepath = out_filepath.parent / (out_filepath.name + '.obs')
            ####
        ####
        tarball_io = io.StringIO()
        write_tarball(
            input_directory, tarball_io, verbose=verbose,
            encode_all=not allow_text, protected_output=out_filepath, encoding=args.encoding,
        )
        tarball_io.seek(0)
        text = tarball_io.read()

        if encode:
            text = base64.b64encode(text.encode()).decode()
            if obfuscate > 0:
                text = ''.join(f'{text[i:i+obfuscate]}~' for i in range(0, len(text), obfuscate))
            ####
        ####
        encoded_output = _encode_text(text, args.encoding)
        out_filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(out_filepath, 'wb') as fout:
            fout.write(encoded_output)
        ####
        print(f'Wrote {str(out_filepath)!r} ' + ('as encoded' if encode else ''))
    elif args.action == 'extract':
        tarball_path = Path(args.tarball_filename)
        decode = bool(args.decode)
        with open(tarball_path, 'r', encoding=args.encoding, newline='') as fin:
            data = fin.read()
        ####
        if decode:
            data = strip_non_b64(data)  # Just go ahead and strip non-b64
            data = base64.b64decode(data.encode()).decode()
        ####
        output_dirpath = Path(args.output_directory)
        extract_tarball(
            io.StringIO(data), output_dirpath, verbose=verbose,
            allow_legacy=args.legacy, protected_source=tarball_path, encoding=args.encoding,
        )
        print(f"Tarball {str(tarball_path)!r} extracted to {str(output_dirpath)!r}.")
    else:
        raise RuntimeError(f'Invalid action: {args.action}')
    ####
####

if __name__ == "__main__":
    main()
####
