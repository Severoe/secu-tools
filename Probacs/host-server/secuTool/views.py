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
from django.db.models import Q
from helper import *
# Create your views here.
################################
# global variables
# winurl = 'http://172.16.165.132:8000'
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


##############################################################################################
##############################################################################################
##################. function for main page ################################################
##############################################################################################
def home(request):
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


##############################################################################################
##############################################################################################
##################. function for preview page ################################################
##############################################################################################

def preview(request):
    # print(request.POST)
    context = {}
    src_filename = request.FILES['srcFile'].name  # llok into tar bar
    compiler_divided = {}
    if "compiler" in request.POST:
        compiler_divided['compiler'], compiler_divided['version'] = request.POST['compiler'].split(" ")

    task_created_time = datetime.now()
    taskName = task_created_time.strftime("%Y-%m-%d-%H-%M-%S")
    message, params = process_files(request, taskName,  compiler_divided)
    # print(params)
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
    context['json_flags'] = json.dumps(['-Wall', '-Wextra', '-O1', '/WX', '/Od'])
    return render(request, 'secuTool/preview.html',context)


##############################################################################################
##############################################################################################
##################. function for compilation redirect ########################################
##############################################################################################

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
            task_num += 1
            new_task = Task(task_id=task_name,username=param['username'],
                tag=param['tags'],
                src_file=filename,target_os=param['target_os'],
                compiler=param['compiler'],version=param['version'],
                flag=ele,init_tmstmp=datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
                exename=getExename(filename,ele,task_num))
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

def on_complete(task_info):
    '''
    called when each time self compilation finished
    '''
    response = requests.post(url=self_ip+"/rcv_compilation",data = task_info)
    return


##############################################################################################
##############################################################################################
##################. function for saving compilation results && download request ##############
##############################################################################################

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

def wrap_dir(request):
    '''
    download files based on whole task level
    '''
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

@csrf_exempt
def download_search(request):
    ## remains earcgh params when privide dowload
    obj = dict(request.POST)
    print(obj['exe_pair'])
    new_name = "archive_searchReqest.tgz"
    with tarfile.open(new_name, "w:gz") as tar:
        for ele in obj['exe_pair']:
            taskFolder,exename = ele.split("$%$") 
            exe_path = rootDir+taskFolder+"/secu_compile/"+exename
            tar.add(exe_path, arcname=os.path.join(taskFolder,exename))
    compressed_dir = open(new_name,'rb')
    response = HttpResponse(compressed_dir,content_type='application/tgz')
    response['Content-Disposition'] = 'attachment; filename='+new_name
    return response


##############################################################################################
##############################################################################################
##################. function for search page #################################################
##############################################################################################


def search_panel(request):
    context = {}
    context['nav3'] = "active show"
    return render(request, 'secuTool/test.html',context)

@transaction.atomic
def check_status(request):    
    '''
    called when search request encountered
    '''
    total_count = 7
    empty_count, query_dict, flags, compilers, context = construct_querySet(request)
    context['nav3'] = "active show"

    if empty_count == total_count:
        context['search_result'] = "-- Showing 0 result of user request."
        return render(request, 'secuTool/test.html',context)

    print(query_dict)
    obj = Task.objects.filter(**query_dict)
    if flags != None:
        obj = obj.filter(flags)
    if compilers != None:
        obj = obj.filter(compilers)

    context['tasks'] = obj
    seq = 0
    for ele in context['tasks']:
        ele.seq = seq
        seq+=1
        if ele.target_os == 'Windows':
            delimit = "\\"
        else:
            delimit = "/"
        ele.flag = ele.flag.replace("_", " ")
        if not ele.exename:
            ele.status = "running"
            ele.err = "-"
            ele.exename = "-"
        else:
            ele.exename = ele.exename.split(delimit)[-1]
            if not ele.err:
                ele.status = 'success'
                ele.err = '-'
            else:
                ele.status = 'fail'
    context['search_result'] = "-- Showing "+str(obj.count())+" results of user request."
    return render(request, 'secuTool/test.html',context)


##############################################################################################
##############################################################################################
##################. function for ajax tracking/ update########################################
##############################################################################################





@transaction.atomic
@csrf_exempt
def rcv_platform_result(request):
    '''
    called when platform server sending back compilation result for each single compilation
    '''
    task = Task.objects.get(task_id=request.POST['task_id'],flag=request.POST['flag'].replace(" ","_"),
        target_os=request.POST['target_os'],compiler=request.POST['compiler'],version=request.POST['version'])
    task.out = request.POST['out']
    task.err = request.POST['err']
    task.finish_tmstmp=datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    print(request.POST['out'], request.POST['err'])
    print('update from platform finished')
    task.save()
    # task = Task.objects.get(task_id=task_info['task_id'],flag=task_info['flag'].replace(" ","_"))
    # print("exename "+str(task.exename))
    return HttpResponse()


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
        # get os type, define delimit
        if ele.target_os == 'Windows':
            delimit = "\\"
        else:
            delimit = "/"
        new_log = {}
        new_log['exename'] = ele.exename#.split(delimit)[-1]
        if ele.finish_tmstmp == "" or ele.finish_tmstmp == None: #ongoing
            new_log['err'] = "-"
            new_log['status'] = "ongoing"
        else:
            finished += 1
            new_log['status'] = "success" if ele.err == "" or ele.err == "-" else "fail"
            new_log['err'] = "-" if ele.err == "" else ele.err


        log_report.append(new_log)

    response['finished'] = finished
    response['task_id'] = task_id
    response['log_report'] = log_report
    return HttpResponse(json.dumps(response),content_type="application/json")

