#!/usr/bin/python
'''
 == Usage ==

 This script produces a neco/snakes Petri net out of a CFG.
 Usage: python cfg2net.py CFG_FILE

 CFG_FILE is a CFG described using the syntax below.


 == CFG syntax ==

 Each line ends with a semicolon, all text after a semicolon is
 considered as comment. You can put a semicolon at the beginning of a
 line to comment the whole line.

 The initial marking can be specified with the init statement:
 init place * threads;
 where 'init' is a keyword, place is a place name, and thread is the
 count of threads in this place. For example, " init p1*2; " means
 that there a two threads in place p1 at initial marking.

 Synchronisations, ie., barriers can be specified with the barrier
 statement:
 barrier place * threads;
 where barrier is a keyword, place is a place name, and threads is
 the count of threads needed to achieve synchronisation step. For
 example, " barrier p2*2; ".

 The transition relation is specified with transition statements:
 begin -> end;
 where begin is the entry place, and end the exit place.

 == Example ==

 ; initial state
 init p1*2;

 ; barriers
 barrier p2*2;

 ; transition relation
 p1 -> p2;
 p1 -> p3;
 p2 -> p4;
 p3 -> p4;
'''

import re, sys
from collections import defaultdict

def error(message, code=-1):
    print >> sys.stderr, message
    exit(code)

_next = 1
def next_thread():
    global _next
    n = _next
    _next += 1
    return n

def parse_model(model):
    # init place * threads
    header_reg  = re.compile("init\s*(?P<initial>\w+)\s*\*\s*(?P<threads>\d+)\s*;\s*")
    # barrier place
    barrier_reg = re.compile("barrier\s*(?P<barrier>\w+)\s*\*\s*(?P<count>\d+)\s*;\s*")
    # place -> place
    rule_reg = re.compile("\s*(?P<start>\w+)\s*->\s*(?P<end>\w+)\s*;\s*")
    # empty line
    empty_reg = re.compile("\s*\n")
    # comment line
    comment_reg = re.compile("\s*;")

    initial_states = {}
    barriers = {}
    states = set()
    transitions = defaultdict(set)

    line_num = 0
    for line in model:
        line_num += 1

        header_match = header_reg.match(line)
        barrier_match = barrier_reg.match(line)
        rule_match = rule_reg.match(line)
        empty_match = empty_reg.match(line)
        comment_match = comment_reg.match(line)

        if header_match:
            if len(header_match.groups()) != 2:
                error("syntax error, line {}".format(line_num))

            state = header_match.group('initial')
            threads = int(header_match.group('threads'))

            if state == '' or threads < 1:
                error("syntax error, line {}".format(line_num))

            if state in initial_states:
                error("initial state {} specified multiple times".format(state))
            initial_states[state] = threads

        elif barrier_match:
            if len(barrier_match.groups()) != 2:
                error("syntax error, line {}".format(line_num))

            barrier = barrier_match.group('barrier')
            count   = barrier_match.group('count')

            if barrier == '' or count < 1:
                error("syntax error, line {}".format(line_num))

            if barrier in barriers:
                error("barrier place {} specified multiple times".format(barrier))
            barriers[barrier] = count

        elif rule_match:
            start = rule_match.group('start')
            end   = rule_match.group('end')
            if not (start and end):
                error("syntax error, line {}".format(line_num))

            states.add(start)
            states.add(end)
            transitions[start].add(end)

        elif not (empty_match or comment_match):
            error("syntax error, line {}".format(line_num))

        for state in initial_states:
            states.add(state)

    return states, barriers, transitions, initial_states



if len(sys.argv) != 2:
    print "Usage: {} CFG_FILE".format(sys.argv[0])
    exit(-1)

file_name = sys.argv[1]
model = open(file_name)

states, barriers, transitions, initial_states = parse_model(model)

print "from neco.extsnakes import *"
print
print "net = PetriNet('net')"
print
print "################################################################################"
for place in sorted(states):
    print "# place {}".format(place)
    if place in initial_states:
        threads = initial_states[place]
        tokens = []
        for _ in range(threads):
            tokens.append("Pid.from_str('1.{}')".format(next_thread()))
        tokens = '[' + (', '.join(tokens)).format(*list(range(1, threads+1))) + ']'
    else:
        tokens = "[]"

    if place in barriers:
        print "net.add_place(Place('{}_i', {}, tPid))".format(place, tokens)
        print "net.add_place(Place('{}_o', [], tPid))".format(place)
    else:
        print "net.add_place(Place('{}', {}, tPid))".format(place, tokens)

print "################################################################################"
num = 0
for place_in, places_out in sorted(transitions.iteritems()):

    for place_out in places_out:
        print "# {} -> {} ".format(place_in, place_out)

        # placed in inner loop for printing
        if place_out in barriers:
            place_out += '_i'

        if place_in in barriers:
            place_in += '_o'

        num += 1
        print "net.add_transition(Transition('t{}', Expression('True')))".format(num)
        print "net.add_input('{}', 't{}', Variable('p'))".format(place_in, num)
        print "net.add_output('{}', 't{}', Variable('p'))".format(place_out, num)

print "################################################################################"
for barrier_place in sorted(barriers):
    num += 1
    print "# barrier {}*{}".format(barrier_place, barriers[barrier_place])
    place_in  = barrier_place + '_i'
    place_out = barrier_place + '_o'
    print "net.add_transition(Transition('t{}', Expression('len(X) == {}')))".format(num, barriers[barrier_place])
    print "net.add_input('{}', 't{}', Flush('X'))".format(place_in, num)
    print "net.add_output('{}', 't{}', Flush('X'))".format(place_out, num)

print
print "if __name__ == '__main__':"
print "    print 'writing net.ps'"
print "    net.draw('net.ps')"
