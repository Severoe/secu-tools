import os, tempfile, zipfile,tarfile, time,json
from subprocess import Popen, PIPE
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
from parser import *

# Create your views here.
################################
# global variables
# winurl = 'http://172.16.165.132:8000'
self_ip = 'http://192.168.56.101:8000'
winurl = 'http://192.168.56.102:8000' #winurl for virtualbox
testurl = 'http://httpbin.org/post'  #test request headers
taskdir = 'Compilation_tasks/'
# the datastructure  is stored in settings
################################

def home(request):
    context = {}
    context['form'] = ProfileUserForm()
    context['progress'] = 'none'
    return render(request,'secuTool/index.html',context)



@transaction.atomic
def rcvSrc(request):
    timestr = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    #create unique task forder for each task, inside which includes:
    # srcCode, <profiles>, compiled file & log, 
    # the archive for downloading will be delete 
    taskName = timestr
    taskFolder = taskdir+timestr
    codeFolder = taskFolder+"/"+"srcCodes"
    os.system("mkdir "+taskFolder)
    context = {}
    srcPath = ''
    #######################
    # handle bad submit request (attention, undergoing compilation info may be missing by rendering blank)
    #######################
    if 'srcCodes' not in request.FILES or 'task_file' not in request.FILES:
        return redirect(home)
    #######################
    #save source files in taskfolder
    #######################
    filename = request.FILES['srcCodes'].name
    taskfile = request.FILES['task_file'].name
    print(request.FILES['srcCodes'].content_type)
    if request.FILES['srcCodes'].content_type not in ['application/x-tar','application/gzip','application/zip']:
        #indicating a single file
        os.system("mkdir "+codeFolder)
        srcPath = codeFolder+"/"+filename
        with open(srcPath,'wb+') as dest:
            for chunk in request.FILES['srcCodes'].chunks():
                dest.write(chunk)
    else:
        #if user upload tar bar, extract and save into srcCode folder
        #also upload filename to be main filename
        with open(taskFolder+'/'+filename,'wb+') as dest:
            for chunk in request.FILES['srcCodes'].chunks():
                dest.write(chunk)
        os.system('tar xvzf '+ taskFolder+'/'+filename+" -C "+srcCodes)
        os.system('mv '+taskFolder+'/'+filename.split('.')[0]+' '+codeFolder)
        srcPath = codeFolder+"/"+filename
        # update filename to be the main srcfile name if tast srcfile is a tarbar
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
    message, p = parseTaskFile(taskPath)
    print(p)
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
                tag=None if 'tag' in param else param['tag'],
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
                response = requests.post(self_ip+"/self_compile", data=data) 
                #new thread
                time.sleep(5)
                # os.system("python make_compilation.py "+srcPath+" "+ outputDir+" "+task_compiler.invoke_format+" "+final_flags)
                print("finished compile")
                os._exit(0)  
            else:
                #parent process, simply return to client
                print("asyn call encountered")
                # settings.TASKS[taskName] = 1
        # if not compiling on linux host, send params to another function, interacting with specific platform server
        else:
            upload_to_platform(param,task_http, task_compiler.invoke_format, final_flags, taskName, taskFolder, codeFolder,filename)
        
    context['task_id'] = taskName
    context['message'] = "file is compiling..."
    context['form'] = ProfileUserForm()
    context['progress'] = 'block'
    context['linux_taskFolder'] = taskName
    return render(request, 'secuTool/index.html', context)
    #add task into database, database approach
    # taskRecord = Tasks(taskFolder=taskName, totalCompilation = 1, finishedCompilation = 1, status = 1)
    # taskRecord.save()

@transaction.atomic
@csrf_exempt
def self_compile(request):
    # compile(taskName, param['target_os'], param['compiler'], param['version'], srcPath, outputDir, task_compiler.invoke_format, final_flags,on_complete)
    compile(request.POST['task_id'],request.POST['target_os'],request.POST['compiler'],request.POST['version'],
        request.POST['srcPath'],request.POST['output'],request.POST['format'],request.POST['flags'],on_complete)
    return HttpResponse()



