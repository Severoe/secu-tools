#!/usr/bin/env python

import os, sys, time, requests

from subprocess import Popen, PIPE


hostserver = ""

def compile(task_id, target_os, compiler, version, src_path, dest_folder, invoke_format, flags):
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

    task_info = {"task_id": task_id,
                "target_os": target_os,
                "compiler": compiler,
                "version": version,
                "src_path": src_path,
                "dest_folder": dest_folder}

    if os.name == 'nt':
        delimit = "\\"
    else:
        delimit = "/"

    name, extension = src_path.split(delimit)[-1].split('.')

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

    print("compilation begins...")
        
    cnt = 0
    for flag in flag_list:
        cnt += 1
        time.sleep(2)
        exename = dest_folder + name + "_%d_%s"%(cnt, flag.replace(" ", "_"))
        exename = exename.replace("/","-")
        logline = "%s\t%s"%(exename, flag)

        command = invoke_format.replace("flags", flag).replace("source", src_path).replace("exename", exename).split(" ")
        # print(command)
        compilation = Popen(command, stdout=PIPE, stderr=PIPE)
        out, err = compilation.communicate()
        log_file.write("%s, %s, %s\n"%(logline, out, err))
        
        # execute callback to notice the completion of a single compilation
        task_info['out'] = out
        task_info['err'] = err
        task_info['exename'] = exename
        task_info['flag'] = flag
        on_complete(task_info)

    log_file.close()
    print("compilation done!")


def on_complete(task_info):
    # send back compilation information back to host server
    # rcv_compilation
    print("update finished")
    data = task_info
    response = requests.post(hostserver+"rcv_compilation", data=data) 
    return



if __name__ == "__main__":
    print(sys.argv)
    if len(sys.argv) != 10:

        sys.stderr.write("Usage: python make_compilation <source file> <output dir> <invoke_format> <flags>\n")

        sys.stderr.flush()

        exit(-1)
    hostserver = sys.argv[9]
    compile(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4],sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8])

    # do_compilation(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])



    



    

