#!/usr/bin/env python

import sys

if sys.version_info < (3, 6, 0):
    sys.stderr.write("You need python 3.6 or later to run this script\n")
    sys.exit(1)

from pathlib import Path
import argparse
import re


gc_args       = None
g_src         = 'Src'
gc_ini        = r"\binitialise_monitor_handles\b"
gc_std_set    = (
                r"\bprintf\b"
                r"|\bscanf\b"
                r"|\bsprintf\b"
                r"|\bfopen\b"
                r"|\bfwrite\b"
                r"|\bfclose\b"
)
gc_dslash_ex  = re.compile(r"^\s*\/\/")
gc_ini_ex     = re.compile(gc_ini)
gc_std_ex     = re.compile(gc_std_set)
gc_all_ex     = re.compile(gc_ini + '|' + gc_std_set)

gc_arg_set    = ['on', 'off', 'remove', 'removeall']


def consume_line(line):
    """
    Returns the (source) line; makes it commented/uncommented, as appropriate.
    If the line is to be dropped, returns (True, line).
    """
    if gc_args.trace_on == gc_arg_set[0]: # on:        Remove comments, if any.
        if gc_all_ex.findall(line) and gc_dslash_ex.match(line):
            return False, gc_dslash_ex.sub("", line, 1)
        return False, line
    if gc_args.trace_on == gc_arg_set[1]: # off:       Comment out, if not commented.
        if gc_all_ex.findall(line) and not gc_dslash_ex.match(line):
            return False, '//' + line
        return False, line
    if gc_args.trace_on == gc_arg_set[2]: # remove:    Remove uncommented std lines.
        if gc_ini_ex.findall(line) and not gc_dslash_ex.match(line):
            return False, '//' + line
        if gc_std_ex.findall(line) and not gc_dslash_ex.match(line):
            return True, line
        return False, line
    if gc_args.trace_on == gc_arg_set[3]: # removeall: Remove every std line.
        if gc_ini_ex.findall(line) and not gc_dslash_ex.match(line):
            return False, '//' + line
        if gc_std_ex.findall(line):
            return True, line
        return False, line
    return False, line

g_newline = ''

def current_nl(f):
    global g_newline

    if g_newline:
        return g_newline
    g_newline = f.newlines
    if isinstance(g_newline, tuple):
        print('!!! Bad Newline\n')
        return '\n'
    return g_newline

def check_file(path):
    header = f'*** {str(path)}'
    out_line = ""
    with open(path, "r") as f_r:
        first_change = True
        for line in f_r.readlines():
            drop_it, o_line = consume_line(line)
            if drop_it:
                if first_change:
                    first_change = False
                    print(header)
                print(f'Removed: {o_line.rstrip()}')
            else:
                out_line += o_line.rstrip('\n') + current_nl(f_r)
            if not drop_it and gc_all_ex.findall(o_line):
                if first_change:
                    first_change = False
                    print(header)
                print(o_line.rstrip())
    with open(path, "w") as f_w:
        f_w.write(out_line)


def check_src_dir():
    src = Path(g_src)
    if src.is_dir():
        print(f'Inspecting "{str(Path.cwd().joinpath(src))}" source directory\n')
        for i in src.glob('*.c'):
            if i.is_file():
                check_file(i)


def retrieve_args():
    parser = argparse.ArgumentParser(description='''
    Trace enabled by uncommenting printf(), etc. lines, disabled by commenting them.
    ''')

    parser.add_argument('trace_on',
                    help='on: uncomment trace statements, off: comment them out')

    rg = parser.parse_args()
    return rg


def main():
    global gc_args

    gc_args = retrieve_args()

    if gc_args.trace_on not in gc_arg_set:
        print(f'Unrecognized option "{gc_args.trace_on}"')
        sys.exit()

    check_src_dir()


if __name__ == '__main__':
    main()