##############################################################################################
##############################################################################################
##################. function for profile/compiler configuration management ##################
##############################################################################################

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
                                upload_time=datetime.now(),
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
    profile_dict = {}
    for profile in profiles:
        target_os, compiler, version = profile["target_os"], profile["compiler"], profile["version"]
        p_dict = {"target_os": target_os,
                    "compiler": compiler,
                    "version": version,
                    "name": profile["name"],
                    "flag": ", ".join(json.loads(profile['flag'])),
                    "date": profile['upload_time'].strftime("%Y-%m-%d %H:%M:%S")
                    }
        rows.append(p_dict.copy())
        if target_os not in profile_dict:
            profile_dict[target_os] = {}
        if compiler not in profile_dict[target_os]:
            profile_dict[target_os][compiler] = []
        if version not in profile_dict[target_os][compiler]:
            profile_dict[target_os][compiler].append(version)

    context["rows"] = rows
    context['json_profiles'] = json.dumps(profile_dict)
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
    res["upload_time"] = profile.upload_time.strftime("%Y-%m-%d %H:%M:%S")
    return HttpResponse(json.dumps(res), content_type="application/json")

@csrf_exempt
def updateCompiler(request):
    if request.POST['submit'] == 'save':    #update existing one
        compiler = Compiler_conf.objects.get(target_os=request.POST['old_target_os'],
                                    compiler=request.POST['old_compiler'],
                                    version=request.POST['old_version'])
        for key in ['target_os', 'compiler', 'version', 'ip', 'port', 'http_path', 'invoke_format']:
            setattr(compiler, key, request.POST[key])

        compiler.save()
        return render(request, "secuTool/test.html", {'message':'Compiler successfully updated', 'nav2': 'active show'})
    else:           #save as new
        compiler = Compiler_conf.objects.filter(target_os=request.POST['target_os'],
                                                compiler=request.POST['compiler'],
                                                version=request.POST['version'])
        if compiler.count() != 0:
            return render(request, "secuTool/test.html", {"message": "A compiler with the same OS/name/version already exists",'nav2': 'active show'})

        d = {}
        for key in ['target_os', 'compiler', 'version', 'ip', 'port', 'http_path', 'invoke_format']:
            d[key] = request.POST[key]

        new_compiler = Compiler_conf(**d)
        new_compiler.save()
        return render(request, "secuTool/test.html", {'message':'New compiler successfully saved', 'nav2': 'active show'})


@csrf_exempt
def updateProfile(request):
    if request.POST['submit'] == 'save':    #update existing one
        new_profile = Profile_conf.objects.filter(target_os=request.POST['target_os'],
                                    compiler=request.POST['compiler'],
                                    version=request.POST['version'],
                                    name=request.POST['name'])

        if new_profile.count() != 0:
            return render(
                request, "secuTool/test.html", {
                    "message":
                    "A profile with the same OS/compiler/version/name already exists"
                })

        profile = Profile_conf.objects.get(target_os=request.POST['old_target_os'],
                                    compiler=request.POST['old_compiler'],
                                    version=request.POST['old_version'],
                                    name=request.POST['old_name'])

        for key in ['target_os', 'compiler', 'version', 'name']:
            setattr(profile, key, request.POST[key])

        new_flag = map(lambda x: x.strip(), request.POST['flag'].splitlines())
        new_flag = list(filter(lambda x: x, new_flag))
        setattr(profile, 'flag', json.dumps(new_flag))

        profile.save()
        return render(request, "secuTool/test.html", {'message':'Profile successfully updated', 'nav2': 'active show'})

    else:       #save as new
        profile = Profile_conf.objects.filter(target_os=request.POST['target_os'],
                                                compiler=request.POST['compiler'],
                                                version=request.POST['version'],
                                                name=request.POST['name'])
        if profile.count() != 0:
            return render(
                request, "secuTool/test.html", {
                    "message":
                    "A profile with the same OS/compiler/version/name already exists"
                })

        d = {}
        for key in ['target_os', 'compiler', 'version', 'name', 'uploader']:
            d[key] = request.POST[key]
        d['upload_time'] = datetime.now()
        new_flag = map(lambda x: x.strip(), request.POST['flag'].splitlines())
        new_flag = list(filter(lambda x: x, new_flag))
        d['flag'] = json.dumps(new_flag)

        new_profile = Profile_conf(**d)
        new_profile.save()
        return render(request, "secuTool/test.html", {'message':'New profile successfully saved', 'nav2': 'active show'})


@csrf_exempt
def deleteCompiler(request):
    compiler_to_delete = Compiler_conf.objects.get(target_os=request.POST['target_os'],
                                    compiler=request.POST['compiler'],
                                    version=request.POST['version'])
    compiler_to_delete.delete()
    return render(request, "secuTool/test.html", {'message':'Compiler successfully deleted', 'nav2': 'active show'})

@csrf_exempt
def deleteProfile(request):
    profile_to_delete = Profile_conf.objects.get(target_os=request.POST['target_os'],
                                                compiler=request.POST['compiler'],
                                                version=request.POST['version'],
                                                name=request.POST['name'])
    profile_to_delete.delete()
    return render(request, "secuTool/test.html", {'message':'Profile successfully deleted', 'nav2': 'active show'})



###########################################################################
###########################################################################
#########           BELOW ARE SOME HELPER/TEST FUNCTIONS       ############
###########################################################################
###########################################################################











