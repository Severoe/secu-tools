#from webapps import settings
#from django.core.management import setup_environ
#setup_environ(settings)
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'webapps.settings'
import django
django.setup()
import json,time
from datetime import datetime
from secuTool.models import *


compiler_all = Compiler_conf.objects.all()
compiler_all.delete()
profile_all = Profile_conf.objects.all()
profile_all.delete()


compiler_data = [
	{'target_os':'linux','compiler':'gcc','version':'6.7','ip':'http://192.168.56.101','port':'8000','http_path':'','invoke_format':'gcc_$flags$_$source$_-o_$exename$'},
	{'target_os':'linux','compiler':'sd','version':'6.7','ip':'http://192.67.56.101','port':'8000','http_path':'','invoke_format':'gcc_$flags$_$source$_-o_$exename$'},
]
profile_data = [
	{'uploader':'jeffery','upload_time':'2006-10-25 14:30:59','name':'max_speed','target_os':'linux','compiler':'gcc','version':'6.7','flag':['-O1 -O0','-O0 -02']},
	{'uploader':'jeffery','upload_time':'2006-10-25 14:30:59','name':'max_optimization','target_os':'linux','compiler':'gcc','version':'6.7','flag':['-Wall','-O3']}
]



for cdata in compiler_data:
	compiler_ = Compiler_conf(target_os=cdata['target_os'], compiler=cdata['compiler'], version=cdata['version'],
		ip = cdata['ip'], port=cdata['port'],http_path=cdata['http_path'],invoke_format=cdata['invoke_format'])
	compiler_.save()

for pdata in profile_data:
	flags = json.dumps(pdata['flag'])
	profile_ = Profile_conf(uploader=pdata['uploader'], upload_time=pdata['upload_time'], name=pdata['name'],
		target_os=pdata['target_os'],compiler=pdata['compiler'],version=pdata['version'],flag=flags)
	profile_.save()


#check database
jeff = Compiler_conf.objects.get(target_os='linux',compiler='sd')
print(jeff.ip)




