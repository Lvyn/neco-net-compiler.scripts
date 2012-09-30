"""
This script produces a pdf file from neco graph output (graph and map files).

bz2 and gz compression is supported, ie., if the extension input files is .bz2
or .gz2 they will be handled accordingly.

"""

import os, re, tempfile, subprocess, argparse, sys
import bz2
import gzip


parser = argparse.ArgumentParser(sys.argv[0])
parser.add_argument('--graph', '-g', default=None, dest='graph', metavar='GRAPH_FILE', type=str,
                    help='graph file.')
parser.add_argument('--map', '-m', default=None, dest='map', metavar='MAP_FILE', type=str,
                    help='graph file.')
parser.add_argument('--out', '-o', default='out.pdf', dest='out', metavar='OUT_FILE', type=str,
                    help='output file.')

args = parser.parse_args()

graph_file_name = args.graph
map_file_name = args.map
out_file_name = args.out

if not (graph_file_name and map_file_name and out_file_name) :
    parser.print_usage(sys.stderr)
    exit(-1)

index = out_file_name.rfind('.')
if out_file_name[index:] != '.pdf':
    print >> sys.stderr, "output file needs a '.pdf' extension"
    parser.print_usage(sys.stderr)
    exit(-1)
    
def open_file(filename):
    index = filename.rfind('.')
    if index == -1:
        return open(filename, 'r')

    ext = filename[index:]
    if ext == '.bz2':
        print "using bz2 decompression for {}".format(filename)
        return bz2.BZ2File(filename, 'r')
    elif ext == '.gz':
        print "using gzip decompression for {}".format(filename)
        return gzip.GzipFile(filename, 'r')
    else:
        print "unknown extension {}, read as regular file".format(ext)
        return open(filename) 

current_file = None
current_line = None

def setup_file_line(cf, cl = 0):
    global current_file
    global current_line
    current_file = cf
    current_line = cl

def incr_line():
    global current_line
    current_line += 1

def syntax_error(line):
    global current_file
    global current_line
    print >> sys.stderr, "syntax error: file {}, line {}".format(current_file, current_line)
    print >> sys.stderr, line
    exit(-1)

dot_map = { '"' : "\\\"",
            '{' : "\\{",
            '}' : "\\}",
            '[' : "\\[",
            ']' : "\\]",
            '|' : "\\|",
            '\\': "\\", }

def dot_protect_string(string):
    lstring = []
    for e in string:
        try:
            lstring.append( dot_map[e] )
        except KeyError:
            lstring.append(e)
    return ''.join(lstring)

#
# Parse map file
#

print "generating dot strings"

map_header = re.compile(r"(?P<id>\d*)\s*:\s*{")
empty_line = re.compile(r"\s*\n")
map_footer = re.compile(r"}")
map_dict = {}
map_file = open_file(map_file_name)

lines = ["digraph G {"]

setup_file_line(map_file_name)

while True:
    line = map_file.readline()
    if line == '':
        break
    incr_line()
    if empty_line.match(line):
        continue

    match = map_header.match(line)
    if not match:
        syntax_error(line)
        break

    ident = match.group('id')
    # consume
    count = 0
    label = ['{']
    while map_file:
        line = map_file.readline()
        if line == '':
            break
        incr_line()
        if empty_line.match(line):
            continue

        match = map_footer.match(line)
        if match:
            break

        if count > 0:
            label.append(' \l| ')
        label.append(dot_protect_string(line[:-1]))
        count += 1
    label.append('\l}')

    lines.append("\tnode{ident} [shape=record,label=\"{ident} | {label}\"];".format(ident=ident, label=''.join(label)))

#
# parse graph file
#
graph_file = open_file(graph_file_name)
graph_entry1 = re.compile(r"(?P<src>\d+)\s*:\s*\[(?P<dests>\s*\d+\s*(,\s*\d+)*)\]")
graph_entry2 = re.compile(r"(?P<src>\d+)\s*:\s*\[]")

setup_file_line(graph_file_name)
for line in graph_file:
    incr_line()
    if empty_line.match(line):
        continue
    match1 = graph_entry1.match(line)
    match2 = graph_entry2.match(line)
    if match1:
        src = match1.group('src')
        dests = match1.group('dests').split(',')
        for dest in dests:
            lines.append('\tnode{src!s} -> node{dest!s};'.format(src=int(src), dest=int(dest)))
    elif match2:
        continue
    else:
        syntax_error(line)

lines.append("}")


#
# write to file
#
tfile = tempfile.NamedTemporaryFile(delete=False)
print "writing dot file ({})".format(tfile.name)

tfile.write("\n".join(lines))
tfile.close()

#
# build pdf
#
command = "dot -Tpdf -o{output_file} {input_file}".format(output_file=out_file_name,
                                                          input_file=tfile.name)
print "produce pdf ({})".format(command)
subprocess.call(command.split(" "))

os.unlink(tfile.name)
