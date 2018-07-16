from django.db.models import Q
import requests
from probacs_parser import parseTaskFile
import os, tempfile, zipfile,tarfile, time,json,signal
from subprocess import Popen, PIPE
from datetime import datetime
import django
django.setup()
from secuTool.models import *


## global variables
rootDir = 'Compilation_tasks/'
tempDir = 'temp/'


############################################################################
##################. helper function for preview ############################
############################################################################
def register_tasks(request):
    '''
    parse files from request, update taskMeta//records in database
    generate flag combinations,
    send back preview information
    '''
    src_filename = request.FILES['srcFile'].name  # llok into tar bar
    compiler_divided = {}
    if "compiler" in request.POST:
        compiler_divided['compiler'], compiler_divided['version'] = request.POST['compiler'].split(" ")

    task_created_time = datetime.now()
    taskName = task_created_time.strftime("%Y-%m-%d-%H-%M-%S")
    message, params = process_files(request, taskName, compiler_divided)
    if message:
        return message, None
    #######################################
    ## register task metadata table
    #######################################
    target_os_list = [param['target_os'] for param in params]
    compiler_full_list = [param['compiler']+" "+param['version'] for param in params]

    new_taskMeta = TaskMeta(task_id=taskName,username=params[0]['username'],tag=params[0]['tag'],
        src_filename=src_filename,target_os=", ".join(target_os_list),
        compiler_full=", ".join(compiler_full_list),profiles = ", ".join(params[0]['profile']),
        created_date=task_created_time)
    new_taskMeta.save()
    #######################################
    ## register subtasks into task table
    #######################################
    rows = []
    flag_list = []
    seq = 1
    for param in params:
        # permute flags combination  from diff flags
        jsonDec = json.decoder.JSONDecoder()
        flag_from_profile = []
        for profile_name in param['profile']:
            p_tmp = Profile_conf.objects.get(name=profile_name,
                                                target_os=param['target_os'],
                                                compiler=param['compiler'],
                                                version=param['version'])
            flag_from_profile.append(jsonDec.decode(p_tmp.flag))
        compile_combination = [[]]
        for x in flag_from_profile:
            compile_combination = [i + [y] for y in x for i in compile_combination]

        # each element in compile_combination is a space-separated flag list
        compile_combination = [" ".join(x) for x in compile_combination]
        profiles = ",".join(param['profile'])

        for flag in compile_combination:
            rows.append({'target_os':param['target_os'],
                            'compiler':param['compiler']+" "+param['version'],
                            'username':param['username'],
                            'profiles':", ".join(profiles.split(",")),
                            'tag':param['tag'],
                            'flag':", ".join(flag.split(" ")),
                            'seq':seq})
            seq += 1

        c_tmp = Compiler_conf.objects.get(target_os=param['target_os'],
                                compiler=param['compiler'],
                                version=param['version'])
        flag_list += jsonDec.decode(c_tmp.flag)

    return None, {"rows":rows,"flag_list":flag_list,"taskName":taskName}


