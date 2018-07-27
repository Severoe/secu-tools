# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User


MAX_UPLOAD_SIZE = 2500000



class Compiler_conf(models.Model):
    target_os = models.CharField(max_length=60)
    compiler = models.CharField(max_length=60)
    version = models.CharField(max_length=60)
    ip = models.CharField(max_length=60)
    port = models.CharField(max_length=20)
    http_path = models.CharField(max_length=60)
    invoke_format = models.TextField()
    flag = models.TextField()

class Profile_conf(models.Model):
    uploader = models.CharField(max_length=200)
    upload_time = models.TextField(max_length=30)
    name = models.CharField(max_length=200)
    target_os = models.CharField(max_length=60)
    compiler = models.CharField(max_length=60)
    version = models.CharField(max_length=60)
    flag = models.TextField()

class Task(models.Model):
	task_id = models.CharField(max_length=200)
	username = models.CharField(max_length=200)
	tag = models.TextField(null=True,blank=True)
	src_file = models.CharField(max_length=200) # file name<hello.c>
	target_os = models.CharField(max_length=60)
	compiler = models.CharField(max_length=60)
	version = models.CharField(max_length=60)
	flag = models.TextField() #flag used for one specific compilation task
	exename = models.TextField(null=True,blank=True)
	out = models.TextField(null=True,blank=True)
	err = models.TextField(null=True,blank=True)
	init_tmstmp = models.TextField()
	finish_tmstmp = models.TextField(null=True,blank=True)
	status = models.TextField(null=True,blank=True)


class TaskMeta(models.Model):
    task_id = models.CharField(max_length=200)
    username = models.CharField(max_length=200)
    tag = models.TextField(null=True,blank=True)
    src_filename = models.CharField(max_length=200)
    profiles = models.TextField()
    target_os = models.TextField()
    compiler_full = models.TextField()
    compilation_num = models.IntegerField(null=True,blank=True)
    created_date = models.DateTimeField()




class ProfileUser(models.Model):
    # user = models.ForeignKey(User)
    # bio = models.CharField(max_length=500)
    srcCodes = models.FileField(upload_to="hellomake", blank=True)
    content_type = models.CharField(max_length=50)  #file type
    task_file = models.FileField(blank=True)
    def __unicode__(self):
        return 'id=' + str(self.id) + ',bio="' + self.content_type + '"'



class CompilationPid(models.Model):
    pid = models.IntegerField()
    taskid = models.CharField(max_length=200)





class Tasks(models.Model):
    taskFolder = models.CharField(max_length=200)
    totalCompilation = models.IntegerField()
    finishedCompilation = models.IntegerField()
    status = models.IntegerField()
    def __unicode__(self):
        return 'id=' + str(self.id) + ',bio="' + self.status + '"'
