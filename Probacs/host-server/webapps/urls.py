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
    url(r'^$', views.home, name='home'),
    # url(r'^uploadSrc$', views.rcvSrc, name='uploadSrc'),
    url(r'^paramUpload$', views.param_upload, name='paramUpload'),
    # url(r'^uploadWin$', views.upWin, name='uploadWin'),
    url(r'^saveExe$', views.saveExe, name='saveExe'),
    # url(r'^download_file$', views.send_zip, name='download_file'),
    url(r'^download_tar$', views.wrap_dir, name='download_tar'),

    url(r'^search_panel$', views.search_panel, name='search_panel'),
    url(r'^check_status$', views.check_status, name='check_status'),
    url(r'^download_search$', views.download_search, name='download_search'),
    
    # url(r'^test$', views.test, name='test'),
    url(r'^redirect_trace$', views.redirect_trace, name='redirect_trace'),
    url(r'^terminate$', views.terminate, name='terminate'),
    
    
    url(r'^preview$', views.preview, name='preview'),
    url(r'^rcv_compilation', views.rcv_platform_result, name='rcv_platform_result'),

    url(r'^peek_profile$', views.peek_profile, name='peek_profile'),

    url(r'^addCompiler', views.addCompiler, name='addCompiler'),
    url(r'^addProfile', views.addProfile, name='addProfile'),
    
    url(r'^addCompiler', views.addCompiler, name='addCompiler'),
    url(r'^addProfile', views.addProfile, name='addProfile'),
    
    url(r'^manageCompiler', views.manageCompiler, name='manageCompiler'),
    url(r'^manageProfile', views.manageProfile, name='manageProfile'),

    url(r'^getProfile', views.getProfile, name='getProfile'),
    url(r'^getCompiler', views.getCompiler, name='getCompiler'),

    url(r'^updateProfile', views.updateProfile, name='updateProfile'),
    url(r'^updateCompiler', views.updateCompiler, name='updateCompiler'),

    url(r'^deleteProfile', views.deleteProfile, name='deleteProfile'),
    url(r'^deleteCompiler', views.deleteCompiler, name='deleteCompiler'),

    
    # url(r'^trace$', views.trace, name='trace'),
    # url(r'^tracetest$', views.tracetest, name='tracetest'),
    # url(r'^trace_test$', views.trace_test, name='trace_test'),
    url(r'^trace_task$', views.trace_task_by_id, name='trace_task'),


    ## commandline interface functions
    url(r'^cmdline_preview$', views.cmdline_preview, name='cmdline_preview'),
    url(r'^cmdline_compile$', views.cmdline_compile, name='cmdline_compile'),
    url(r'^cmdline_download$', views.cmdline_download, name='cmdline_download'),
    url(r'^cmdline_terminate$', views.cmdline_terminate, name='cmdline_terminate'),
    url(r'^cmdline_search$', views.cmdline_search, name='cmdline_search'),

    
    







]