def call_compile(task_params,enable_test,filename, taskFolder, codeFolder, srcPath, task_name, self_ip):
    '''
    receive subtask params, update task databse, calling compilations
    '''
    print(task_params)
    task_num = 0
    for param in task_params:
        task_compiler = Compiler_conf.objects.get(target_os=param['target_os'], compiler=param['compiler'],
        version=param['version'])
        task_http = task_compiler.ip + ":"+task_compiler.port+task_compiler.http_path
            ## check server accessibility
        if not enable_test:
            try:
                response = requests.get(task_http+"/heartbeat", timeout=10)
            except:
                return 0,False
        #############################
        # add entries into task database
        for ele in param['flag'].split(","):
            task_num += 1
            new_task = Task(task_id=task_name,username=param['username'],
                tag=param['tags'],
                src_file=filename,target_os=param['target_os'],
                compiler=param['compiler'],version=param['version'],
                flag=ele,init_tmstmp=datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
                exename=getExename(filename,ele,task_num),
                status="ongoing")
            new_task.save()

        #############################
        # calling compilation tasks
        #############################
        if enable_test:
            outputDir = taskFolder+"/"+"secu_compile"
            data = {
            'task_id':task_name,'target_os':param['target_os'],'compiler':param['compiler'],'version':param['version'],'srcPath':srcPath,
            'output':outputDir,'format':task_compiler.invoke_format,'flags':param['flag']}
            import os
            pid = os.fork()
            if pid == 0:
                compile(task_name, param['target_os'], param['compiler'], param['version'], srcPath, outputDir, task_compiler.invoke_format, param['flag'],on_complete, self_ip)
                #new thread
                print("finished compile")
                os._exit(0)
            else:
                #parent process, simply return to client
                cur_id = pid
                # print(cur_id)
                new_task = CompilationPid(pid = cur_id,taskid=task_name)
                new_task.save()
                print("asyn call encountered")
        # if not compiling on linux host, send params to another function, interacting with specific platform server
        else:
            ## if compile on same machine but diff port, using self_ip
            self_ip_addr = self_ip.split(":")
            if task_compiler.ip == self_ip_addr[0]+":"+self_ip_addr[1]:
                param['host_ip'] = self_ip
            else:
                param['host_ip'] = host_ip_gateway
            print(param['host_ip'])
            upload_to_platform(param,task_http, task_compiler.invoke_format, task_name, taskFolder, codeFolder,filename)
    return task_num,True


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
    empty_count = 0
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
        f = "%m/%d/%Y"
        context['date_after'] = request.POST['date_after']
        date_obj = datetime.strptime(request.POST['date_after'], f).strftime("%Y-%m-%d %H-%M-%S")
        query_dict['init_tmstmp__gte'] = date_obj

    if 'date_before' not in request.POST or request.POST['date_before']=="":
        empty_count += 1
    else:
        f = "%m/%d/%Y"
        context['date_before'] = request.POST['date_before']
        date_obj = datetime.strptime(request.POST['date_before'], f).strftime("%Y-%m-%d %H-%M-%S")
        query_dict['init_tmstmp__lte'] = date_obj

    return empty_count, query_dict, flags, compilers, context

def form_search_response(query_dict,flags,compilers,context):
    obj = Task.objects.filter(**query_dict)
    if flags != None:
        obj = obj.filter(flags)
    if compilers != None:
        obj = obj.filter(compilers)

    context['tasks'] = obj
    seq = 0
    for ele in context['tasks']:
        if ele.status != "success":
            ele.ifenable = "disabled"
        ele.seq = seq
        seq+=1
        if ele.target_os == 'Windows':
            delimit = "\\"
        else:
            delimit = "/"
        ele.flag = ele.flag.replace("_", " ")
        if not ele.exename:
            ele.err = "-"
            ele.exename = "-"
        else:
            ele.exename = ele.exename.split(delimit)[-1]
            if not ele.err:
                ele.err = '-'

    return context, obj




############################################################################
##################. helper function for compilation ##################
############################################################################

def compile(task_id, target_os, compiler, version, src_path, dest_folder, invoke_format, flags, on_complete, self_ip):
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
        compilation = Popen(command, stdout=PIPE, stderr=PIPE)
        out, err = compilation.communicate()
        log_file.write("%s, %s, %s\n"%(logline, out, err))

        # execute callback to notice the completion of a single compilation
        task_info['out'] = out
        task_info['err'] = err
        task_info['exename'] = exename
        task_info['flag'] = flag
        on_complete(task_info, self_ip)


    log_file.close()
    print("compilation done!")
    return


def on_complete(task_info, self_ip):
    '''
    called when each time self compilation finished
    '''
    response = requests.post(url=self_ip+"/rcv_compilation",data = task_info)
    return

############################################################################
##################. helper function for termination ##################
############################################################################
def terminate_process(task_id,subtasks, enable_test):
    if enable_test: 
        ongoing_process = CompilationPid.objects.filter(taskid=task_id)
        for ele in ongoing_process:
            pid = ele.pid
            os.kill(pid, signal.SIGTERM)
        # ongoing_process.delete()
        
    else:
        obj = subtasks[0]
        compiler_info = Compiler_conf.objects.get(target_os=obj.target_os,compiler=obj.compiler,version=obj.version)
        address = compiler_info.ip+":"+compiler_info.port+"/terminate"
        response = requests.post(address, data={"task_id":task_id})


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