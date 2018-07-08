import os, tempfile, zipfile,tarfile, time,json
from subprocess import Popen, PIPE
from django.utils import timezone
from datetime import datetime
from wsgiref.util import FileWrapper
from django.shortcuts import render, redirect
from secuTool.forms import *
from secuTool.models import *
from django.core.files import File
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import requests
from django.conf import settings
from probacs_parser import parseTaskFile
from django.core import serializers
from io import BytesIO
import zipfile,io,base64
# Create your views here.
################################
# global variables
# winurl = 'http://172.16.165.132:8000'
# self_ip =
host_ip_gateway = settings.GATEWAY
enable_test = settings.ENABLE_LOCALTEST
print(enable_test)
self_ip = settings.LOCAL_IP
print(self_ip)
winurl = 'http://192.168.56.102:8000' #winurl for virtualbox
testurl = 'http://httpbin.org/post'  #test request headers
rootDir = 'Compilation_tasks/'
tempDir = 'temp/'
# the datastructure  is stored in settings
################################

def home(request):
    context = {}
    context['form'] = ProfileUserForm()
    return render(request,'secuTool/index.html',context)


def preview(request):
    # print(request.POST)
    context = {}
    src_filename = request.FILES['srcFile'].name  # llok into tar bar
    compiler_divided = {}
    if "compiler" in request.POST:
        compiler_divided['compiler'], compiler_divided['version'] = request.POST['compiler'].split(" ")

    taskName = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    message, params = process_files(request, taskName,  compiler_divided)
    # print(params)
    #######################################
    ## register task metadata table
    #######################################
    target_os_list = [param['target_os'] for param in params]
    compiler_full_list = [param['compiler']+" "+param['version'] for param in params]

    new_taskMeta = TaskMeta(task_id=taskName,username=params[0]['username'],tag=params[0]['tag'],
        src_filename=src_filename,target_os=", ".join(target_os_list),
        compiler_full=", ".join(compiler_full_list),profiles = ", ".join(params[0]['profile']))
    new_taskMeta.save()

    if message:
        return render(request, 'secuTool/test.html', {"message":message})
    rows = []
    seq = 1
    for param in params:
        # permute flags combination  from diff flags
        # print(param)
        jsonDec = json.decoder.JSONDecoder()
        flag_from_profile = []
        for profile_name in param['profile']:
            # print(profile_name)
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
    context = {}
    context['rows'] = rows
    # for row in rows:
    print(rows)
    context['taskid'] = taskName
    return render(request, 'secuTool/preview.html',context)


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


