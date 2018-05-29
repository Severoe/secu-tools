"""webapps URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from secuTool import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.home),
    url(r'^uploadSrc$', views.rcvSrc, name='uploadSrc'),
    # url(r'^uploadWin$', views.upWin, name='uploadWin'),
    url(r'^saveExe$', views.saveExe, name='saveExe'),
    # url(r'^download_file$', views.send_zip, name='download_file'),
    # url(r'^serve_pdf$', views.serve_pdf, name='serve_pdf'),
    url(r'^download_tar$', views.wrap_dir, name='download_tar'),

    

# download_fil
]
