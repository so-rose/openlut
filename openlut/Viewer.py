import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

import sys, os, os.path

class Viewer :
	def __init__(self, res, title="OpenLUT Image Viewer") :
		self.res = res
		
		pygame.init()
		pygame.display.set_caption(title)
		pygame.display.set_mode(res, DOUBLEBUF|OPENGL)
		
		self.initGL()
				
	def initGL(self) :
		'''
		Initialize OpenGL.
		'''
		glEnable(GL_TEXTURE_2D)
		
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		glOrtho(0, self.res[0], self.res[1], 0, 0, 100)
		
		glMatrixMode(GL_MODELVIEW)
		
		#~ glClearColor(0, 0, 0, 0)
		#~ glClearDepth(0)
		#~ glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
		
	#~ def resizeWindow(self, newRes) :
		#~ self.res = newRes
		#~ pygame.display.set_mode(self.res, RESIZABLE|DOUBLEBUF|OPENGL)
		##~ glLoadIdentity()
		##~ glOrtho(0, self.res[0], self.res[1], 0, 0, 100)
		
		##~ glMatrixMode(GL_MODELVIEW)
	
	def drawQuad(self) :
		'''
		Draws an image to the screen.
		'''
		glBegin(GL_QUADS)
		
		glTexCoord2i(0, 0)
		glVertex2i(0, 0)
		
		glTexCoord2i(0, 1)
		glVertex2i(0, self.res[1])
		
		glTexCoord2i(1, 1)
		glVertex2i(self.res[0], self.res[1])
		
		glTexCoord2i(1, 0)
		glVertex2i(self.res[0], 0)
		
		glEnd()
		
	def bindTex(self, img)	:
		'''
		Binds the image contained the numpy float array img to a 2D texture on the GPU.
		'''
		id = glGenTextures(1)
		
		glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
		glBindTexture(GL_TEXTURE_2D, id)
		
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img.shape[1], img.shape[0], 0, GL_RGB, GL_FLOAT, img)
		
	def display(self) :
		'''
		Repaints the window.
		'''
		
		#Clears the "canvas"
		glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
		glMatrixMode(GL_MODELVIEW)
		
		#Maybe do them here.
		glEnable(GL_TEXTURE_2D)
		self.drawQuad()
		
		#Updates the display.
		pygame.display.flip()
		
	def close() :
		#~ print()
		pygame.quit()
		
	def run(img, xRes, yRes, title = "OpenLUT Image Viewer") :
		'''
		img is an rgb array.
		'''
		v = Viewer((xRes, yRes), title)
		v.bindTex(img)
		
		FPS = None
		clock = pygame.time.Clock()
		
		while True :
			for event in pygame.event.get() :
				if event.type == pygame.QUIT: Viewer.close(); break
				
				#~ if event.type == pygame.VIDEORESIZE :
					#~ v.resizeWindow((event.w, event.h))
					
				if event.type == pygame.KEYDOWN :
					try :
						{
							
						}[event.key]()
					except KeyError as key :
						if str(key) == "27": Viewer.close(); break #Need to catch ESC to close the window.
						print("Key not mapped!")
			else :
				#This else will only run if the event loop is completed.
				v.display()
				
				#Smooth playback at FPS.
				if FPS: clock.tick(FPS)
				else: clock.tick()
				#~ print("\r", clock.get_fps(), end="", sep="")
				
				continue
				
			break #This break will only run if the event loop is broken out of.
			