@csrf_exempt
@transaction.atomic
def param_upload(request):
    '''
    get updated compilation parameters from user, write db with new subtasks, deliver compilation tasks to
    platforms in asyn calls
    '''
    print(request.POST)
    task_name = request.POST['taskid']
    task_num = request.POST['taskCount']
    task_params = []
    #####################
    ##retrieve source file path/ name, config source path, output path, etc,
    #####################
    cur_taskMeta = TaskMeta.objects.get(task_id=task_name)
    filename = cur_taskMeta.src_filename
    taskFolder = rootDir+task_name
    codeFolder = taskFolder+"/"+"src"
    srcPath = codeFolder+"/"+filename
    #####################
    ## parse params from requests
    #####################
    # ensure all compilation on single machine with same compiler will be packed together
    single_vm_ref = {}
    vm_num = 0
    for i in range(int(task_num)):
        obj = {}
        task_id = 'tasks['+str(i)+']'
        os = task_id+'[os]'
        compiler = task_id+'[compiler]'
        profile = task_id+'[profile]'
        flag = task_id+'[flag]'
        username = task_id+'[username]'
        tag = task_id+'[tags]'
        ref_key = request.POST[os].strip()+"|"+request.POST[compiler].strip()
        # print(ref_key)
        if ref_key in single_vm_ref.keys():
            ## task already exists, pack extra flags
            obj = task_params[single_vm_ref[ref_key]]
            new_flags = request.POST[flag].split(",")
            new_flags = "_".join([ele.strip() for ele in new_flags])
            obj['flag'] = obj['flag']+","+new_flags
        else:
            ## no task with same destination, establish a new one
            obj['target_os'] = request.POST[os]
            compiler_full = request.POST[compiler].split(" ")
            obj['compiler'] = compiler_full[0]
            obj['version'] = compiler_full[1]
            obj['profile'] = request.POST[profile]
            obj['flag'] = request.POST[flag].split(",")
            obj['flag'] = "_".join([ele.strip() for ele in obj['flag']])
            obj['username'] = request.POST[username]
            obj['tags'] = request.POST[tag]
            single_vm_ref[ref_key] = vm_num
            vm_num += 1
            task_params.append(obj)
    #####################
    #form request format from obj for each task
    #####################
    # print(task_params)
    task_num = 0
    for param in task_params:
        task_compiler = Compiler_conf.objects.get(target_os=param['target_os'], compiler=param['compiler'],
        version=param['version'])
        task_http = task_compiler.ip + ":"+task_compiler.port+task_compiler.http_path

        #############################
        # add entries into task database
        for ele in param['flag'].split(","):
            new_task = Task(task_id=task_name,username=param['username'],
                tag=None if not 'tag' in param else param['tag'],
                src_file=filename,target_os=param['target_os'],
                compiler=param['compiler'],version=param['version'],flag=ele)
            new_task.save()
            task_num += 1

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
                compile(task_name, param['target_os'], param['compiler'], param['version'], srcPath, outputDir, task_compiler.invoke_format, param['flag'],on_complete)
                #new thread
                print("finished compile")
                os._exit(0)
            else:
                #parent process, simply return to client
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

    cur_taskMeta.compilation_num = task_num
    cur_taskMeta.save()
    response = {}
    response['taskid'] = task_name
    return HttpResponse(json.dumps(response),content_type="application/json")



def upload_to_platform(param,ip, compiler_invoke, taskName, taskFolder, codeFolder,mainSrcName):
    '''
    flags is compressed string used for make_compilation.py
    compiler_invoke is a string used for cmd line compilation
    codeFolder is the code directory path, need compress then send along
    '''
    #################################
    # form code archive for code folder
    #################################
    tarPath = taskFolder+'/'+'src.tar'
    print("inside upload "+codeFolder)
    os.system('cd '+taskFolder+' && tar cvf src.tar src/')
    #send request to specific platform servers
    runEnv = None
    if '&&' in compiler_invoke:
        runEnv = compiler_invoke.split('&&')[0]
        compiler_invoke = compiler_invoke.split('&&')[1]
    data = { 'Srcname':mainSrcName,'taskid':taskName,'command': compiler_invoke,'flags': param['flag'],
    'env':runEnv,'target_os':param['target_os'],'compiler':param['compiler'],'version':param['version'],'host_ip':param['host_ip']}
    print(data)
    files={'file':(tarPath, open(tarPath, 'rb'))}    #need file archive path
    pid = os.fork()
    if pid == 0:
        response = requests.post(ip, files=files,data=data)
        os._exit(0)
    else:
        return



#receive compiled task from win, need to save file at taskFolder
@csrf_exempt
def saveExe(request):
    taskFolder = request.POST['taskid']
    filename = request.FILES['file'].name
    basedir = rootDir+taskFolder+'/'
    #create 'secu_compile' folder to be default folder containing all the tasks
    if not os.path.exists(basedir+'secu_compile'):
        os.system('mkdir '+basedir+'secu_compile')
    # print(filename)
    basedir += 'secu_compile/'
    with open(basedir+filename,'wb+') as dest:
        for chunk in request.FILES['file'].chunks():
            dest.write(chunk)
    #untar archive, delete archive
    os.system('tar xvzf '+ basedir+filename+" -C "+basedir)
    os.system('rm '+basedir+filename)
    response = HttpResponse()
    response.write("file received")

    return response


