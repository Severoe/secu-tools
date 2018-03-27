#!/usr/bin/env python

import os
import sys
from subprocess import Popen, PIPE

cc = "gcc"
w_flags = ["-Wall", "-Wextra"]
o_flags = ["-O0", "-O1", "-O2", "-O3"]

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.stderr.write("Usage: python make_compilation <source file> <output dir>\n")
        sys.stderr.flush()
        exit(-1)

    source = sys.argv[1]
    name, extension = source.split('/')[-1].split('.')
    output_dir = sys.argv[2]
    if output_dir[-1] == '/':
        output_dir = output_dir[0:-1]

    if os.path.exists(output_dir) and not os.path.isdir(output_dir):
        sys.stderr.write("Output directory already exists!\n")
        sys.stderr.flush()
        exit(-1)
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    output_dir += '/'
    log_filename = output_dir + name + ".log"
    log_file = open(log_filename, "w")

    for i1, f1 in enumerate(w_flags):
        for i2, f2 in enumerate(o_flags):
            exe_name = output_dir + name + "_%d_%d"%(i1, i2)
            logline = "%s\t%s\t%s"%(exe_name, f1, f2)
            compilation = Popen([cc, f1, f2, source, '-o', exe_name], stdout=PIPE, stderr=PIPE)
            out, err = compilation.communicate()
            log_file.write("%s, %s, %s\n"%(logline, out, err))
    log_file.close()

    