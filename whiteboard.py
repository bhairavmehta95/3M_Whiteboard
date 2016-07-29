#!/usr/bin/env python

import sys

sys.path.append('/usr/local/lib/python2.7/site-packages')

import numpy
import cv2
import cv2.cv as cv
from squares import *
import os
import time
import sys
import video
from common import mosaic
from PIL import ImageEnhance, ImageChops
import PIL.Image
from skimage.measure import compare_ssim as ssim
import math, operator
import datetime
from time import strftime
import os
from reportlab.platypus.flowables import KeepTogether
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch

from pits_whiteboard import find_squares

styles = getSampleStyleSheet()


# Global variables for pdf
parts = []
doc = SimpleDocTemplate('generated.pdf', pagesize = letter)
save_count = 0
BACKGROUND = 0

# TO DO: Fix this so it takes in a numpy array
# A function that computes the most dominant color and the number of occurances
def compute_dominant_pixel(): 
	im = PIL.Image.open('fakepath.jpg')
	# will not be neccesary with smaller images
	colors = im.getcolors(im.size[0] * im.size[1])
	R = 0
	G = 0
	B = 0
	count = len(colors)

	for color in colors:
		R += color[1][0]
		G += color[1][1]
		B += color[1][2]

	print R/count, G/count, B/count
	return [R/count, G/count, B/count]


# A function that simply reads and returns the image from 'cap(ture device)'
def get_image(cap):
 retval, im = cap.read()
 return im 

# Builds the final PDF from global parts list
def generate_pdf():
	global parts

	doc.build(parts)

# checks if color value is APPROXIMATELY white
# if numbers are approx the same, then they are white/gray
def dominant_pixel_diff(values):
	min_val = min(values[0], values[1], values[2])
	max_val = max(values[0], values[1], values[2])

	# is approximately white bc min and max difference is 
	
	return abs(min_val - max_val)


# A function that sets up the camera and takes the original bg picture
def start_up():
	global BACKGROUND

	try: src = sys.argv[1]
	except: src = 0

	ramp_frames = 30 
	cap = cv2.VideoCapture(src)
	cap.set(cv2.cv.CV_CAP_PROP_EXPOSURE, .5)
	cap.set(cv2.cv.CV_CAP_PROP_CONTRAST, 10000) 
	for i in xrange(ramp_frames):
		temp = cap.read()


	# capture, save image
	camera_capture = get_image(cap)
	filename = "whiteboard_session/full/0.jpg"

	cv2.imwrite(filename, camera_capture)

	im = PIL.Image.open(filename)

	# will not be neccesary with smaller images
	colors = im.getcolors(im.size[0] * im.size[1])

	values = colors[0][1]

	values = values[0] * values[0] + values[1] * values[1] + values[2] * values[2]

	BACKGROUND = np.sqrt(values)
	print BACKGROUND, 'is bg'
	return cap

# A function that calculates cosines between edges
def angle_cos(p0, p1, p2):
	d1, d2 = (p0-p1).astype('float'), (p2-p1).astype('float')
	return abs( np.dot(d1, d2) / np.sqrt( np.dot(d1, d1)*np.dot(d2, d2) ) )