#download files based on whole task level
def wrap_dir(request):
    taskFolder = request.POST['downloadtaskid']
    if taskFolder == None or taskFolder == "" or TaskMeta.objects.filter(task_id=taskFolder).count() == 0:
        message = "there is no corresponding tasks"
        return render(request, 'secuTool/test.html', {"message":message, "nav4":"active show"})
    print("taskFolder: "+taskFolder )

    #pack executables inside task folder, send back
    new_name = "archive_"+taskFolder+".tgz"
    current_rootDir = rootDir+taskFolder+'/'
    with tarfile.open(current_rootDir+new_name, "w:gz") as tar:
        tar.add(current_rootDir+'secu_compile', arcname=os.path.basename(current_rootDir+'secu_compile'))

    compressed_dir = open(current_rootDir+new_name,'rb')
    response = HttpResponse(compressed_dir,content_type='application/tgz')
    response['Content-Disposition'] = 'attachment; filename='+new_name
    # os.system("rm "+taskFolder+'/'+new_name)
    return response

@transaction.atomic
def check_status(request):
    ##KWARGS
    context = {}
    task_id = request.POST['task_id']
    flags = request.POST['flags']
    obj = Task.objects.all()
    empty_count = 0
    total_count = 5
    query_dict = {}

    if request.POST['task_id']==None:
        query_dict['task_id'] = None
        empty_count += 1
    else:
        request.POST['task_id'].split(",")

    if request.POST['flags']==None:
        query_dict['flag'] = None
        empty_count += 1
    else:
        request.POST['flags'].split(",")

    if request.POST['username']==None:
        query_dict['username'] = None
        empty_count += 1
    else:
        request.POST['username'].split(",")

    constraints = {"target_os__in": ['Linux']}
    print (Compiler_conf.objects.filter(**constraints).count())

    query_dict['compiler'] = None if request.POST['compilers']==None else request.POST['compilers'].split(",")
    query_dict['tag'] = None if request.POST['tag']==None else request.POST['tag'].split(",")
    # query_dict['profiles'] = None if request.POST['profiles']==None else request.POST['profiles'].split(",")
    print(query_dict)
    for key, val in query_dict.items():
        if obj == None:
            break
        if val == None or val==['']:
            continue
        else:
            if key=='task_id':
                obj = obj.filter(task_id__in=val)
            elif key=='flag':
                obj = obj.filter(flag__in=[ele.replace(" ","_") for ele in val])
            elif key=='username':
                obj = obj.filter(username__in=val)
            elif key=='compiler':
                obj = obj.filter(compiler__in=val)
            elif key=='tag':
                obj = obj.filter(tag__in=val)


    # obj = obj.filter({"task_id__in":val, })
    if obj.count() != Task.objects.all().count():
        context['tasks'] = obj
        for ele in context['tasks']:
            ele.flag = ele.flag.replace("_", " ")
            ele.status = 'not finished' if ele.exename == None else 'finished'
            ele.exename = '-' if not ele.exename else ele.exename
            ele.out = '-' if not ele.out else ele.out
            ele.err = '-' if not ele.err else ele.err
    context['nav3'] = "active show"
    # context['task_id'] = request.POST['task_id']
    return render(request, 'secuTool/test.html',context)




@transaction.atomic
@csrf_exempt
def rcv_platform_result(request):
    '''
    called when platform server sending back compilation result for each single compilation
    '''
    task = Task.objects.get(task_id=request.POST['task_id'],flag=request.POST['flag'].replace(" ","_"),
        target_os=request.POST['target_os'],compiler=request.POST['compiler'],version=request.POST['version'])
    # print("exename "+str(task.exename))
    #handle error case
    if task == None or task.exename != None:
        print('task already gone or already updated')
        return HttpResponse()
    task.exename = request.POST['exename']
    task.out = request.POST['out']
    task.err = request.POST['err']
    print(request.POST['out'], request.POST['err'])
    print('update from platform finished')
    task.save()
    # task = Task.objects.get(task_id=task_info['task_id'],flag=task_info['flag'].replace(" ","_"))
    # print("exename "+str(task.exename))
    return HttpResponse()


def on_complete(task_info):
    '''
    called when each time compilation finished
    '''
    response = requests.post(url=self_ip+"/rcv_compilation",data = task_info)
    return

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