def upload_to_platform(param,ip, compiler_invoke, flags, taskName, taskFolder, codeFolder,mainSrcName):
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
    os.system('cd '+taskFolder+' && tar cvf src.tar srcCodes/')
    #send request to specific platform servers
    runEnv = None
    if '&&' in compiler_invoke:
        runEnv = compiler_invoke.split('&&')[0]
        compiler_invoke = compiler_invoke.split('&&')[1]
    data = { 'Srcname':mainSrcName,'taskid':taskName,'command': compiler_invoke,'flags': flags,
    'env':runEnv,'target_os':param['target_os'],'compiler':param['compiler'],'version':param['version']}
    print(data)
    files={'file':(tarPath, open(tarPath, 'rb'))}    #need file archive path
    settings.TASKS[taskFolder] = 0
    pid = os.fork()
    if pid == 0:
        response = requests.post(winurl, files=files,data=data) 
        os._exit(0)  
    else:
        return



#receive compiled task from win, need to save file at taskFolder
@transaction.atomic
@csrf_exempt
def saveExe(request):
    taskFolder = request.POST['taskid']
    print('id in saveexe:'+taskFolder)
    filename = request.FILES['file'].name
    basedir = taskdir+taskFolder+'/'
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


#need to pack task based on taskid, also return blank page if request is empty
@transaction.atomic
def wrap_dir(request):
    taskFolder = request.POST['taskid']
    print("taskFolder: "+taskFolder )
    print(settings.TASKS)
    # records = Tasks.objects.get(taskFolder=taskFolder)
    if os.path.exists(taskdir+taskFolder) == False:# or records == None:
        print(os.path.exists(taskdir+taskFolder))
        # print(str(taskFolder) not in taskTrace)
        return redirect(home)
    elif settings.TASKS[taskFolder] == 0:
        context = {}
        context['form'] = ProfileUserForm()
        context['message'] = "win compilation did not finish! try later"
        context['win_taskFolder'] = taskFolder
        return render(request,'secuTool/index.html',context)
    elif settings.TASKS[taskFolder] == 1:
        print('task exists')
    #pack executables inside task folder, send back
    new_name = "archive_"+taskFolder+".tgz"
    current_taskdir = taskdir+taskFolder+'/'
    with tarfile.open(current_taskdir+new_name, "w:gz") as tar:
        tar.add(current_taskdir+'secu_compile', arcname=os.path.basename(current_taskdir+'secu_compile'))

    compressed_dir = open(current_taskdir+new_name,'rb')
    response = HttpResponse(compressed_dir,content_type='application/tgz')
    response['Content-Disposition'] = 'attachment; filename='+new_name
    # os.system("rm "+taskFolder+'/'+new_name)
    return response

@transaction.atomic
def check_status(request):
    context = {}
    task_id = request.POST['task_id']
    flags = request.POST['flags']
    obj = Task.objects.all()
    query_dict = {}
    query_dict['task_id'] = None if request.POST['task_id']==None else request.POST['task_id'].split(",")
    query_dict['flag'] = None if request.POST['flags']==None else request.POST['flags'].split(",")
    query_dict['username'] = None if request.POST['username']==None else request.POST['username'].split(",")
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

    context['form'] = ProfileUserForm()


    context['tasks'] = obj
    for ele in context['tasks']:
        ele.flag = ele.flag.replace("_", " ")
        ele.status = 'not finished' if ele.exename == None else 'finished'
        ele.exename = '-' if not ele.exename else ele.exename
        ele.out = '-' if not ele.out else ele.out
        ele.err = '-' if not ele.err else ele.err

    # context['task_id'] = request.POST['task_id']
    return render(request, 'secuTool/index.html',context)



#used for database computing
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
    print('update from platform finished')
    task.save()
    # task = Task.objects.get(task_id=task_info['task_id'],flag=task_info['flag'].replace(" ","_"))
    # print("exename "+str(task.exename))
    return HttpResponse()


@transaction.atomic
def on_complete(task_info):
    '''
    called when each time compilation finished
    '''
    response = requests.post(url=self_ip+"/rcv_compilation",data = task_info)  
    return

@transaction.atomic
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

    dest_folder += delimit
    log_filename = dest_folder + name + ".log"
    log_file = open(log_filename, "w")

    print("compilation begins...")
        
    cnt = 0
    for flag in flag_list:
        cnt += 1
        time.sleep(5)
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
        # task = Task.objects.get(task_id=task_info['task_id'],flag=task_info['flag'].replace(" ","_"))
        # printRcd(task)


    log_file.close()
    print("compilation done!")
    return



#trace job status
def trace(request):
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

# test funciton
def test(request):
    context = {}
    context['message'] = 'shkadhlaskdjask'
    context['form'] = ProfileUserForm()
    # context['status'] = statuses
    return render(request, 'secuTool/test.html',context)

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


