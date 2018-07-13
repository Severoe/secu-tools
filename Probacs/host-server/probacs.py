import sys,json, time
import requests

jsonDec = json.decoder.JSONDecoder()
host_ip = "http://localhost:7789"

#**************#**************#**************#**************
#**************    develop log#**************#**************
'''
    1. handle multiple source taskfile input
'''
#**************#**************#**************#**************
def handin_task(srcfile, taskfile):
	files =  {'srcFile': open(srcfile, 'rb'), 'taskFile': open(taskfile, 'rb')}
	response = requests.post(host_ip+"/cmdline_preview", files=files)
	confirm_compile(response.content)


def confirm_compile(data):
	'''
	compile by specifying task_id
	'''
	# print(params)
	print(data)
	response = requests.post(host_ip+"/cmdline_compile", data={"content":data})
	task_id = jsonDec.decode(response.content.decode("utf-8"))
	print(task_id)
	trace_task(task_id['taskid'])

def trace_task(task_id):
	'''
	tracing tasks by task_id
	''' 
	interval = 1
	keep_going = True
	while keep_going:
		time.sleep(interval)
		response = requests.get(host_ip+"/trace_task", params={"task_id":task_id})
		res = jsonDec.decode(response.content.decode("utf-8"))
		####
		# update progressbar
		####
		print(res)
		if res['finished'] == res['total']:
			keep_going = False
		


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
	if len(sys.argv) < 2:
		print(sys.argv)
		sys.stderr.write("input not valid\n") #might be more specific
		sys.stderr.flush()
		exit(-1)

	if sys.argv[1] == "compile":
		if len(sys.argv) != 4:
			sys.stderr.write("need specify sourcefile and taskfile\n") #might be more specific
			sys.stderr.flush()
			exit(-1)
		handin_task(sys.argv[2],sys.argv[3])


