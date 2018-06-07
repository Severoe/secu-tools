
import os, tempfile, zipfile,tarfile, time,sys
from datetime import datetime
from wsgiref.util import FileWrapper
from django.shortcuts import render
from winServer.forms import *
from winServer.models import *
from django.core.files import File 
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests    #need pip install requests
from subprocess import Popen, PIPE
# from multiprocessing import Process

# hostserver = "http://192.168.27.131:8000/" #ip/port of the host server
# hostserver = "http://172.16.165.125:8000/" #ip/port of the host server
hostserver = "http://192.168.56.101:8000/" #ip/port of the host server on virtualbox


@csrf_exempt
def execute(request):
	#create working dir for this compilation task
	taskFolder = request.POST['taskid']
	print("id: "+taskFolder)
	#timestr = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
	os.system("mkdir "+taskFolder)
	print('order received')
	#save file in task folder
	filename = request.FILES['file'].name
	host_ip = request.META['REMOTE_ADDR']
	host_port = request.META['SERVER_PORT']
	hostserver = "http://"+host_ip+":"+host_port+"/"
	print(hostserver)
	src_dir = 'srcCodes'

	with open(taskFolder+'\\'+filename,'wb+') as dest:
		for chunk in request.FILES['file'].chunks():
			dest.write(chunk)
	tar = r'"C:\Program Files (x86)\GnuWin32\bin\tar.exe"'
	os.system(tar+" "+"xvf "+ taskFolder+'\\'+filename)
	print(request.FILES['file'])

	############################################
	# compilation work
	srcpath = src_dir+'\\'+request.POST['Srcname']
	print(srcpath)
	compileDir = taskFolder+'\\'+'secu_compile_win'
	os.system("mkdir "+compileDir)
	# compilation start here, store executables and logs
	# into compileDir
	cl = None
	if 'env' in request.POST and request.POST['env'] != None:
		cl = request.POST['env'].replace("_",' ')
	compile(taskFolder, request.POST['target_os'], request.POST['compiler'], request.POST['version'],
		srcpath, compileDir, request.POST['command'], request.POST['flags'],cl)
	# make compilation async
	# p = Process(target=sub_process,args=(request.POST,taskFolder,srcpath,compileDir,cl,src_dir))
	# p.start()
	# print("python make_compilation.py "+srcpath+ " "+compileDir+" "+request.POST['command']+" "+request.POST['flags'])
	# cl = r'"C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\VC\Auxiliary\Build\vcvars64.bat"'
	# os.system(cl+"&& python make_compilation.py "+srcpath+ " "+compileDir+" "+request.POST['command']+" "+request.POST['flags'])
	############################################
	# send back exe archive to host by http request
	response = HttpResponse()
	print("send back request")
	return response

# def sub_process(info, taskFolder, srcpath, compileDir,cl,src_dir):
# 	compile(taskFolder, info['target_os'], info['compiler'], info['version'],
# 		srcpath, compileDir, info['command'], info['flags'],cl)
# 	print("finished compile")
# 	responseFromHost,tmpzip = sendBackExe(taskFolder) # test purpose, replace hellomake later
# 	os.system("del /-f "+src_dir +" /Q") #delete tmp zip file
# 	return


def compile(task_id, target_os, compiler, version, src_path, dest_folder, invoke_format, flags, cl):
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
    Popen(cl)
    for flag in flag_list:
        cnt += 1
        time.sleep(3)
        exename = dest_folder + name + "_%d_%s"%(cnt, flag.replace(" ", "_"))
        logline = "%s\t%s"%(exename, flag)

        command = invoke_format.replace("flags", flag).replace("source", src_path).replace("exename", exename).split(" ")
        print(command)
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
	print(task_info)
	data = task_info
	response = requests.post(hostserver+"rcv_compilation", data=data) 
	return



# create zip file containing exe and log, then send to host
# delete zip file after sending to host
def sendBackExe(folder):
	#create a zip file first
	print("send back exe")
	timestr = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
	new_name = "winexe_"+timestr+".tgz"
	exe_folderPath = folder+'\\'+'secu_compile_platform'
	with tarfile.open(new_name, "w:gz") as tar:
		tar.add(exe_folderPath, arcname=os.path.basename(exe_folderPath))
	compressed_dir = open(new_name,'rb')
	#form http request
	files = {'file':(new_name,compressed_dir)}
	url = hostserver+'saveExe';
	response = requests.post(url, files = files,data={'taskid': folder})
	print("response received from host")
	return response,new_name

# test only, not fully deployed
def retJson(request):
	print('retJson called')
	response = {}
	response['message'] = "receive request successfully !"
	return HttpResponse(json.dumps(response),  content_type="application/json")
