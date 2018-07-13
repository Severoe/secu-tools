from django.db.models import Q
import requests
from probacs_parser import parseTaskFile
import os, tempfile, zipfile,tarfile, time,json
from subprocess import Popen, PIPE
from datetime import datetime

from secuTool.models import *

## global variables
rootDir = 'Compilation_tasks/'
tempDir = 'temp/'


############################################################################
##################. helper function for preview ############################
############################################################################
def process_files(request, taskName, compiler_divided):
    """
    save and extract source code, and parse task file (or task form)
    :type request: http request obbject
    :type taskName: str, name of this task
    :rtype: tuple
        tuple[0] = message
        tuple[1] = list of dictionary, each element is the information of a task
    """
    taskFolder = rootDir + taskName
    srcFolder = taskFolder + "/src"
    os.mkdir(taskFolder)
    os.mkdir(srcFolder)

    srcPath = srcFolder + "/" + request.FILES['srcFile'].name
    with open(srcPath, 'wb+') as dest:
        for chunk in request.FILES['srcFile'].chunks():
            dest.write(chunk)

    cmd = None
    if request.FILES['srcFile'].content_type == 'application/x-tar':
        cmd = ['tar', 'xf', srcPath, '-C', srcFolder]
    elif request.FILES['srcFile'].content_type == 'application/gzip':
        cmd = ['tar', 'xzf', srcPath, '-C', srcFolder]
    elif request.FILES['srcFile'].content_type == 'application/zip':
        cmd = ['unzip', srcPath, '-d', srcFolder]

    if cmd:
        extract = Popen(cmd, stdout=PIPE, stderr=PIPE)
        _, err = extract.communicate()
        if err:
            return 'error occured when extracting file. \n%s'%err, None

    # user specified task through UI, not file, then save it to disk
    if 'taskFile' not in request.FILES:
        with open(taskFolder + "/task.txt", 'w') as dest:
            for key in ['compiler', 'version']:
                dest.write(key + ":" + compiler_divided[key] + "\n")
            for key in ['target_os', 'username']:
                dest.write(key + ":" + request.POST[key] + "\n")
            for key in ['profile']:
                # print(dict(request.POST))
                dest.write(key + ":" + ",".join(dict(request.POST)[key]) + "\n")
            if 'tag' in request.POST:
                dest.write('tag:' + request.POST['tag'] + "\n")
    else:
        with open(taskFolder + '/task.txt', 'wb+') as dest:
            for chunk in request.FILES['taskFile'].chunks():
                dest.write(chunk)

    return parseTaskFile(taskFolder + '/task.txt')


#################################################################
##################. helper function for search ##################
#################################################################
def construct_querySet(request):
    '''
	parse search request, form regular queryset, compiler filter and flags flter
	return those three and a empty count
	'''
    # 2018-07-02 16:08
    empty_count = 0;
    flags = None
    compilers = None
    query_dict = {}
    context = {}

    if 'task_id' not in request.POST or request.POST['task_id']=="":
        empty_count += 1
    else:
        context['task_id'] = request.POST['task_id']
        query_dict["task_id__in"] = request.POST['task_id'].split(",")
        query_dict['task_id__in'] = [ele.strip() for ele in query_dict['task_id__in']]

    if 'flags' not in request.POST or request.POST['flags']=="":
        flags = None
        empty_count += 1
    else:
        context['flags'] = request.POST['flags']
        flags_filter = Q()
        for flag in request.POST['flags'].split(","):
            flags_filter |= Q(flag__icontains = flag.strip())
        flags = flags_filter

    if 'username' not in request.POST or request.POST['username']=="":
        empty_count += 1
    else:
        context['username'] = request.POST['username']
        query_dict['username__in'] = request.POST['username'].split(",")
        query_dict['username__in'] = [ele.strip() for ele in query_dict['username__in']]

    if 'compilers' not in request.POST or request.POST['compilers']=="":
        empty_count += 1
    else:
        context['compilers'] = request.POST['compilers']
        compiler_dict = {}
        for ele in request.POST['compilers'].split(","):
            divide = ele.strip().split(" ")
            query_key = divide[0].lower()
            query_val = divide[1]
            if query_val == "*":
                compiler_dict[query_key]= None
            else:
                if query_key in compiler_dict.keys() and compiler_dict[query_key] != None:
                    compiler_dict[query_key].append(query_val)
                elif query_key not in compiler_dict.keys():
                    compiler_dict[query_key] = [query_val]
        print(compiler_dict)
        compiler_filter = Q()
        for key, val in compiler_dict.items():
            if key == "*":
                if val == None:
                    compiler_filter |= Q(compiler__icontains="")
                else:
                    compiler_filter |= Q(version__in=val)
            elif val == None:
                compiler_filter |= Q(compiler__icontains=key)
            else:
                compiler_filter |= Q(compiler__icontains=key, version__in=val)
        compilers = compiler_filter

    if 'tag' not in request.POST or request.POST['tag']=="":
        empty_count += 1
    else:
        context['tag'] = request.POST['tag']
        query_dict['tag__in'] = request.POST['tag'].split(",")
        query_dict['tag__in'] = [ele.strip() for ele in query_dict['tag__in']]

    if 'date_after' not in request.POST or request.POST['date_after']=="":
        empty_count += 1
    else:
        # f = "%Y-%m-%d %H:%M"
        f = "%m/%d/%Y"
        context['date_after'] = request.POST['date_after']
        date_obj = datetime.strptime(request.POST['date_after'], f).strftime("%Y-%m-%d %H-%M-%S")
        query_dict['init_tmstmp__gte'] = date_obj

    if 'date_before' not in request.POST or request.POST['date_before']=="":
        empty_count += 1
    else:
        # f = "%Y-%m-%d %H:%M"
        f = "%m/%d/%Y"
        context['date_before'] = request.POST['date_before']
        date_obj = datetime.strptime(request.POST['date_before'], f).strftime("%Y-%m-%d %H-%M-%S")
        query_dict['init_tmstmp__lte'] = date_obj

    return empty_count, query_dict, flags, compilers, context




