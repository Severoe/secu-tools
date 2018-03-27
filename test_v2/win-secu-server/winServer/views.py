import os, tempfile, zipfile,tarfile, time
from datetime import datetime
from wsgiref.util import FileWrapper
from django.shortcuts import render
from winServer.forms import *
from winServer.models import *
from django.core.files import File 
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests    #need pip install requests

hostserver = "http://172.16.165.125:8000/" #ip/port of the host server

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
	with open(taskFolder+'\\'+filename,'wb+') as dest:
		for chunk in request.FILES['file'].chunks():
			dest.write(chunk)
	print(request.FILES['file'])
	############################################
	# compilation work
	os.system("mkdir "+taskFolder+'\\'+'secu_compile_win') #this is the working dir for storing exe 
	compileDir = taskFolder+'\\'+'secu_compile_win\\'
	# compilation start here, store executables and logs
	# into compileDir
	#
	#
	############################################
	# send back exe archive to host by http request
	responseFromHost,tmpzip = sendBackExe(taskFolder) # test purpose, replace hellomake later
	os.system("del /-f "+tmpzip) #delete tmp zip file
	# clean out directory
	#os.system("del /-f "+taskFolder)
	response = HttpResponse()
	#response.write("<p>Here's the text of the Web page.</p>")
	return response

# create zip file containing exe and log, then send to host
# delete zip file after sending to host
def sendBackExe(folder):
	#create a zip file first
	timestr = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
	new_name = "winexe_"+timestr+".tgz"
	exe_folderPath = folder+'\\'+'secu_compile_win'
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
