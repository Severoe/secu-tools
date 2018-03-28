# test_v2


	- security-tool-server is the host server running on linux
		- need to change ip/port specified in global variable section in views.py 
	- win-secu-server is the working server running on windows
		- need to change ip/port specified in global variable section in views.py 
		- need environment settings: 
			- install python 3, set python environment path
			- install pip
			- need to install requests package: pip apt-get requests
			- may need to install unzipping softwares later(not in this test)



	- workflow (one total circle) for windows compliation request:
		- user upload file, click submit
		- linux host create folder for this task, store source code inside
			- embed file in http request to working server
		- working server create task folder, store src codes, 
			- create folder inside task folder storing executables and log files
			- respond back with compiled archive
		- linux server append executables into task folder, create download link

