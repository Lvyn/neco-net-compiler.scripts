#!/usr/bin/python

from distutils.core import setup
import sys

std_paths = ['/usr', '/usr/', '/usr/local', '/usr/local/']
def has_non_std_prefix():
    for i, opt in enumerate(sys.argv):
        if opt.find('--prefix') == 0:
            if len(opt) > 8 and opt[8] == '=':
                path = opt[9:]
            else:
                path = sys.argv[i+1]
            if path not in std_paths:
                return path
    return None

setup(name='Neco_scipts',
      version='0.1',
      description='Neco Net Compiler additional scripts',
      author='Lukasz Fronc',
      author_email='lfronc@ibisc.univ-evry.fr',
      url='http://code.google.com/p/neco-net-compiler/',
      license='LGPL',
      scripts=['cfg2net/cfg2net.py',
               'cfg2pdf/cfg2pdf',
               'graph2pdf/graph2pdf.py'])

prefix = has_non_std_prefix()
if prefix:
    if prefix[-1] != '/':
        prefix += '/'

    print sys.version_info
    py_version = "{}.{}".format(sys.version_info.major, sys.version_info.minor)
    if py_version != '2.7':
        exit(-1)

    print
    print "[W] You are using a non standard prefix ({}) please add the following lines to your .bashrc file:".format(prefix)
    print
    print "export PATH=$PATH:{}bin".format(prefix)
    print
