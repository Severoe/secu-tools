import sys
import json
import requests

host_ip = "http://localhost:2222"
jsonDec = json.decoder.JSONDecoder()


def handin_task(srcfile, taskfile):
    files =  {'srcFile': open(srcfile, 'rb'), 'taskFile': open(taskfile, 'rb')}
    response = requests.post(host_ip+"/cmdline_preview", files=files)
    task = jsonDec.decode(response.content.decode("utf-8"))
    print("The task id is " + task['taskid'] + ".")
    print("The preview page for the task:")
    jobs = task['rows']
    print("{:<15} {:<15} {:<30} {:<25} {:<15} {:<25}".format('target_os', 'compiler', 'profiles', 'flags', 'username', 'tag'))
    for job in jobs:
        print("{:<15} {:<15} {:<30} {:<25} {:<15} {:<25}".format(job['target_os'], job['compiler'], job['profiles'], job['flag'], job['username'], job['tag']))


if __name__ == '__main__':
    '''
	1. compile with src and task file 
		- python /asda/asdasd/probacs.py compile src.c task.txt.   $compile?(y/n)
			- return task_id, preview_page
			- if compile, tracking progress
			- download
	2. terminate the task by id
	3. search the task by id
	'''
    if len(sys.argv) < 3:
        print(sys.argv)
        sys.stderr.write("input not valid\n") # might be more specific
        sys.stderr.flush()
        exit(-1)

if sys.argv[1] == "compile":
    if len(sys.argv) != 4:
        sys.stderr.write("need specify sourcefile and taskfile\n") # might be more specific
        sys.stderr.flush()
        exit(-1)

    handin_task(sys.argv[2],sys.argv[3])
    ifCompile = input("Ready to compile? (Y/N): ")
    if (ifCompile is 'Y' or ifCompile is 'y'):
        print("AA")
    else:
        exit(-1)

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
