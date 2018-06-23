

@transaction.atomic
def rcvSrc(request):
    timestr = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    #create unique task forder for each task, inside which includes:
    # srcCode, <profiles>, compiled file & log, 
    # the archive for downloading will be delete 
    taskName = timestr
    taskFolder = rootDir+timestr
    codeFolder = taskFolder+"/"+"srcCodes"
    os.system("mkdir "+taskFolder)
    context = {}
    srcPath = ''
    #######################
    # handle bad submit request (attention, undergoing compilation info may be missing by rendering blank)
    #######################
    if 'srcCodes' not in request.FILES or 'task_file' not in request.FILES:
        return redirect(home)
    #######################
    #save source files in taskfolder
    #######################
    filename = request.FILES['srcCodes'].name
    taskfile = request.FILES['task_file'].name
    print(request.FILES['srcCodes'].content_type)
    if request.FILES['srcCodes'].content_type not in ['application/x-tar','application/gzip','application/zip']:
        #indicating a single file
        os.system("mkdir "+codeFolder)
        srcPath = codeFolder+"/"+filename
        with open(srcPath,'wb+') as dest:
            for chunk in request.FILES['srcCodes'].chunks():
                dest.write(chunk)
    else:
        #if user upload tar bar, extract and save into srcCode folder
        #also upload filename to be main filename
        with open(taskFolder+'/'+filename,'wb+') as dest:
            for chunk in request.FILES['srcCodes'].chunks():
                dest.write(chunk)
        os.system('tar xvzf '+ taskFolder+'/'+filename+" -C "+srcCodes)
        os.system('mv '+taskFolder+'/'+filename.split('.')[0]+' '+codeFolder)
        srcPath = codeFolder+"/"+filename
        # update filename to be the main srcfile name if tast srcfile is a tarball
    #######################
    # write task specify file to taskFolder
    #######################
    taskPath = taskFolder+"/"+taskfile
    with open(taskPath,'wb+') as dest:
        for chunk in request.FILES['task_file'].chunks():
            dest.write(chunk)


    #######################
    # parse task file
    #######################
    p = parseTaskFile(taskPath)
    print(p)
    message = p.get("message", None)
    if message != None:
        context['form']  = ProfileUserForm()
        context['message'] = message
        return render(request, 'secuTool/index.html',context)

    #form request format from parse.py for each task
    for param in p:
        task_compiler = Compiler_conf.objects.get(target_os=param['target_os'], compiler=param['compiler'],
        version=param['version'])
        task_http = task_compiler.ip + ":"+task_compiler.port+task_compiler.http_path
        # permute flags combination  from diff flags
        jsonDec = json.decoder.JSONDecoder()
        flag_from_profile = []
        for profile_name in param['profile']:
            # print(profile_name)
            p_tmp = Profile_conf.objects.get(name=profile_name, target_os=param['target_os'],compiler=param['compiler'],
                version=param['version'])
            flag_from_profile.append(jsonDec.decode(p_tmp.flag))
        compile_combination = [[]]
        for x in flag_from_profile:
            compile_combination = [i + [y] for y in x for i in compile_combination]
        compile_combination = [" ".join(x) for x in compile_combination]
        compile_combination = [x.replace(" ","_") for x in compile_combination]
        #############################
        # add entries into task database 
        for ele in compile_combination:
            new_task = Task(task_id=taskName,username=param['username'],
                tag=None if not 'tag' in param else param['tag'],
                src_file=filename,target_os=param['target_os'], 
                compiler=param['compiler'],version=param['version'],flag=ele)
            new_task.save()
        final_flags = ",".join(compile_combination) 
        #############################
        # calling compilation tasks
        #############################
        if task_http == self_ip:
            outputDir = taskFolder+"/"+"secu_compile"
            data = {
            'task_id':taskName,'target_os':param['target_os'],'compiler':param['compiler'],'version':param['version'],'srcPath':srcPath,
            'output':outputDir,'format':task_compiler.invoke_format,'flags':final_flags,
            }
            pid = os.fork()
            if pid == 0:
                compile(taskName, param['target_os'], param['compiler'], param['version'], srcPath, outputDir, task_compiler.invoke_format, final_flags,on_complete)
                #new thread
                # os.system("python make_compilation.py "+srcPath+" "+ outputDir+" "+task_compiler.invoke_format+" "+final_flags)
                print("finished compile")
                os._exit(0)  
            else:
                #parent process, simply return to client
                print("asyn call encountered")
        # if not compiling on linux host, send params to another function, interacting with specific platform server
        else:
            upload_to_platform(param,task_http, task_compiler.invoke_format, final_flags, taskName, taskFolder, codeFolder,filename)
        
    context['task_id'] = taskName
    context['message'] = "file is compiling..."
    context['form'] = ProfileUserForm()
    context['progress'] = 'block'
    context['linux_taskFolder'] = taskName
    return render(request, 'secuTool/index.html', context)






                        <input type="checkbox" /> max_speed<br/>
                    <input type="checkbox" /> max_optimization<br/>