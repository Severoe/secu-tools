import os, sys, json, time
import requests
from configparser import ConfigParser

host_ip = None
jsonDec = json.decoder.JSONDecoder()
destination = "./"


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
	return task_id['taskid']


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


def search(cmd_arg):
	if len(cmd_arg) % 2 == 1:
		# queryset must in pair -> key, value
		sys.stderr.write("The query format is wrong, try again.\n")
		sys.stderr.flush()
		exit(-1)
	query_set = {}
	i = 0
	while i + 1 < len(cmd_arg):
		if cmd_arg[i] == '-tid':
			query_set['task_id'] = cmd_arg[i + 1]
		elif cmd_arg[i] == '-u':
			query_set['username'] = cmd_arg[i + 1]
		elif cmd_arg[i] == '-f':
			query_set['flags'] = cmd_arg[i + 1]
		elif cmd_arg[i] == '-c':
			query_set['compilers'] = cmd_arg[i + 1].replace("-", " ")
		elif cmd_arg[i] == '-t':
			query_set['tag'] = cmd_arg[i + 1]
		elif cmd_arg[i] == '-da':
			#####################################
			#expect dateformat to be yyyy-m-d-h-m
			#backend
			query_set['date_after'] = cmd_arg[i + 1]
		elif cmd_arg[i] == '-db':
			query_set['date_before'] = cmd_arg[i + 1]
		else:
			sys.stderr.write("The query format is wrong, try again\n")
			sys.stderr.flush()
			exit(-1)

		i += 2
	print(query_set)
	response = requests.post(host_ip + "/cmdline_search", data=query_set)
	res = jsonDec.decode(response.content.decode("utf-8"))
	return res


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


def printProgressBar(finished, total, length = 50, fill = '*'):
	percent = ("{0:.01f}").format(100 * (finished / float(total)))
	finishedLen = int(length * finished // total)
	bar = fill * finishedLen + '-' * (length - finishedLen)
	print('\r%s |%s| %s%% %s' % ('Progress:', bar, percent, 'Completed'), end='\r')
	if finished == total:
		print()


if __name__ == '__main__':
	'''
	1. compile with src and task file 
		- python ../../probacs.py compile src.c task.txt
			- return task_id, preview_page
			- if compile, tracking progress
			- if download, specify the task id and destination
	2. search the task by id
	3. download the task by id
	4. terminate the task by id
	'''
	## READ HOST IP ADDRESS FROM CONFIG.INI
	config = ConfigParser()
	BASE_DIR = os.path.dirname(os.path.abspath(__file__))
	config.read(os.path.join(BASE_DIR, 'config.ini'))
	host_ip = config.get("Localtest", "Local_ip")

	if len(sys.argv) < 2:
		sys.stderr.write('Probacs: Profile Based Auto Compilation System\n')
		sys.stderr.write('Provided functionalities: compile/search/download/teminate\n')
		sys.stderr.write("eg: python probacs.py compile sourcefile taskfile\n")
		sys.stderr.write("eg: python probacs.py search -tid/-u/-t/-c/-f keys\n")
		sys.stderr.write("eg: python probacs.py download task_id ./dest\n")
		sys.stderr.write("eg: python probacs.py terminate task_id\n")
		sys.stderr.flush()
		exit(-1)


	# Function 1: compile
	if sys.argv[1] == "compile":
		if len(sys.argv) != 4:
			sys.stderr.write("Please specify the source file and task file.\n")
			sys.stderr.write("eg: python probacs.py compile sourcefile taskfile\n")
			sys.stderr.flush()
			exit(-1)

		response = handin_task(sys.argv[2], sys.argv[3])
		ifCompile = input("Ready to compile? (Y/N): ")
		task_id = ""
		if ifCompile is 'Y' or ifCompile is 'y':
			task_id = confirm_compile(response.content)
			print("The task id is " + task_id)
		else:
			exit(-1)

		ifDownload = input("Do you want to download the executables? (Y/N): ")
		if ifDownload is 'Y' or ifDownload is 'y':
			destination = input("Please specify the path (Default './') : ")
			download_tasks(task_id, destination)
			print("Download completed.")
		else:
			exit(-1)


	# Function 2: search
	elif sys.argv[1] == "search":
		if len(sys.argv) < 4:
			sys.stderr.write("Please specify the keywords to search.\n")
			sys.stderr.write("keywords format: task id -tid, compiler -c (eg: gcc-4.0), flags -f, username -u, tag -t\n")
			sys.stderr.flush()
			exit(-1)
		res = search(sys.argv[2:])
		if not res:
			print("Showing 0 result of user request.")
		else:
			print("Showing " + str(len(res)) + " result of user request.")
			print("{:<25} {:<10} {:<30} {:<10} {:<15} {:<25} {:<10}".format('task_id', 'username', 'tag', 'target_os', 'compiler', 'flag', 'status'))
			for i in range(len(res)):
				task = res[i]['fields']
				print(
					"{:<25} {:<10} {:<30} {:<10} {:<15} {:<25} {:<10}".format(
						task['task_id'], task['username'], task['tag'], task['target_os'],
				task['compiler'] + " " + task['version'], task['flag'], task['status']))


	# Function 3: download
	elif sys.argv[1] == "download":
		if len(sys.argv) != 4:
			sys.stderr.write("Please specify the task id and the destination to download.\n")
			sys.stderr.write("eg: python probacs.py download task_id ./dest\n")
			sys.stderr.flush()
			exit(-1)
		print(sys.argv[2])
		download_tasks(sys.argv[2], sys.argv[3])
		print("Download completed.")


	# Function 4: terminate
	elif sys.argv[1] == "terminate":
		if len(sys.argv) != 3:
			sys.stderr.write("Please specify the task id to terminate.\n")
			sys.stderr.write("eg: python probacs.py terminate task_id\n")
			sys.stderr.flush()
			exit(-1)
		print(sys.argv[2])
		terminate(sys.argv[2])
		print("The task is terminated.")

	else:
		sys.stderr.write('Probacs: Profile Based Auto Compilation System\n')
		sys.stderr.write(
			'Provided functionalities: compile/search/download/teminate\n')
		sys.stderr.write("eg: python probacs.py compile sourcefile taskfile\n")
		sys.stderr.write("eg: python probacs.py search -tid/-u/-t/-c/-f keys\n")
		sys.stderr.write("eg: python probacs.py download task_id ./dest\n")
		sys.stderr.write("eg: python probacs.py terminate task_id\n")
		exit(-1)
