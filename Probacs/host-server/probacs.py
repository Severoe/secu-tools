from time import sleep
import pdb


def handin_task(srcfile, taskfile):
	pass

def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='*'):
	percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
	filledLength = int(length * iteration // total)
	bar = fill * filledLength + '-' * (length - filledLength)
	print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='\r')
	# Print New Line on Complete
	if iteration == total:
		print()


if __name__ == '__main__':
	'''
	1. compile with src and task file 
		- python probacs.py compile src.c task.txt
			- return task_id, numbers, username, tags
			- print the preview page and ask if ready to compile?
			- Y: compile with progress bar
				- download it?

	2. tracking progress when compiling  -> 
		- (download by id)
		- 
	'''
	##

	##
	ifCompile = input("Ready to compile? (Y/N): ")

	items = list(range(0, 57))
	l = len(items)
	printProgressBar(0, l, prefix='Progress:', suffix='Complete', length=50)
	for i, item in enumerate(items):
		sleep(0.1)
		printProgressBar(
			i + 1, l, prefix='Progress:', suffix='Complete', length=50)

	# print "{:<8} {:<15} {:<10}".format('Key','Label','Number')
	# for k, v in d.iteritems():
	# 	label, num = v
	# 	print "{:<8} {:<15} {:<10}".format(k, label, num)
