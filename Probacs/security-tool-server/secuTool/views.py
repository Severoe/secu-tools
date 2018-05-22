import os, tempfile, zipfile,tarfile, time
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

# Create your views here.
################################
# global variables
# winurl = 'http://172.16.165.132:8000'
winurl = 'http://192.168.56.101:8000' #winurl for virtualbox
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
	taskName = 'linux_'+timestr
	taskFolder = taskdir+'linux_'+timestr
	os.system("mkdir "+taskFolder)
	context = {}
	# handle bad submit request (attention, undergoing compilation info may be missing by rendering blank)
	if 'srcCodes' not in request.FILES:
		return redirect(home)
	#save file in taskfolder
	filename = request.FILES['srcCodes'].name
	# print(filename)
	srcPath = taskFolder+"/"+filename
	with open(srcPath,'wb+') as dest:
		for chunk in request.FILES['srcCodes'].chunks():
			dest.write(chunk)

	context['form']  = ProfileUserForm()
	context['message'] = 'file compile finished !'
	print(filename)
	# specify working dir id
	outputDir = taskFolder+"/"+"secu_compile"
	os.system("python make_compilation.py "+srcPath+" "+ outputDir)
	print("finished compile")
	context['linux_taskFolder'] = taskName

	#add task into database, database approach
	# taskRecord = Tasks(taskFolder=taskName, totalCompilation = 1, finishedCompilation = 1, status = 1)
	# taskRecord.save()

	settings.TASKS[taskName] = 1
	return render(request, 'secuTool/index.html', context)

# upload files to a folder to store, then send it to windows server
@transaction.atomic
@csrf_exempt
def upWin(request):
	timestr = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
	context = {}
	context['message'] = 'win VM received the command !'
	#create task folder
	taskFolder = 'win_'+timestr
	os.system("mkdir "+taskdir+taskFolder)
	if 'srcCodes' not in request.FILES:
		return redirect(home)
	#save file in taskfolder		
	filename = request.FILES['srcCodes'].name
	print(filename)
	srcPath = taskdir+taskFolder+"/"+filename
	with open(srcPath,'wb+') as dest:
		for chunk in request.FILES['srcCodes'].chunks():
			dest.write(chunk)
	#form httprequest 
	filename = request.FILES['srcCodes'].name
	files={'file':(srcPath, open(srcPath, 'rb'))}

	#add record to database, database approach
	# taskRecord = Tasks(taskFolder=taskFolder, totalCompilation = 1, 
		# finishedCompilation = 0, status = 0)
	# taskRecord.save()

	settings.TASKS[taskFolder] = 0
	# printRcd(taskRecord)
	print('in upwin, print total: time: '+ str(datetime.now().strftime("%Y-%m-%d-%H-%M-%S")))
	print(settings.TASKS)

	#send request to win
	response = requests.post(winurl, files=files,data={'taskid':taskFolder}) 

	context['filename'] = "file is compiling..."
	context['form'] = ProfileUserForm()
	context['win_taskFolder'] = taskFolder
	return render(request, 'secuTool/index.html', context)

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



