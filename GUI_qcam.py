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
from cyCvBox.image_ROIs import ImageROIs as ROIs
from cyCvBox.image_ROIs import interpolateXY

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
		self.View = tkViPanel(self.L1_Frames[0], osdScale=1.2, size=(720, 540))	# (720, 540), (960, 720)

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

def httpGet_jpeg(url):
	# TS.SubStart()
	#----------------------------------------------
	# 向 server 提取影像
	#----------------------------------------------
	resp = req.get(mainGUI.url, allow_redirects=True)
	if resp.status_code != 200:
		return False, None
	# TS.SubEnd("getIMG")

	# TS.SubStart()
	# print("Type - content: ", type(resp.content))
	img_array = np.frombuffer(resp.content, dtype=np.dtype('uint8'))
	img = cv2.imdecode(img_array, flags=cv2.IMREAD_UNCHANGED)
	# TS.SubEnd("cvtJPG")
	return True, img


def calcualte_score(img):
	lap = cv2.Laplacian(img, -1, ksize=3)
	score = np.sum(lap)
	return score, lap


def crop_frame_roi(frame, Vt, Vb):
	rowStart, rowEnd = Vt[1], Vb[1]+1
	colStart, colEnd = Vt[0], Vb[0]+1
	# print(rowStart, rowEnd, colStart, colEnd)
	roi_img = frame[rowStart:rowEnd, colStart:colEnd,]
	return roi_img


def implant_frame_roi(frame, roi_img, Vt, Vb):
	rowStart, rowEnd = Vt[1], Vb[1]+1
	colStart, colEnd = Vt[0], Vb[0]+1
	# print(rowStart, rowEnd, colStart, colEnd)
	frame[rowStart:rowEnd, colStart:colEnd,] = roi_img
	# return roi_img

def focusing_scoring(frame, roi_rects):
	roi_scores = []
	vertices = roi_rects.get_vertex_all()
	for vtx in vertices:
		roi_score = []
		# print("Vertex: {}, {}-{}".format(vtx[0], vtx[1], vtx[2]))
		Vt, Vb = vtx[1], vtx[2]

		roi_img = crop_frame_roi(frame, Vt, Vb)
		score, lap_img = calcualte_score(roi_img)

		roi_score.append(vtx[0]) #-- store roi name
		roi_score.append(score/100.0)	 # store roi's focusing score
		roi_scores.append(roi_score)

		#-- 鑲嵌 edge 影像
		implant_frame_roi(frame, lap_img, Vt, Vb)

	return roi_scores


def draw_focusing(frame, roi_rects, roi_scores):
	for roi in roi_scores:
		roi_name, score = roi
		roi_rects.draw(roi_name, frame, text="{}".format(score))


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
# url = 'http://192.168.7.1/frame.jpeg'
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

#----------------------------------------------------
# 讀取影像初始參數
#----------------------------------------------------
print("Connecting {} for initial configuration...".format(mainGUI.url))
frame_ww, frame_hh = -1, -1
succ, frame_img = httpGet_jpeg(mainGUI.url)
if not succ:
	raise RuntimeError("Failed capturing jpeg from: {}".fomat(mainGUI.url))
	exit()
frame_hh, frame_ww = frame_img.shape[:2]
frame_Vt = (0, 0)		#-- image 左上頂點
frame_Vb = (frame_ww-1, frame_hh-1)	#-- image 右下頂點
if True:
	print("frame dimension: {} x {}".format(frame_ww, frame_hh))
	print("frame vertex: {} ~ {}".format(frame_Vt, frame_Vb))


#----------------------------------------------------
# Create ROI rectangles
#----------------------------------------------------
roi_size = (int(frame_ww/10.0), int(frame_hh/10.0))
frame_CC = (int(frame_ww/2.0), int(frame_hh/2.0))	#-- 畫面中心座標
roi_rects = ROIs(frame_ww, frame_hh)
corner_field = 1.0 - 0.65

#-- 中心 ROI (Cx)
roi_rects.add("Cx", frame_CC, roi_size)

#-- 左上 ROI (Q01), field @ 0.65
Qcc = interpolateXY(frame_Vt, frame_CC, corner_field)
roi_rects.add("Q00", Qcc, roi_size)

#-- 左下 ROI (Q10), field @ 0.65
Qcc = interpolateXY((0, frame_Vb[1]), frame_CC, corner_field)
roi_rects.add("Q10", Qcc, roi_size)

#-- 右上 ROI (Q01), field @ 0.65
Qcc = interpolateXY((frame_Vb[0], 0), frame_CC, corner_field)
roi_rects.add("Q01", Qcc, roi_size)

#-- 右下 ROI (Q11), field @ 0.65
Qcc = interpolateXY(frame_Vb, frame_CC, corner_field)
roi_rects.add("Q11", Qcc, roi_size)


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
	if resp.status_code != 200:
		print("-p-", end="")
		continue
	TS.SubEnd("getIMG")

	TS.SubStart()
	# print("Type - content: ", type(resp.content))
	img_array = np.frombuffer(resp.content, dtype=np.dtype('uint8'))
	img = cv2.imdecode(img_array, flags=cv2.IMREAD_UNCHANGED)
	TS.SubEnd("cvtJPG")

	#--- 計算調焦分數
	scores = focusing_scoring(img, roi_rects)

	#--- 畫框 and 分數
	draw_focusing(img, roi_rects, scores)



	mainGUI.View.show(img, name="#{:04d}".format(frame_index))

	if frame_index == 9999:
		frame_index = 0
	else:
		frame_index += 1
	pass #-- end of if mainGUI.connected == True

	# break

cv2.destroyAllWindows()
