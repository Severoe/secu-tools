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

class Profile_conf(models.Model):
	uploader = models.CharField(max_length=200)
	upload_time = models.DateTimeField()
	name = models.CharField(max_length=200)
	target_os = models.CharField(max_length=60)
	compiler = models.CharField(max_length=60)
	version = models.CharField(max_length=60)
	flag = models.TextField()
	



class ProfileUser(models.Model):
    # user = models.ForeignKey(User)
    # bio = models.CharField(max_length=500)
    srcCodes = models.FileField(upload_to="hellomake", blank=True)
    content_type = models.CharField(max_length=50)  #file type
    task_file = models.FileField(blank=True)
    def __unicode__(self):
        return 'id=' + str(self.id) + ',bio="' + self.content_type + '"'



class Tasks(models.Model):
	taskFolder = models.CharField(max_length=200)
	totalCompilation = models.IntegerField()
	finishedCompilation = models.IntegerField()
	status = models.IntegerField()
	def __unicode__(self):
		return 'id=' + str(self.id) + ',bio="' + self.status + '"'

