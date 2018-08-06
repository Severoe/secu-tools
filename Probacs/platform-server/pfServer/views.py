import os, tempfile, zipfile,tarfile, time,sys, signal
import json
from datetime import datetime
from wsgiref.util import FileWrapper
from django.shortcuts import render
# from pfServer.forms import *
from pfServer.models import *
from django.core.files import File
from django.http import HttpResponse
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
import requests    #need pip install requests
from subprocess import Popen, PIPE

rootDir = 'Compilation_tasks'
hostserver = "" #ip/port of the host server on virtualbox
os_name = os.name
if os_name == 'nt':
	delimit = "\\"
else:
	delimit = "/"



##########################################
########	dev log.   ##################
'''

''' 
##########################################


@csrf_exempt
def execute(request):
	#create working dir for this compilation task
	taskFolder = request.POST['taskid']
	print("id: "+taskFolder)
	#timestr = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
	os.mkdir(rootDir+delimit+taskFolder)
	print('order received')
	#save file in task folder
	src = request.FILES['file'].name
	filename = request.POST['Srcname'].split(".")[0]


	hostserver = request.POST['host_ip']+"/"
	task_dir = rootDir+delimit+taskFolder+delimit
	# os.mkdir(task_dir+"src")

	with open(task_dir+src,'wb+') as dest:
		for chunk in request.FILES['file'].chunks():
			dest.write(chunk)

	if os_name == 'nt':
		tar = r'"C:\Program Files (x86)\GnuWin32\bin\tar.exe"'
		# p = Popen([tar, 'xfv', src], cwd = task_dir)
		# print(p.communicate())
		cmd = "cd "+task_dir+" && "+tar+" xvf "+src
		print(cmd)
		os.system(cmd)
	else:
		tar = "tar"
		os.system(tar+" xvf "+ task_dir+src+" -C "+task_dir)

	print(request.FILES['file'])
	####################################
	##### change suffix to enable multi-platform executables
	suffix = request.POST['target_os'] + "_" + request.POST['compiler'] + "_" + request.POST['version']
	invalidChars = '\/:*?"<>|'
	for ch in invalidChars:
		suffix = suffix.replace(ch, '')

	dest_name = 'secu_compile_platform_' + suffix
	############################################
	# compilation working directory
	compileDir = task_dir+dest_name
	os.mkdir(compileDir)
	# compilation start here, store executables and logs
	# into compileDir
	cl = None
	if 'env' in request.POST and request.POST['env'] != None:
		cl = request.POST['env'].replace("_",' ')
	# compile(taskFolder, request.POST['target_os'], request.POST['compiler'], request.POST['version'],
	# 	srcpath, compileDir, request.POST['command'], request.POST['flags'],cl)
	# make compilation async
	# p = Process(target=sub_process,args=(request.POST,taskFolder,srcpath,compileDir,cl,src_dir))
	# p.start()
	# print("python make_compilation.py "+srcpath+ " "+compileDir+" "+request.POST['command']+" "+request.POST['flags'])
	# cl = r'"C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\VC\Auxiliary\Build\vcvars64.bat"'
	if cl == None:
		# proc = Popen(["python","make_compilation.py",taskFolder,request.POST['target_os'],
		# 	request.POST['compiler'],request.POST['version'],srcpath,compileDir,request.POST['command'],
		# 	request.POST['flags'],hostserver], shell=True)
		# print(proc.pid)
		os.system("python make_compilation.py "+taskFolder+" "+
		 request.POST['target_os']+" "+request.POST['compiler']+" "+request.POST['version']+" "+filename+" "+
		 compileDir+" "+request.POST['command']+" "+request.POST['flags']+" "+request.POST['exenames']+" "+
		 dest_name+" "+hostserver)
	else:
		os.system(cl+"&& python make_compilation.py "+taskFolder+" "+
		 request.POST['target_os']+" "+request.POST['compiler']+" "+request.POST['version']+" "+filename+" "+
		 compileDir+" "+request.POST['command']+" "+request.POST['flags']+" "+request.POST['exenames']+" "+
		 dest_name+" "+hostserver)
	####################################
	##### change suffix to enable multi-platform executables
	suffix = request.POST['target_os'] + "_" + request.POST['compiler'] + "_" + request.POST['version']
	invalidChars = '\/:*?"<>|'
	for ch in invalidChars:
		suffix = suffix.replace(ch, '')

	############################################
	# send back exe archive to host by http request
	responseFromHost,tmpzip = sendBackExe(taskFolder, hostserver,dest_name) # test purpose, replace hellomake later
	##clear environment
	if os_name == 'nt':
		# os.system("del /f "+src_dir +" /Q")
		os.system("del /f *.tgz")
		os.system("del /f "+task_dir)
	else:
		# os.system("rm -rf "+src_dir)
		os.system("rm -rf *.obj")
		os.system("rm -rf *.tgz")
		os.system("rm -rf "+task_dir)
	response = HttpResponse()
	print("send back request")
	return response


@transaction.atomic
@csrf_exempt
def terminate_sub(request):
	task_id = request.POST['task_id']
	ongoing_process = CompilationPid.objects.get(taskid=task_id)
	# response = {}
	if ongoing_process == None:
		response = "false"
	else:
		pid = ongoing_process.pid
		os.kill(pid, signal.SIGTERM)
		print(pid)
		ongoing_process.delete()
		response = "true"
	return HttpResponse(response)


# create zip file containing exe and log, then send to host
# delete zip file after sending to host
def sendBackExe(folder,hostserver,dest_name):
	#create a zip file first
	print("send back exe")
	timestr = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
	new_name = "exe_"+timestr+".tgz"
	exe_folderPath = rootDir+delimit+folder+delimit+dest_name
	with tarfile.open(new_name, "w:gz") as tar:
		tar.add(exe_folderPath, arcname=os.path.basename(exe_folderPath))
	compressed_dir = open(new_name,'rb')
	#form http request
	files = {'file':(new_name,compressed_dir)}
	print(hostserver)
	url = hostserver+'saveExe';
	response = requests.post(url, files = files,data={'taskid': folder})
	print("response received from host")
	return response,new_name


def check_alive(request):
	return HttpResponse()


# test only, not fully deployed
def retJson(request):
	print('retJson called')
	response = {}
	response['message'] = "receive request successfully !"
	return HttpResponse(json.dumps(response),  content_type="application/json")