# A function that takes, analyzes, and outputs a picture (to a PDF)
def take_picture(cap, pic_count, centers):
	ret, img = cap.read()
	ret, img = cap.read()

	global save_count

	# so we can save at the right spot
	start_save_count = save_count

	# uses last picture as BG, saves this picture as new (changed)
	original_str = 'whiteboard_session/full/' + str(pic_count - 1) + '.jpg'
	changed_str = 'whiteboard_session/full/' + str(pic_count) + '.jpg'

	cv2.imwrite(changed_str, img)

	original = cv2.imread(original_str)
	changed = img

	# Show the original
	cv2.imshow('Background Image',original)
	ch = 0xFF & cv2.waitKey()
	cv2.destroyAllWindows()

	img_changes = changed

	# converts, blurs images for image processing
	img_a = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
	img_a = cv2.GaussianBlur(img_a, (5, 5), 0)

	img_b = cv2.cvtColor(changed, cv2.COLOR_BGR2GRAY)
	img_b = cv2.GaussianBlur(img_b, (5, 5), 0)

	# calculates difference, thresholds
	img_diff = cv2.absdiff(img_a, img_b)

	thresh = cv2.threshold(img_diff, 10, 255, cv2.THRESH_BINARY)[1]

	# dilate the thresholded image to fill in holes, then find contours
	# on thresholded image

	thresh = cv2.dilate(thresh, None, iterations=2)
	(contours, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)


	# lists to store the dictionaries of contours
	contours_final = []
	context_dict = []
	count = 0

	# loop over the contours
	for c in contours:
		context = {}

		# if the area is too small, skip it
		if cv2.contourArea(c) < 1000:
			continue

		# compute the bounding box for the contour, draw it on the frame
		(x, y, w, h) = cv2.boundingRect(c)
		rect = cv2.rectangle(img_changes, (x, y), (x + w, y + h), (255, 0, 0), 2)
		
		cnt_len = cv2.arcLength(c, True)
		cnt = cv2.approxPolyDP(c, 0.05*cnt_len, True)

		shape = 'default'
		
		# Makes a bounding rectangle
		(x, y, w, h) = cv2.boundingRect(cnt)
		roi = cv2.boundingRect(cnt)
		cnt = cnt.reshape(-1, 2)

		# check if post it note 

		############# POST ITS

		# splices the image where the difference was found
		roi_original = original[y:y+h, x:x+w]
		roi_changed = changed[y:y+h, x:x+w]

		cv2.imshow('original', roi_original)
		cv2.imshow('changed', roi_changed)
		ch = 0xFF & cv2.waitKey()
		cv2.destroyAllWindows()

		# computes dominant color and pixel
		cv2.imwrite('fakepath.jpg', roi_original)

		original_dominant = compute_dominant_pixel()

		cv2.imwrite('fakepath.jpg', roi_changed)	

		changed_dominant = 	compute_dominant_pixel()

		original_dominant = dominant_pixel_diff(original_dominant)
		changed_dominant = dominant_pixel_diff(changed_dominant)

		# Saves the changed file
		save_string = 'whiteboard_session/img_test/' + str(save_count) + '.jpg'
		save_count += 1

		# Original is more homogenous, so it is closer to a white or gray
		if changed_dominant > original_dominant:
			print "finding additions"
			context['change'] = 'added'
			cv2.imwrite('fakepath.jpg', roi_changed)
			count_ = save_count
			find_squares(count_)
			cv2.imwrite(save_string, roi_changed)

		else:
			print "finding removals"
			context['change'] = 'removed'
			cv2.imwrite('fakepath.jpg', roi_original)
			cv2.imshow('original in removed', roi_original)
			count_ = save_count
			find_squares(count_)
			cv2.imwrite(save_string, roi_original)
		

		context['shape'] = shape
		context['roi'] = rect

		# Adds them to the list
		contours_final.append(rect)
		context_dict.append(context)

	# Stores where we end the save count
	end_save_count = save_count

	string_to_write = 'whiteboard_session/changes/' + str(pic_count) + '.jpg'
	cv2.imwrite(string_to_write, img_changes)
	
	#### BUILDING THE PDF ####

	# build into document
	global parts
	style = styles["Normal"]
	title = 'Start of timestamp: ' + str(start_save_count)
	p = Paragraph(title, style)
 	parts.append(p)
 	string = 'Full board at timestamp:' + str(start_save_count)
 	file = 'whiteboard_session/full/' + str(pic_count) + '.jpg'
 	p = Paragraph(string, style)
 	parts.append(p)
 	parts.append(KeepTogether(Image(file)))


 # 	# Added post its
 	
 # 	tmp = start_save_count
 # 	it = 0

 # 	string = 'Post Its Added at timestamp:' + str(start_save_count)
 # 	p = Paragraph(string, style)
 # 	parts.append(p)

	# while tmp < end_save_count:
	# 	if context_dict[it]['shape'] == 'post' and context_dict[it]['change'] == 'added':
	# 		file = 'whiteboard_session/img_test/' + str(start_save_count) + '.jpg'
	# 		parts.append(KeepTogether(Image(file)))
	# 	tmp += 1
	# 	it += 1

	# # Removed post its
 	
 # 	tmp = start_save_count
 # 	it = 0

 # 	string = 'Post Its Removed at timestamp:' + str(start_save_count)
 # 	p = Paragraph(string, style)
 # 	parts.append(p)

	# while tmp < end_save_count:
	# 	if context_dict[it]['shape'] == 'post' and context_dict[it]['change'] == 'removed':
	# 		file = 'whiteboard_session/img_test/' + str(start_save_count) + '.jpg'
	# 		parts.append(KeepTogether(Image(file)))
	# 	tmp += 1
	# 	it += 1

 # 	# Added Other Objects
 	
 # 	tmp = start_save_count
 # 	it = 0

 # 	string = 'Other Objects Added at timestamp:' + str(start_save_count)
 # 	p = Paragraph(string, style)
 # 	parts.append(p)

	# while tmp < end_save_count:
	# 	if context_dict[it]['shape'] != 'post' and context_dict[it]['change'] == 'added':
	# 		file = 'whiteboard_session/img_test/' + str(start_save_count) + '.jpg'
	# 		parts.append(KeepTogether(Image(file)))
	# 	tmp += 1
	# 	it += 1

	# # Removed Other Objects
 	
 # 	tmp = start_save_count
 # 	it = 0

 # 	string = 'Other Objects Removed at timestamp:' + str(start_save_count)
 # 	p = Paragraph(string, style)
 # 	parts.append(p)

	# while tmp < end_save_count:
	# 	if context_dict[it]['shape'] != 'post' and context_dict[it]['change'] == 'removed':
	# 		file = 'whiteboard_session/img_test/' + str(start_save_count) + '.jpg'
	# 		parts.append(KeepTogether(Image(file)))
	# 	tmp += 1
	# 	it += 1


	## End generation of PDF

	#### SHOWING WHAT WAS CHANGED ####

	cv2.drawContours(original, contours_final, -1, (255, 0, 0), 3 )
	save_string = 'whiteboard_session/pdf/' + str(pic_count) + '.jpg'
	cv2.imwrite(save_string, changed)
	# cv2.imshow('im',original)
	# cv2.imshow('im removed', changed)

	ch = 0xFF & cv2.waitKey()
	cv2.destroyAllWindows()

	cv2.imshow('imdf', img_changes)

	ch = 0xFF & cv2.waitKey()
	cv2.destroyAllWindows()


	return centers

if __name__ == '__main__':
	from glob import glob
	# global doc
	print "Starting up, please wait..."
	cap = start_up()
	count = 1
	centers = []
	while True:
		print "Please type h(elp), p(icture), or q(uit)"
		val = raw_input('> ')
		if val == 'h' or val == 'help':
			print "This is a program that does fun things, try another command!"
		elif val == 'q' or val == 'quit':
			doc.build(parts)
			break
		elif val == 'p' or val == 'picture':
			centers = take_picture(cap, count, centers)
			count += 1
		else:
			print "Not a valid command, try again"

	