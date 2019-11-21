# -*- encoding: utf-8 -*-
"""
GUI to browse amba raw streaming
"""
import sys
import numpy as np
import cv2, time
import tkinter as TK
import threading
# import socket
import argparse

import requests as req

#---- Use site-packages modules
from cyTkGUI.cy_ViPanel import tkViPanel
from cyTkGUI.cy_ViPanel import tkV3Frame
from cy_Utils.cy_TimeStamp import TimeStamp


###########################################################
# Argument Parser
###########################################################
parser = argparse.ArgumentParser()
parser.add_argument("-m", '--host', type=str, help='The host machine: localhost or IP of remote machine', default='10.34.149.29')
parser.add_argument("-p", '--port', type=int, help='The port on which to connect the host', default=-1)
parser.add_argument("-j", '--jpg', type=str, help='The jpeg file to display', default='test001.jpg')
# parser.add_argument('--jpeg_quality', type=int, help='The JPEG quality for compressing the reply', default=70)
args = parser.parse_args()


#----------------------------------------------------------------------
# Main GUI
#----------------------------------------------------------------------
class MainGUI:
	"""
	"""
	def __init__(self, url):
		self.thread = threading.Thread(target=self.Tk_mainloop, daemon=True, args=())
		self.lock = threading.Lock()

		self.url = url
		self.liveStart = False	#-- start/stop live view


	def Tk_mainloop(self):
		self.root = TK.Tk()

		#-- Create Top-Bottom frames
		self.L1_Frames = tkV3Frame(self.root).Frames

		#---------------------------------
		# Video Panel
		#---------------------------------
		#-- Use frame#0 (upper-left) to display feyeView
		self.View = tkViPanel(self.L1_Frames[0], size=(640, 480))

		#---------------------------------
		# Connection Page
		#---------------------------------
		#-- URL
		TK.Label(self.L1_Frames[1], text="URL: ").pack(side=TK.LEFT, fill=TK.Y)
		self.txtURL = TK.StringVar()
		self.entryURL = TK.Entry(self.L1_Frames[1], width=40, bd=2, textvariable=self.txtURL)
		self.entryURL.pack(side=TK.LEFT, expand=TK.YES)
		# self.txtHost.set("192.168.1.19")
		self.txtURL.set(self.url)

		#---------------------------------
		# Start/Stop Button
		#---------------------------------
		# #-- LabelFrame
		# self.calibFrame = TK.LabelFrame(self.quadFrames[3], text="Calibration")
		# self.calibFrame.pack(expand=TK.YES)

		#-- Start/Stop button
		self.btnStart = TK.Button(self.L1_Frames[2], width=20, text="START", state=TK.NORMAL, command=self.command_btnStart)
		self.btnStart.pack(expand=TK.YES)

		self.root.mainloop()


	def command_btnStart(self):
		if self.liveStart:
			print("--- btnSTOP ---")
			self.liveStart = False
			self.btnStart.configure(text="START")
		else:
			print("--- btnSTART ---")
			self.liveStart = True
			self.btnStart.configure(text="STOP")



#---------------------------------------------------------
# Main thread functions
#---------------------------------------------------------

def onClose():
	global evAckClose
	evAckClose.set()
	# print("---- Set ----")

#---------------------------------------------------------
# Main thread Entry
#---------------------------------------------------------

""" ----- Initiate Main GUI ------------------------------
"""
evAckClose = threading.Event()
evAckClose.clear()
url = 'http://192.168.7.1/frame.jpeg'
url = "http://{}".format(args.host)
if args.port > 0:
	url += ":{}".format(args.port)
url += "/{}".format(args.jpg)

mainGUI = MainGUI(url)
mainGUI.thread.start()
time.sleep(0.01)

mainGUI.root.wm_protocol("WM_DELETE_WINDOW", onClose)

TS = TimeStamp(name="QCam", enable=False)
TS.ProcStart()

frame_index = 0
while True:
	if evAckClose.isSet():
		break

	if not mainGUI.liveStart:
		time.sleep(0.5)
		print("-x-", end="")
		continue

	TS.SubStart()
	#----------------------------------------------
	# 向 server 提取影像
	#----------------------------------------------
	resp = req.get(mainGUI.url, allow_redirects=True)
	TS.SubEnd("getIMG")

	TS.SubStart()
	# print("Type - content: ", type(resp.content))
	img_array = np.frombuffer(resp.content, dtype=np.dtype('uint8'))
	img = cv2.imdecode(img_array, flags=cv2.IMREAD_UNCHANGED)
	TS.SubEnd("cvtJPG")
	mainGUI.View.show(img)

	if frame_index == 9999999:
		frame_index = 0
	else:
		frame_index += 1
	pass #-- end of if mainGUI.connected == True


cv2.destroyAllWindows()
