import os, tempfile, zipfile,tarfile, time
from datetime import datetime
from wsgiref.util import FileWrapper
from django.shortcuts import render
from secuTool.forms import *
from secuTool.models import *
from django.core.files import File 
from django.http import HttpResponse
# Create your views here.


def home(request):
	context = {}
	context['form'] = ProfileUserForm()
	return render(request,'secuTool/index.html',context)




def rcvSrc(request):
	os.system("rm -rf secu_compile")
	context = {}
	new_upload = ProfileUser()
	form = ProfileUserForm(request.POST, request.FILES, instance=new_upload)
	form.save()

	context['form']  = ProfileUserForm()
	context['message'] = 'file compile finished !'
		# context['profile'] = new_upload
	filename = request.FILES['srcCodes'].name
	print(filename)
	# check out sourcecoude filename
	# specify working dir id
	os.system("python make_compilation.py hellomake/"+filename+" secu_compile")
	print("finished compile")
	return render(request, 'secuTool/index.html', context)

# def getPhoto(request, id):
# 	profile = get_object_or_404(ProfileUser, id=id)
# 	return HttpResponse(profile.picture, content_type=profile.content_type)

# def download_file(request):
# 	print("hi there")
# 	file_data = open('src_codes/semester_course.png','rb').read()
# 	return HttpResponse(file_data, content_type="image/png")


# def serve_pdf(request):
# 	with open('src_codes/15440-p2-handout.pdf','rb') as pdf:
# 		response = HttpResponse(pdf.read())
# 		response['content_type'] = 'application/pdf'
# 		response['Content-Disposition'] = 'attachment;filename=file.pdf'
# 	return response



def wrap_dir(request):
    timestr = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    new_name = "archive_"+timestr+".tgz"
    with tarfile.open(new_name, "w:gz") as tar:
        tar.add('secu_compile', arcname=os.path.basename('secu_compile'))

    compressed_dir = open(new_name,'rb')
    response = HttpResponse(compressed_dir,content_type='application/tgz')
    response['Content-Disposition'] = 'attachment; filename='+new_name

    return response



