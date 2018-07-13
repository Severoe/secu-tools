import sys,json, time, os
import requests
from configparser import ConfigParser

host_ip = None#"http://localhost:7789"
jsonDec = json.decoder.JSONDecoder()
destination = "./"
#**************#**************#**************#**************
#**************    develop log#**************#**************
'''
	1. handle multiple source taskfile input
'''
#**************#**************#**************#**************
def handin_task(srcfile, taskfile):
	'''
	send sourcefile and taskfile to host server, reveice compilation preview info
	'''
	files =  {'srcFile': open(srcfile, 'rb'), 'taskFile': open(taskfile, 'rb')}
	response = requests.post(host_ip+"/cmdline_preview", files=files)
	task = jsonDec.decode(response.content.decode("utf-8"))
	print("The task id is " + task['taskid'] + ".")
	print("The preview page for the task:")
	jobs = task['rows']
	print("{:<15} {:<15} {:<30} {:<25} {:<15} {:<25}".format('target_os', 'compiler', 'profiles', 'flags', 'username', 'tag'))
	for job in jobs:
		print("{:<15} {:<15} {:<30} {:<25} {:<15} {:<25}".format(job['target_os'], job['compiler'], job['profiles'], job['flag'], job['username'], job['tag']))
	return response

def confirm_compile(data):
	'''
	compile by specifying task_id
	'''
	response = requests.post(host_ip+"/cmdline_compile", data={"content":data})
	task_id = jsonDec.decode(response.content.decode("utf-8"))
	trace_task(task_id['taskid'])
	download_tasks(task_id['taskid'],destination)



def trace_task(task_id):
	'''
	tracing tasks by task_id, receive log report for this task id
	''' 
	interval = 1
	keep_going = True
	while keep_going:
		time.sleep(interval)
		response = requests.get(host_ip+"/trace_task", params={"task_id":task_id})
		res = jsonDec.decode(response.content.decode("utf-8"))
		printProgressBar(res['finished'], res['total'])
		if res['finished'] == res['total']:
			success = 0
			fail = 0
			for log in res['log_report']:
				if log['status'] == "success":
					success += 1
				elif log['status'] == "fail":
					fail += 1
			print("There are " + str(res['total']) + " jobs in this task, " + str(success) + " success, " + str(fail) + " fail")
			keep_going = False
		

def download_tasks(task_id, destination):
	'''
	download task archive from host, save to destination
	'''
	response = requests.post(host_ip+"/cmdline_download", data={"task_id":task_id})
	with open(destination+"archive_"+str(task_id)+".tgz", 'wb') as w:
	    w.write(response.content)

def terminate(task_id):
	'''
	midway termination for specific task
	'''
	response = requests.post(host_ip+"/cmdline_terminate", data={"task_id":task_id})
	res = jsonDec.decode(response.content.decode("utf-8"))
	print(res)




	# files =  {'srcFile': open(srcfile, 'rb'), 'taskFile': open(taskfile, 'rb')}
	# response = requests.post(host_ip+"/cmdline_preview", files=files)
	# task = jsonDec.decode(response.content.decode("utf-8"))
	# print("The task id is " + task['taskid'] + ".")
	# print("The preview page for the task:")
	# jobs = task['rows']
	# print("{:<15} {:<15} {:<30} {:<25} {:<15} {:<25}".format('target_os', 'compiler', 'profiles', 'flags', 'username', 'tag'))
	# for job in jobs:
	#     print("{:<15} {:<15} {:<30} {:<25} {:<15} {:<25}".format(job['target_os'], job['compiler'], job['profiles'], job['flag'], job['username'], job['tag']))


def printProgressBar(finished, total, length = 50, fill = '*'):
	percent = ("{0:.01f}").format(100 * (finished / float(total)))
	finishedLen = int(length * finished // total)
	bar = fill * finishedLen + '-' * (length - finishedLen)
	print('\r%s |%s| %s%% %s' % ('Progress:', bar, percent, 'Completed'), end = '\r')
	if finished == total:
		print()

if __name__ == '__main__':
	'''
	1. compile with src and task file 
		- python ../../probacs.py compile src.c task.txt
			- return task_id, preview_page
			- if compile, tracking progress
			- download
	2. terminate the task by id
	3. search the task by id
	'''
	## READ HOST IP ADDRESS FROM CONFIG.INI
	config = ConfigParser()
	BASE_DIR = os.path.dirname(os.path.abspath(__file__))
	config.read(os.path.join(BASE_DIR, 'config.ini'))
	# print(BASE_DIR)
	host_ip = config.get("Localtest", "Local_ip")
	# print(host_ip)

	if len(sys.argv) < 2:
		print(sys.argv)
		sys.stderr.write("input not valid\n")
		sys.stderr.flush()
		exit(-1)

	if sys.argv[1] == "compile":
		if len(sys.argv) != 4:
			sys.stderr.write("need specify sourcefile and taskfile\n")
			sys.stderr.flush()
			exit(-1)
		handin_task(sys.argv[2],sys.argv[3])

	if sys.argv[1] == "terminate":
		if len(sys.argv) != 3:
			sys.stderr.write("need specify task_id to terminate\n") #might be more specific
			sys.stderr.flush()
			exit(-1)
		terminate(sys.argv[2])

	# ifCompile = input("Ready to compile? (Y/N): ")
	# if (ifCompile is 'Y' or ifCompile is 'y'):
	#     print("AA")
	# else:
	#     exit(-1)






	# items = list(range(0, 57))
	# l = len(items)
	# # printProgressBar(0, l, prefix='Progress:', suffix='Complete', length=50)
	# for i, item in enumerate(items):
	# 	sleep(0.1)
	# 	printProgressBar(
	# 		i + 1, l, prefix='Progress:', suffix='Complete', length=50)

	# def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
	# 	percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
	# 	filledLength = int(length * iteration // total)
	# 	bar = fill * filledLength + '-' * (length - filledLength)
	# 	print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
	# 	# Print New Line on Complete
	# 	if iteration == total: 
	# 		print()

	
		response = handin_task(sys.argv[2],sys.argv[3])
		ifCompile = input("Ready to compile? (Y/N): ")
		if (ifCompile is 'Y' or ifCompile is 'y'):
			confirm_compile(response.content)
		else:
			exit(-1)
