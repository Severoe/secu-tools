import requests


host_ip = "http://localhost:7789"

def handin_task(srcfile, taskfile):
	files =  {'srcfile': open(srcfile, 'rb'), 'taskfile': open(taskfile, 'rb')}
	response = requests.post(host_ip+"/cmdline_preview", files=files)


if __name__ == '__main__':

	'''
	1. compile with src and task file 
		- python /asda/asdasd/probacs.py compile src.c task.txt.   $compile?(y/n)
			- return task-id numbers, username, tags

	2. tracking progress when compiling  -> 

		- (download by id)

		- 
	2. 

	'''
	if len(sys.argv) <3:
		print(sys.argv)
		sys.stderr.write("input not valid\n") #might be more specific
		sys.stderr.flush()
		exit(-1)

	if sys.argv[2] == "compile":
		if len(sys.argv) != 5:
			sys.stderr.write("need specify sourcefile and taskfile\n") #might be more specific
			sys.stderr.flush()
			exit(-1)
		handin_task(sys.argv[3],sys.argv[4])