# test funciton
def test(request):
    context = {}
    context['form'] = ProfileUserForm()
    context['nav1'] = "active show"
    profiles = Profile_conf.objects.values()
    profile_dict = {}
    for profile in profiles:
        target_os, compiler, name = profile["target_os"], profile["compiler"] + " " + profile["version"], profile["name"]
        if target_os not in profile_dict:
            profile_dict[target_os] = {}
        if compiler not in profile_dict[target_os]:
            profile_dict[target_os][compiler] = []
        profile_dict[target_os][compiler].append(name)

    context['json_profiles'] = json.dumps(profile_dict)
    # context['status'] = statuses
    return render(request, 'secuTool/test.html',context)

def redirect_trace(request):
    '''
    refresh ajax page, return first several tasks
    invoked whenever the tab has been clicked
    '''
    context = {}
    task_number = 5
    current_id = None
    if 'ongoing' in request.GET:
        current_id = request.GET['ongoing']
        context['ongoing_display'] = 'block'
    else:
        context['ongoing_display'] = 'none'
    ## now retrieve top five in database
    ## form a dictionary adn return
    tasks_report = []
    if current_id == None: #simply retrieve 5
        obj = TaskMeta.objects.all().order_by('-id')[:task_number]
        print(obj.count())
        for ele in obj:
            tasks_report.append(parse_taskMeta(ele, False))
    else:
        tasks_report.append(parse_taskMeta(TaskMeta.objects.get(task_id=current_id),True))
        obj = TaskMeta.objects.all().order_by('-id')
        task_number -= 1
        for ele in TaskMeta.objects.all().order_by('-id'):
            if ele.task_id == current_id:
                continue
            else:
                task_number -= 1
                tasks_report.append(parse_taskMeta(ele,False))
                if task_number == 0:
                    break
    print(tasks_report)
    context['nav4'] = "active show"
    context['tracing_tasks'] = tasks_report
    context['ongoing_tasks'] = current_id
    # context['status'] = statuses
    return render(request, 'secuTool/test.html',context)


def trace_task_by_id(request):
    '''
    trace task used for new ui, return
    '''
    task_id = request.GET['task_id']
    obj = Task.objects.filter(task_id=task_id)
    response = {}
    response['total'] = obj.count()
    finished = 0
    log_report = []
    for ele in obj:
        # printRcd(ele)
        # print(ele.exename == None)
        if ele.exename != None:
            finished+= 1
            new_log = {}
            new_log['exename'] = ele.exename.split("/")[-1]
            new_log['out'] = "-" if ele.out == "" else ele.out
            new_log['err'] = "-" if ele.err == "" else ele.err
            log_report.append(new_log)

    response['finished'] = finished
    response['task_id'] = task_id
    response['log_report'] = log_report
    return HttpResponse(json.dumps(response),content_type="application/json")

@csrf_exempt
def peek_profile(request):
    target_os = request.POST['target_os']
    compiler, version = request.POST['compiler'].split(' ')
    name = request.POST['name']

    profile = Profile_conf.objects.filter(name=name,
                                        target_os=target_os,
                                        compiler=compiler,
                                        version=version)

    num = profile.count()
    if num > 1:
        res = {"message":"Multiple profiles found with given information"}
    elif num < 1:
        res = {"message":"No profile matching given information"}
    else:
        res = {"target_os": profile[0].target_os,
                "compiler": profile[0].compiler,
                "version": profile[0].version,
                "name": profile[0].name,
                "uploader": profile[0].uploader,
                "upload_time": profile[0].upload_time.strftime("%Y-%m-%d-%H-%M-%S"),
                "flag": profile[0].flag}

    return HttpResponse(json.dumps(res), content_type="application/json")



