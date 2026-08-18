# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path

import click
import yaml

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import wireviz.wireviz as wv
from wireviz import APP_NAME, __version__
from wireviz import wv_merge, wv_yaml
from wireviz.wv_errors import WireVizError
from wireviz.wv_helper import file_read_text

format_codes = {
    # "c": "csv",
    "g": "gv",
    "h": "html",
    "p": "png",
    # "P": "pdf",
    "s": "svg",
    "t": "tsv",
}

epilog = "The -f or --format option accepts a string containing one or more of the "
epilog += "following characters to specify which file types to output:\n"
epilog += ", ".join([f"{key} ({value.upper()})" for key, value in format_codes.items()])


@click.command(
    epilog=epilog,
    no_args_is_help=True,
    context_settings=dict(help_option_names=["-h", "--help"]),
)
@click.argument("file", nargs=-1)
@click.option(
    "-f",
    "--format",
    default="hpst",
    type=str,
    show_default=True,
    help="Output formats (see below).",
)
@click.option(
    "-p",
    "--prepend",
    default=[],
    multiple=True,
    type=Path,
    help="YAML file to prepend to the input file (optional).",
)
@click.option(
    "-o",
    "--output-dir",
    default=None,
    type=Path,
    help="Directory to use for output files, if different from input file directory.",
)
@click.option(
    "-O",
    "--output-name",
    default=None,
    type=str,
    help="File name (without extension) to use for output files, if different from input file name.",
)
@click.option(
    "-m",
    "--merge",
    is_flag=True,
    default=False,
    help="Treat all input FILEs as parts of ONE harness and render a single "
    "output, instead of rendering each file separately. Any --prepend files "
    "are prepended to each input in turn, so YAML anchors resolve per file.",
)
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Treat duplicate YAML keys and unreferenced components as errors "
    "rather than silently dropping them.",
)
@click.option(
    "-V",
    "--version",
    is_flag=True,
    default=False,
    help=f"Output {APP_NAME} version and exit.",
)
def wireviz(file, format, prepend, output_dir, output_name, merge, strict, version):
    """
    Parses the provided FILE and generates the specified outputs.
    """
    print()
    print(f"{APP_NAME} {__version__}")
    if version:
        return  # print version number only and exit

    # get list of files
    try:
        _ = iter(file)
    except TypeError:
        filepaths = [file]
    else:
        filepaths = list(file)

    # determine output formats
    output_formats = []
    for code in format:
        if code in format_codes:
            output_formats.append(format_codes[code])
        else:
            raise Exception(f"Unknown output format: {code}")
    output_formats = tuple(sorted(set(output_formats)))
    output_formats_str = (
        f'[{"|".join(output_formats)}]'
        if len(output_formats) > 1
        else output_formats[0]
    )

    # check prepend file
    if len(prepend) > 0:
        prepend_input = ""
        for prepend_file in prepend:
            prepend_file = Path(prepend_file)
            if not prepend_file.exists():
                raise Exception(f"File does not exist:\n{prepend_file}")
            print("Prepend file:", prepend_file)

            prepend_input += file_read_text(prepend_file) + "\n"
    else:
        prepend_input = ""

    filepaths = [Path(f) for f in filepaths]
    for file in filepaths:
        if not file.exists():
            raise Exception(f"File does not exist:\n{file}")

    image_paths = {f.parent for f in filepaths}
    for p in prepend:
        image_paths.add(Path(p).parent)

    def render(inp, _output_dir, _output_name):
        print(
            "Output file: ", f"{Path(_output_dir / _output_name)}.{output_formats_str}"
        )
        try:
            wv.parse(
                inp,
                output_formats=output_formats,
                output_dir=_output_dir,
                output_name=_output_name,
                image_paths=list(image_paths),
                strict=strict,
            )
        except WireVizError as e:
            # A clean message, not a traceback: these are input problems, and
            # under --strict they are the expected way to report them.
            raise SystemExit(f"Error: {e}")

    if merge:
        # One harness from many files. Each input is parsed on its own with the
        # prepended text in front of it, so anchors defined there resolve in
        # every file; the parsed results are then combined at the data level.
        # Concatenating the text instead would let a duplicate top-level key
        # silently discard an entire file's worth of definitions.
        # A list of pairs rather than a dict: the same file passed twice must
        # surface as a duplicate-component error, not silently deduplicate.
        sources = []
        for file in filepaths:
            print("Input file:  ", file)
            try:
                sources.append((
                    str(file),
                    wv_yaml.safe_load(prepend_input + file_read_text(file), strict=strict)
                    or {},
                ))
            except (WireVizError, yaml.YAMLError) as e:
                raise SystemExit(f"Error: {file}: {e}")
        try:
            merged = wv_merge.merge(sources)
        except WireVizError as e:
            raise SystemExit(f"Error: {e}")

        _output_dir = filepaths[0].parent if not output_dir else output_dir
        _output_name = filepaths[0].stem if not output_name else output_name
        render(merged, Path(_output_dir), _output_name)
    else:
        # run WireViz on each input file
        for file in filepaths:
            _output_dir = file.parent if not output_dir else output_dir
            _output_name = file.stem if not output_name else output_name

            print("Input file:  ", file)
            render(prepend_input + file_read_text(file), Path(_output_dir), _output_name)

    print()


if __name__ == "__main__":
    wireviz()
