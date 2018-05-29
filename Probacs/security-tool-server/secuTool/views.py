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
	return render(request,'secuTool/index.html',context)



@transaction.atomic
def rcvSrc(request):
	timestr = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
	#create unique task forder for each task, inside which includes:
	# srcCode, <profiles>, compiled file & log, 
	# the archive for downloading will be delete 
	taskName = 'task_'+timestr
	taskFolder = taskdir+'task_'+timestr
	codeFolder = taskFolder+"/"+"srcCodes"
	os.system("mkdir "+taskFolder)
	context = {}
	srcPath = ''
	# handle bad submit request (attention, undergoing compilation info may be missing by rendering blank)
	if 'srcCodes' not in request.FILES or 'task_file' not in request.FILES:
		return redirect(home)
	#save file in taskfolder
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
		os.system('tar xvzf '+ taskFolder+'/'+filename+" -C "+taskFolder)
		os.system('mv '+taskFolder+'/'+filename.split('.')[0]+' '+codeFolder)
		srcPath = codeFolder+"/"+filename

	# write task specify file to taskFolder
	taskPath = taskFolder+"/"+taskfile
	with open(taskPath,'wb+') as dest:
		for chunk in request.FILES['task_file'].chunks():
			dest.write(chunk)


	#######################
	# parse task file
	#######################
	message, param = parseTaskFile(taskPath)
	print(param)
	if message != None:
		context['form']  = ProfileUserForm()
		context['message'] = message
		return render(request, 'secuTool/index.html',context)

	#form request format from parse.py
	task_compiler = Compiler_conf.objects.get(target_os=param['target_os'], compiler=param['compiler'],
		version=param['version'])
	task_http = task_compiler.ip + ":"+task_compiler.port+task_compiler.http_path
	# permute flags combination  from diff flags
	jsonDec = json.decoder.JSONDecoder()
	flag_from_profile = []
	for profile_name in param['profile']:
		print(profile_name)
		p_tmp = Profile_conf.objects.get(name=profile_name, target_os=param['target_os'],compiler=param['compiler'],
			version=param['version'])
		flag_from_profile.append(jsonDec.decode(p_tmp.flag))
	compile_combination = [[]]
	for x in flag_from_profile:
		compile_combination = [i + [y] for y in x for i in compile_combination]
	compile_combination = [" ".join(x) for x in compile_combination]
	compile_combination = [x.replace(" ","_") for x in compile_combination]
	final_flags = ",".join(compile_combination) 
	print(final_flags)
	#############################
	# calling compilation tasks
	#############################
	if task_http == self_ip:
		## compile in this host linux
		# specify working dir id
		outputDir = taskFolder+"/"+"secu_compile"
		print(final_flags)
		os.system("python make_compilation.py "+srcPath+" "+ outputDir+" "+task_compiler.invoke_format+" "+final_flags)
		print("finished compile")
		context['linux_taskFolder'] = taskName
		context['form']  = ProfileUserForm()
		context['message'] = 'file compile finished !'
		print(filename)
		settings.TASKS[taskName] = 1
		return render(request, 'secuTool/index.html', context)
	# if not compiling on linux host, send params to another function, interacting with specific platform server
	upload_to_platform(task_http, task_compiler.invoke_format, final_flags, taskName, codeFolder,filename)
	context['message'] = "file is compiling..."
	context['form'] = ProfileUserForm()
	context['linux_taskFolder'] = taskFolder
	return render(request, 'secuTool/index.html', context)
	#add task into database, database approach
	# taskRecord = Tasks(taskFolder=taskName, totalCompilation = 1, finishedCompilation = 1, status = 1)
	# taskRecord.save()

@transaction.atomic
def upload_to_platform(ip, compiler_invoke, flags, taskFolder, codeFolder,mainSrcName):
	'''
	flags is compressed string used for make_compilation.py
	compiler_invoke is a string used for cmd line compilation
	codeFolder is the code directory path, need compress then send along
	'''
	#################################
	# form code archive for code folder
	#################################
	tarPath = taskFolder+'/src.tar'
	print(tarPath)
	os.system('tar cvzf '+tarPath+' '+codeFolder)
	#send request to specific platform servers
	data = { 'Srcname':mainSrcName,'taskid':taskFolder,'command': compiler_invoke,'flags': flags}
	files={'file':(tarPath, open(tarPath, 'rb'))}    #need file archive path
	settings.TASKS[taskFolder] = 0
	response = requests.post(winurl, files=files,data={'taskid':taskFolder}) 
	return



# # upload files to a folder to store, then send it to windows server
# @transaction.atomic
# @csrf_exempt
# def upWin(request):
# 	timestr = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
# 	context = {}
# 	context['message'] = 'win VM received the command !'
# 	#create task folder
# 	taskFolder = 'win_'+timestr
# 	os.system("mkdir "+taskdir+taskFolder)
# 	if 'srcCodes' not in request.FILES:
# 		return redirect(home)
# 	#save file in taskfolder		
# 	filename = request.FILES['srcCodes'].name
# 	print(filename)
# 	srcPath = taskdir+taskFolder+"/"+filename
# 	with open(srcPath,'wb+') as dest:
# 		for chunk in request.FILES['srcCodes'].chunks():
# 			dest.write(chunk)
# 	#form httprequest 
# 	filename = request.FILES['srcCodes'].name
# 	files={'file':(srcPath, open(srcPath, 'rb'))}

# 	#add record to database, database approach
# 	# taskRecord = Tasks(taskFolder=taskFolder, totalCompilation = 1, 
# 		# finishedCompilation = 0, status = 0)
# 	# taskRecord.save()

# 	settings.TASKS[taskFolder] = 0
# 	# printRcd(taskRecord)
# 	print('in upwin, print total: time: '+ str(datetime.now().strftime("%Y-%m-%d-%H-%M-%S")))
# 	print(settings.TASKS)

# 	#send request to win
# 	response = requests.post(winurl, files=files,data={'taskid':taskFolder}) 

# 	context['filename'] = "file is compiling..."
# 	context['form'] = ProfileUserForm()
# 	context['win_taskFolder'] = taskFolder
# 	return render(request, 'secuTool/index.html', context)

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

	#change task status, database methods
	# records = Tasks.objects.get(taskFolder=taskFolder)
	# printRcd(records)
	# records.finishedCompilation += 1
	# if records.finishedCompilation == records.totalCompilation:
	# 	records.status == 1
	# records.save()

	print(settings.TASKS)
	settings.TASKS[taskFolder] = 1
	print(settings.TASKS)
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
		print(str(taskFolder) not in taskTrace)
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

#used for database computing
def printRcd(rcd):
	print("============rcd report")
	if rcd == None:
		print('rcd not exists')
		return
	print("folder: "+ str(rcd.taskFolder))
	print("finished: "+ str(rcd.finishedCompilation))
	print("total: "+ str(rcd.totalCompilation))
	print("status: "+ str(rcd.status))
	return