@csrf_exempt
def addCompiler(request):
    if 'compiler_file' not in request.FILES:
        context = {'nav2':'active show', 'message':'No compiler file uploaded'}
        return render(request, "secuTool/test.html", context)

    compiler_conf_path = tempDir + request.FILES['compiler_file'].name
    with open(compiler_conf_path, 'wb+') as dest:
        for chunk in request.FILES['compiler_file'].chunks():
            dest.write(chunk)

    message, compiler = parseCompilerFile(compiler_conf_path)
    if message:
        return render(request, 'secuTool/test.html', {"message":message, "nav2":"active show"})


    new_compiler = Compiler_conf(target_os=compiler['target_os'],
                                    compiler=compiler['compiler'],
                                    version=compiler['version'],
                                    ip=compiler['ip'],
                                    port=compiler['port'],
                                    http_path=compiler['http_path'],
                                    invoke_format=compiler['invoke_format'])
    new_compiler.save()

    context = {"message":"New compiler added successfully",
                "nav2":"active show"}
    return render(request, "secuTool/test.html", context)

@csrf_exempt
def addProfile(request):
    if 'profile_file' not in request.FILES:
        context = {'nav2':'active show', 'message':'No profile file uploaded'}
        return render(request, "secuTool/test.html", context)

    profile_conf_path = tempDir + request.FILES['profile_file'].name
    with open(profile_conf_path, 'wb+') as dest:
        for chunk in request.FILES['profile_file'].chunks():
            dest.write(chunk)

    message, profile = parseProfileFile(profile_conf_path)
    if message:
        return render(request, 'secuTool/test.html', {"message":message, "nav2":"active show"})

    old_profile = Profile_conf.filter(target_os=profile['target_os'],
                            compiler=profile['compiler'],
                            version=profile['version'],
                            name=profile['name'])
    if old_profile.count() != 0:
        context={'message':'A profile with same os/compiler/version/name already exists', 'nav2': 'active show'}
        return render(request, 'secuTool/test.html', context)


    new_profile = Profile_conf(uploader=profile['uploader'],
                                upload_time=timezone.now(),
                                name=profile['name'],
                                target_os=profile['target_os'],
                                compiler=profile['compiler'],
                                version=profile['version'],
                                flag=json.dumps(profile['flag']))
    new_profile.save()

    context = {"message":"New profile added successfully",
                "nav2":"active show"}

    return render(request, "secuTool/test.html", context)

def manageProfile(request):
    context = {}
    profiles = Profile_conf.objects.values()
    rows = []
    for profile in profiles:
        p_dict = {"target_os": profile["target_os"],
                    "compiler": profile["compiler"],
                    "version": profile["version"],
                    "name": profile["name"],
                    "num_of_flag": len(json.loads(profile['flag']))
                    }
        rows.append(p_dict.copy())
    context["rows"] = rows
    return render(request, "secuTool/manageProfile.html", context)

def manageCompiler(request):
    context = {}
    compilers = Compiler_conf.objects.values()
    rows = []
    for compiler in compilers:
        c_dict = {"target_os": compiler['target_os'],
                    'compiler': compiler['compiler'],
                    'version': compiler['version'],
                    'ip': compiler['ip'],
                    'port': compiler['port'],
                    'http_path': compiler['http_path']}
        rows.append(c_dict.copy())
    context['rows'] = rows
    return render(request, "secuTool/manageCompiler.html", context)

# ajax function to show content of compiler configuration
@csrf_exempt
def getCompiler(request):
    compiler = Compiler_conf.objects.get(target_os=request.POST['target_os'],
                                        compiler=request.POST['compiler'],
                                        version=request.POST['version'])

    res = {}
    for key in ['target_os', 'compiler', 'version', 'ip', 'port', 'http_path', 'invoke_format']:
        res[key] = getattr(compiler, key)

    return HttpResponse(json.dumps(res), content_type="application/json ")

# ajax function to show content of profile
@csrf_exempt
def getProfile(request):
    profile = Profile_conf.objects.get(target_os=request.POST['target_os'],
                                            compiler=request.POST['compiler'],
                                            version=request.POST['version'],
                                            name=request.POST['name'])
    res = {}
    for key in ["target_os", "compiler", "version", "name", "flag", "uploader"]:
        res[key] = getattr(profile, key)
    res["upload_time"] = profile.upload_time.strftime("%Y-%m-%d-%H-%M-%S")
    return HttpResponse(json.dumps(res), content_type="application/json")

