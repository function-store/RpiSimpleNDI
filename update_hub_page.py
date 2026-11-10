#!/usr/bin/env python3
"""Copy the TDXMediaServe web page into templates/hub.html for hub_server.py.

The page comes from TDXMediaServe and is not part of this repository:
templates/hub.html is gitignored. Copy it on the machine that runs the hub,
from a TDXMediaServe checkout or from the page file itself:

    python3 update_hub_page.py --from /path/to/TDXMediaServe
    python3 update_hub_page.py --from /path/to/index.html
"""

import argparse
import os
import re
import subprocess
import sys

PAGE_IN_CHECKOUT = os.path.join('templates', 'index.html')
TARGET = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'hub.html')
STAMP = 'TDXMediaServe page copied from {source} by update_hub_page.py. Do not edit here: change the page in TDXMediaServe and copy it again.'


def git(folder: str, *args: str) -> str:
    return subprocess.run(['git', '-C', folder, *args], capture_output=True, text=True, check=True).stdout.strip()


def readPage(source: str) -> tuple:
    """The page and a label for where it came from: branch@commit for a checkout, the file name otherwise."""
    path = os.path.join(source, PAGE_IN_CHECKOUT) if os.path.isdir(source) else source
    with open(path, encoding='utf-8-sig') as file:
        page = file.read()
    folder = os.path.dirname(os.path.abspath(path))
    try:
        label = f"{git(folder, 'rev-parse', '--abbrev-ref', 'HEAD')}@{git(folder, 'rev-parse', '--short', 'HEAD')}"
        if git(folder, 'status', '--porcelain', '--', os.path.abspath(path)):
            label += '+uncommitted'
    except (OSError, subprocess.CalledProcessError):
        label = os.path.basename(path)
    return page, label


def stamped(page: str, source: str) -> str:
    """The page with the source comment after its doctype, replacing an earlier stamp."""
    page = re.sub(r'\n?<!-- TDXMediaServe page copied from .*? -->', '', page, count=1)
    comment = f'<!-- {STAMP.format(source=source)} -->'
    match = re.match(r'\s*<!DOCTYPE[^>]*>', page, re.IGNORECASE)
    if match:
        return page[:match.end()] + '\n' + comment + page[match.end():]
    return comment + '\n' + page


def main() -> None:
    parser = argparse.ArgumentParser(description='Copy the TDXMediaServe web page for hub_server.py.')
    parser.add_argument('--from', dest='source', required=True, help='A TDXMediaServe checkout, or the page file itself')
    args = parser.parse_args()

    try:
        page, label = readPage(args.source)
    except OSError as e:
        print(f'Could not read the page: {e}', file=sys.stderr)
        sys.exit(1)
    if 'nodes' not in page or '/browser' not in page:
        print('That page does not look like a protocol 2 TDXMediaServe page (no nodes list or /browser socket).', file=sys.stderr)
        sys.exit(1)
    with open(TARGET, 'w', encoding='utf-8', newline='\n') as file:
        file.write(stamped(page, label))
    print(f'Wrote {TARGET} from {label}')


if __name__ == '__main__':
    main()