############################################################################
##################. helper function for local compilation ##################
############################################################################

def compile(task_id, target_os, compiler, version, src_path, dest_folder, invoke_format, flags, on_complete):
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
    ##
    ## what if gcc with diff version ? -> overwritten log file
    ##
    dest_folder += delimit
    log_filename = dest_folder + name + ".log"
    log_file = open(log_filename, "w")

    print("compilation begins...")

    cnt = 0
    for flag in flag_list:
        cnt += 1
        time.sleep(2)
        exename = dest_folder + name + "_%d_%s"%(cnt, flag.replace(" ", "_"))
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
    return



############################################################################
##################. other helper function ##################################
############################################################################

def getExename(filename,ele,num):
    '''
	construct exename based on sourcefile name and flags as well as sequence number
	'''
    return ".".join(filename.split(".")[:-1])+"_"+str(num)+"_"+ele



def parse_taskMeta(ele, iscur):
    '''
    parse taskMeta object to be valid object in django template
    '''
    tmp = {}
    tmp['taskname'] = ele.task_id
    tmp['target_os'] = ele.target_os
    tmp['compiler'] = ele.compiler_full
    tmp['profiles'] = ele.profiles
    tmp['username'] = ele.username
    tmp['tag'] = ele.tag
    tmp['total'] = ele.compilation_num
    tmp['submittime'] = ".".join(ele.task_id.split("-")[:3])+" "+":".join(ele.task_id.split("-")[3:])
    if iscur:
        tmp['current_task']="background: yellow;"
    return tmp

############################################################################
##################. helper function for tracking ############################
############################################################################
def form_log_report(obj):
    finished = 0
    log_report = []
    for ele in obj:
        # get os type, define delimit
        if ele.target_os == 'Windows':
            delimit = "\\"
        else:
            delimit = "/"
        new_log = {}
        new_log['exename'] = ele.exename#.split(delimit)[-1]
        new_log['status'] = ele.status
        if ele.status == "ongoing":
            new_log['err'] = "-"
        else:
            finished+=1
            new_log['err'] = "-" if ele.err == "" else ele.err
        # if ele.finish_tmstmp == "" or ele.finish_tmstmp == None: #ongoing
        #     new_log['err'] = "-"
        #     new_log['status'] = "ongoing"
        # else:
        #     finished += 1
        #     new_log['status'] = "success" if ele.err == "" or ele.err == "-" else "fail"
        #     new_log['err'] = "-" if ele.err == "" else ele.err
        log_report.append(new_log)
    return finished, log_report

############################################################################
##################. helper function for database ##################
############################################################################
def printRcd(rcd):
    '''
	used for database debugging,schema can be changed
	'''
    print("============rcd report")

    if rcd == None:
        print('rcd not exists')
        return
    print("id: "+ str(rcd.task_id))
    print("flag: "+ str(rcd.flag))
    print("exename: "+ str(rcd.exename))
    print("err: "+ str(rcd.err))
    print("out: "+ str(rcd.out))

    return