@csrf_exempt
def updateCompiler(request):
    if request.POST['submit'] == 'save':
        compiler = Compiler_conf.objects.get(target_os=request.POST['old_target_os'],
                                    compiler=request.POST['old_compiler'],
                                    version=request.POST['old_version'])
        for key in ['target_os', 'compiler', 'version', 'ip', 'port', 'http_path', 'invoke_format']:
            setattr(compiler, key, request.POST[key])

        compiler.save()
        return render(request, "secuTool/test.html", {'message':'Compiler successfully updated', 'nav2': 'active show'})
    else:
        d = {}
        for key in ['target_os', 'compiler', 'version', 'ip', 'port', 'http_path', 'invoke_format']:
            d[key] = request.POST[key]

        new_compiler = Compiler_conf(**d)
        new_compiler.save()
        return render(request, "secuTool/test.html", {'message':'New compiler successfully saved', 'nav2': 'active show'})


@csrf_exempt
def updateProfile(request):
    if request.POST['submit'] == 'save':
        profile = Profile_conf.objects.get(target_os=request.POST['old_target_os'],
                                    compiler=request.POST['old_compiler'],
                                    version=request.POST['old_version'],
                                    name=request.POST['old_name'])

        for key in ['target_os', 'compiler', 'version', 'name']:
            setattr(profile, key, request.POST[key])
        
        new_flag = map(lambda x: x.strip(), request.POST['flag'].splitlines())
        new_flag = filter(lambda x: x, new_flag)
        setattr(profile, 'flag', json.dumps(new_flag))

        profile.save()
        return render(request, "secuTool/test.html", {'message':'Profile successfully updated', 'nav2': 'active show'})

    else:
        d = {}
        for key in ['target_os', 'compiler', 'version', 'name', 'uploader']:
            d[key] = request.POST[key]
        d['upload_time'] = datetime.now()
        new_flag = map(lambda x: x.strip(), request.POST['flag'].splitlines())
        new_flag = filter(lambda x: x, new_flag)
        d['flag'] = json.dumps(new_flag)

        new_profile = Profile_conf(**d)
        new_profile.save()
        return render(request, "secuTool/test.html", {'message':'New profile successfully saved', 'nav2': 'active show'})




###########################################################################
###########################################################################
#########           BELOW ARE SOME HELPER/TEST FUNCTIONS       ############
###########################################################################
###########################################################################
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

def tracetest(request):
    return render(request, 'secuTool/blank.html')



def trace_test(request):
    obj = Task.objects.all()
    response = {}
    response['total'] = obj.count()
    finished = 0
    for ele in obj:
        # printRcd(ele)
        # print(ele.exename == None)
        if ele.exename != None:
            finished+= 1
    response['finished'] = finished

    return HttpResponse(json.dumps(response),content_type="application/json")

def trace(request):
    '''
    trace job status, INVOKED BY AJAX
    '''
    task_id = request.GET['task_id']
    obj = Task.objects.filter(task_id=task_id)
    response = {}
    response['total'] = obj.count()
    finished = 0
    for ele in obj:
        # printRcd(ele)
        # print(ele.exename == None)
        if ele.exename != None:
            finished+= 1
    response['finished'] = finished
    response['task_id'] = task_id
    return HttpResponse(json.dumps(response),content_type="application/json")



#used for database debugging
def printRcd(rcd):
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





##########################################
########## backup functions #############


