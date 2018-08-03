#from webapps import settings
#from django.core.management import setup_environ
#setup_environ(settings)
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'webapps.settings'
import django
django.setup()
import json, time
from datetime import datetime
from secuTool.models import *


compiler_all = Compiler_conf.objects.all()
compiler_all.delete()
profile_all = Profile_conf.objects.all()
profile_all.delete()


compiler_data = [
    {
        'target_os': 'Windows',
        'compiler': 'MSVC++',
        'version': '14.11',
        'ip': 'http://192.168.56.102',
        'port': '8000',
        'invoke_format': r'"C:\Program_Files_(x86)\Microsoft_Visual_Studio\2017\Community\VC\Auxiliary\Build\vcvars64.bat"&&cl_flags_source_/Feexename',
        'flag': ['/O1', '/O2', '/Ob1', '/Oi', '/Os', '/Ot', '/Ox', '/Oy', '/W1', '/W2', '/W3', '/W4', '/Wall', '/WX']
    },
    {
        'target_os': 'Linux',
        'compiler': 'gcc',
        'version': '6.7',
        'ip': 'http://192.168.56.101',
        'port': '8000',
        'invoke_format': 'gcc_flags_source_-o_exename',
        'flag': ['-O1', '-O2', '-O3', '-O0', '-Os', '-Ofast', '-Og', '-fgcse-las',
        '-fdelete-null-pointer-checks', '-fgcse-sm', '-fgcse-lm', '-finline-small-functions',
        '-fno-inline', '-fsyntax-only', '-w', '-Werror', '-Wpedantic', '-Wall', '-Wextra',
        '-Wno-coverage-mismatch', '-Wno-cpp', '-Wformat', '-Wfatal-errors', '-Wmain', '-Wunused',
        '-Wno-pedantic-ms-format', '-Wuninitialized', '-Wsystem-headers', '-Wunknown-pragmas']
    },
]
profile_data = [
    {
        'uploader': 'jeffery',
        'upload_time': '2006-10-25 14:30:59',
        'name': 'warnings',
        'target_os': 'Linux',
        'compiler': 'gcc',
        'version': '6.7',
        'flag': ['-fsyntax-only', '-w', '-Werror', '-Wpedantic', '-Wall', '-Wextra', '-Wno-coverage-mismatch', '-Wno-cpp', '-Wformat', '-Wfatal-errors', '-Wmain', '-Wunused', '-Wmain -Wfatal-errors', '-Wno-pedantic-ms-format -Wformat -Wpedantic', '-Wextra -Wunused', '-Wuninitialized -Wunused', '-Wformat -Wpedantic', '-Wsystem-headers -Wunknown-pragmas']
    },
    {
        'uploader': 'jeffery',
        'upload_time': '2006-10-25 14:30:59',
        'name': 'max_optimization',
        'target_os': 'Linux',
        'compiler': 'gcc',
        'version': '6.7',
        'flag': ['-O1', '-O2', '-O3', '-O0', '-Os', '-Ofast', '-Og', '-fgcse-las -O1', '-fgcse-las -Ofast', '-fgcse-las -Og', '-fdelete-null-pointer-checks -O3', '-fgcse-sm -Og', '-fgcse-sm -fgcse-lm', '-fgcse-lm -Og', '-finline-small-functions -Ofast', '-fno-inline -O2']
    },
    {
        'uploader': 'Dave',
        'upload_time': '2006-10-25 14:30:59',
        'name': 'warnings',
        'target_os': 'Windows',
        'compiler': 'MSVC++',
        'version': '14.11',
        'flag': [ '/W1', '/W2', '/W3', '/W4', '/Wall', '/WX', '/W1 /WX', '/W2 /WX', '/W3 /WX', '/W4 /WX']
    },
    {
        'uploader': 'Dave',
        'upload_time': '2006-10-25 14:30:59',
        'name': 'max_optimization',
        'target_os': 'Windows',
        'compiler': 'MSVC++',
        'version': '14.11',
        'flag': ['/O1', '/O2', '/Ob1', '/Oi', '/Os', '/Ot', '/Ox', '/Oy', '/Oi /O1', '/Oi /O2', '/Oi /Ob1', '/Ox /Oy', '/Oi /Ox /Oy']
    },
]


for cdata in compiler_data:
    flags = json.dumps(cdata['flag'])
    compiler_ = Compiler_conf(
        target_os=cdata['target_os'],
        compiler=cdata['compiler'],
        version=cdata['version'],
        ip=cdata['ip'],
        port=cdata['port'],
        invoke_format=cdata['invoke_format'],
        flag=flags)
    compiler_.save()

for pdata in profile_data:
    flags = json.dumps(pdata['flag'])
    profile_ = Profile_conf(
        uploader=pdata['uploader'],
        upload_time=pdata['upload_time'],
        name=pdata['name'],
        target_os=pdata['target_os'],
        compiler=pdata['compiler'],
        version=pdata['version'],
        flag=flags)
    profile_.save()