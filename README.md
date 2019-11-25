# Qcam
A small project to learn using Python Requests package to access a remote webpage.

## Usage
cmd> python3 GUI_qcam.py [--port port_num] [--host host_ip] [--jpg, -j remote_jpeg_file]

### Default arguments
	--host 		10.34.148.29
	--port,-p 	-1
		negative value tell program to bypass port designation
	--jpg, -j	test001.jpg
	
	With the default arguments, the complete URL becomes: 
	http://10.34.149.29/test001.jpg
	
### Test Scenario
I start a Docker-Nginx on Ubuntu at 10.34.149.29:7777.
Issue the following coommand would be able to connect to the server.

cmd> python3 GUI_qcam.py --port 7777


