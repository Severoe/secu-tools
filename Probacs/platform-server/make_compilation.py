#!/usr/bin/env python

import os, sys, time, requests
import os.path

from subprocess import Popen, PIPE
import django
django.setup()
from pfServer.models import *

hostserver = ""

def compile(task_id, target_os, compiler, version, name, dest_folder, invoke_format, flags, exenames, dest_name):
    """
    task_id: string, task id of this job
    target_os: string, target os for this task
    compiler: string, compiler name
    version: string, version number of this compiler
    src_path: string, the source code file path
    dest_folder: string, folder name where you want the executables and log to be
    invoke_format: string, how to invoke the compiler, example: cc_flags_source_-o_exename
    flags: string, combinations of flags to be used, comma seperated
    on_complete: callback function, takes a dictionary as argument
    def onComplete(task_info):
        '''
        keys = 'task_id', 'target_os', 'compiler', 'version', 'src_path', 'flag'
        'dest_folder', 'exename', 'out', 'err'
        '''
    """
    #test:
    # tmp = Task.objects.get(task_id=task_info['task_id'],flag=task_info['flag'])
    #print(tmp.exename)
    invoke_format = invoke_format.replace("_", " ")
    flag_list = flags.replace("_", " ").split(",")
    exelist = exenames.split(",")

    task_info = {"task_id": task_id,
                "target_os": target_os,
                "compiler": compiler,
                "version": version,
                # "src_path": src_path,
                "dest_folder": dest_folder}

    if os.name == 'nt':
        delimit = "\\"
    else:
        delimit = "/"

    # name, extension = src_path.split(delimit)[-1].split('.')

    if dest_folder[-1] == delimit:
        dest_folder = dest_folder[0:-1]

    if os.path.exists(dest_folder) and not os.path.isdir(dest_folder):
        sys.stderr.write("Output directory already exists!\n")
        sys.stderr.flush()
        exit(-1)

    if not os.path.exists(dest_folder):
        os.mkdir(dest_folder)

    dest_folder += delimit
    log_filename = dest_folder + name + ".log"
    log_file = open(log_filename, "w")

    ## check directory level
    src_dir = dest_folder+".."+delimit+"src"
    exe_path_prefix = ".."+delimit
    for f in os.listdir(src_dir):
        if os.path.isdir(os.path.join(src_dir, f)):
            src_dir += delimit+f
            exe_path_prefix += ".."+delimit
            break

    print("code folder: "+src_dir)
    print("compilation begins...")

    cnt = 0
    for flag,exefname in zip(flag_list,exelist):
        cnt += 1
        # time.sleep(2)

        # exefname = name.split(".")[0] + "_%d_%s"%(cnt, flag.replace(" ", "_"))
        exename = exe_path_prefix + dest_name + delimit+exefname
        # if os.name == 'nt':
        #     exefname = exefname.replace("/","-")
        #     exename = exename.replace("/","-")
        logline = "%s\t%s"%(exefname, flag)

        command = invoke_format.replace("flags", flag).replace("exename", exename).split(" ")
        # print(command)
        compilation = Popen(command, cwd = src_dir,stdout=PIPE, stderr=PIPE)
        out, err = compilation.communicate()
        # print(os.listdir(dest_folder))
        #check file existense\
        task_info['status'] = check_existence(dest_folder,exefname)
        log_file.write("%s, %s, %s\n"%(logline, out, err))

        # execute callback to notice the completion of a single compilation
        task_info['out'] = out
        task_info['err'] = out+b"\n"+err
        task_info['platform_folder'] = dest_name
        task_info['flag'] = flag

        on_complete(task_info)

    log_file.close()
    print("compilation done!")


def check_existence(dest_folder,exefname):
    print(dest_folder)
    for f in os.listdir(dest_folder):
        if str(f).startswith(exefname):
            print(exefname+" exists!")
            return "success"
    print(exefname+" not exists!")
    return "fail"

def on_complete(task_info):
    # send back compilation information back to host server
    # rcv_compilation
    print("update finished")
    data = task_info
    response = requests.post(hostserver+"rcv_compilation", data=data)
    return



if __name__ == "__main__":
    print(sys.argv)
    if len(sys.argv) != 12:

        sys.stderr.write("Usage: python make_compilation <source file> <output dir> <invoke_format> <flags>\n")

        sys.stderr.flush()

        exit(-1)
    hostserver = sys.argv[11]
    print(hostserver)
    cur_id = os.getpid()
    ## register pid with taskid
    new_task = CompilationPid(pid = cur_id,taskid=str(sys.argv[1]))
    new_task.save()

    print(cur_id)
    compile(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5],
            sys.argv[6], sys.argv[7], sys.argv[8], sys.argv[9],sys.argv[10])
    finished_task = CompilationPid.objects.get(pid=cur_id)
    # finished_task.delete()

    # do_compilation(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])