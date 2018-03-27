# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User


MAX_UPLOAD_SIZE = 2500000

class ProfileUser(models.Model):
    # user = models.ForeignKey(User)
    # bio = models.CharField(max_length=500)
    srcCodes = models.FileField(upload_to="hellomake", blank=True)
    content_type = models.CharField(max_length=50)  #file type

    def __unicode__(self):
        return 'id=' + str(self.id) + ',bio="' + self.bio + '"'