@transaction.atomic
def rcvSrc(request):
    timestr = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    #create unique task forder for each task, inside which includes:
    # srcCode, <profiles>, compiled file & log,
    # the archive for downloading will be delete
    taskName = timestr
    taskFolder = rootDir+timestr
    codeFolder = taskFolder+"/"+"src"
    os.system("mkdir "+taskFolder)
    context = {}
    srcPath = ''
    #######################
    # handle bad submit request (attention, undergoing compilation info may be missing by rendering blank)
    #######################
    if 'src' not in request.FILES or 'task_file' not in request.FILES:
        return redirect(home)
    #######################
    #save source files in taskfolder
    #######################
    filename = request.FILES['src'].name
    taskfile = request.FILES['task_file'].name
    print(request.FILES['src'].content_type)
    if request.FILES['src'].content_type not in ['application/x-tar','application/gzip','application/zip']:
        #indicating a single file
        os.system("mkdir "+codeFolder)
        srcPath = codeFolder+"/"+filename
        with open(srcPath,'wb+') as dest:
            for chunk in request.FILES['src'].chunks():
                dest.write(chunk)
    else:
        #if user upload tar bar, extract and save into srcCode folder
        #also upload filename to be main filename
        with open(taskFolder+'/'+filename,'wb+') as dest:
            for chunk in request.FILES['src'].chunks():
                dest.write(chunk)
        os.system('tar xvzf '+ taskFolder+'/'+filename+" -C "+src)
        os.system('mv '+taskFolder+'/'+filename.split('.')[0]+' '+codeFolder)
        srcPath = codeFolder+"/"+filename
        # update filename to be the main srcfile name if tast srcfile is a tarball
    #######################
    # write task specify file to taskFolder
    #######################
    taskPath = taskFolder+"/"+taskfile
    with open(taskPath,'wb+') as dest:
        for chunk in request.FILES['task_file'].chunks():
            dest.write(chunk)


    #######################
    # parse task file
    #######################
    p = parseTaskFile(taskPath)
    print(p)
    message = p.get("message", None)
    if message != None:
        context['form']  = ProfileUserForm()
        context['message'] = message
        return render(request, 'secuTool/index.html',context)

    #form request format from parse.py for each task
    for param in p:
        task_compiler = Compiler_conf.objects.get(target_os=param['target_os'], compiler=param['compiler'],
        version=param['version'])
        task_http = task_compiler.ip + ":"+task_compiler.port+task_compiler.http_path
        # permute flags combination  from diff flags
        jsonDec = json.decoder.JSONDecoder()
        flag_from_profile = []
        for profile_name in param['profile']:
            # print(profile_name)
            p_tmp = Profile_conf.objects.get(name=profile_name, target_os=param['target_os'],compiler=param['compiler'],
                version=param['version'])
            flag_from_profile.append(jsonDec.decode(p_tmp.flag))
        compile_combination = [[]]
        for x in flag_from_profile:
            compile_combination = [i + [y] for y in x for i in compile_combination]
        compile_combination = [" ".join(x) for x in compile_combination]
        compile_combination = [x.replace(" ","_") for x in compile_combination]
        #############################
        # add entries into task database
        for ele in compile_combination:
            new_task = Task(task_id=taskName,username=param['username'],
                tag=None if not 'tag' in param else param['tag'],
                src_file=filename,target_os=param['target_os'],
                compiler=param['compiler'],version=param['version'],flag=ele)
            new_task.save()
        final_flags = ",".join(compile_combination)
        #############################
        # calling compilation tasks
        #############################
        if task_http == self_ip:
            outputDir = taskFolder+"/"+"secu_compile"
            data = {
            'task_id':taskName,'target_os':param['target_os'],'compiler':param['compiler'],'version':param['version'],'srcPath':srcPath,
            'output':outputDir,'format':task_compiler.invoke_format,'flags':final_flags,
            }
            pid = os.fork()
            if pid == 0:
                compile(taskName, param['target_os'], param['compiler'], param['version'], srcPath, outputDir, task_compiler.invoke_format, final_flags,on_complete)
                #new thread
                # os.system("python make_compilation.py "+srcPath+" "+ outputDir+" "+task_compiler.invoke_format+" "+final_flags)
                print("finished compile")
                os._exit(0)
            else:
                #parent process, simply return to client
                print("asyn call encountered")
        # if not compiling on linux host, send params to another function, interacting with specific platform server
        else:
            upload_to_platform(param,task_http, task_compiler.invoke_format, final_flags, taskName, taskFolder, codeFolder,filename)

    context['task_id'] = taskName
    context['message'] = "file is compiling..."
    context['form'] = ProfileUserForm()
    context['progress'] = 'block'
    context['linux_taskFolder'] = taskName
    return render(request, 'secuTool/index.html', context)
