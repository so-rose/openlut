import multiprocessing as mp

#Future: Use GLFW!
import pygame
from pygame.locals import *

import numpy as np

MOD_OPENGL = True
try :
	from OpenGL.GL import *
	from OpenGL.GL.shaders import compileShader,ShaderProgram
	from OpenGL.GLU import *
	from OpenGL.arrays import vbo #This is a class that makes it easy to use Vertex Buffer Objects.
	from OpenGL.GL.framebufferobjects import *
	from OpenGL.GL.EXT.framebuffer_object import *
	#~ from OpenGLContext.arrays import *
except :
	print('Unable to load OpenGL. Make sure your graphics drivers are installed & up to date!')
	MOD_OPENGL = False
	

import sys, os, os.path

class Viewer :
	def __init__(self, res, title="OpenLUT Image Viewer") :
		self.res = res
		
		#Vertex shaders calculate vertex positions - gl_position, which is a vec4.
		#In our case, this vec4 is on a ortho projected square in front of the screen.
		#~ self.shaderVertex = compileShader("""#version 330 core
#~ layout (location = 0) in vec2 position;
#~ layout (location = 1) in vec2 texCoords;

#~ out vec2 TexCoords;

#~ void main()
#~ {
    #~ gl_Position = vec4(position.x, position.y, 0.0f, 1.0f); 
    #~ TexCoords = texCoords;
#~ }  
#~ """, GL_VERTEX_SHADER )
		
		#After a vertex is processed, clupping happens, etc. Then frag shader.
		#Fragment shaders make "fragments" - pixels, subpixels, hidden stuff, etc. . They can do per pixel stuff.
		#Goal: Make gl_FragColor, the color of the fragment. It's a vec4.
		#In this case, we're sampling the texture coordinates.
		#~ self.shaderFrag = compileShader("""#version 330 core
#~ in vec2 TexCoords;
#~ out vec4 color;

#~ uniform sampler2D screenTexture;

#~ void main()
#~ { 
    #~ color = texture(screenTexture, TexCoords);
#~ }
#~ """, GL_FRAGMENT_SHADER )

		#Convenience for glCreateProgram, then attaches each shader via pointer, links with glLinkProgram,
		#validates with glValidateProgram and glGetProgramiv, then cleanup & return shader program.
		#~ self.shader = Viewer.shaderProgramCompile(self.shaderVertex, self.shaderFrag)
		#~ self.vbo = self.bindVBO()
				
		#Init pygame in OpenGL double-buffered mode.
		pygame.init()
		pygame.display.set_caption(title)
		pygame.display.set_mode((res), DOUBLEBUF|OPENGL)
		
		#Initialize OpenGL.
		self.initGL()
		
	def shaderProgramCompile(*shaders) :
		prog = glCreateProgram()
		for shader in shaders :
			glAttachShader(prog, shader)
		prog = ShaderProgram(prog)
		glLinkProgram(prog)
		return prog
		
	def initGL(self) :
		'''
		Initialize OpenGL.
		'''
		#Start up OpenGL in Ortho projection mode.
		glEnable(GL_TEXTURE_2D)
		
		glViewport(0, 0, self.res[0], self.res[1])
		
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		glOrtho(0, self.res[0], self.res[1], 0, 0, 100)
		
		glMatrixMode(GL_MODELVIEW)
		#~ glUseProgram(self.shader)
		
	def resizeWindow(self, newRes) :
		#~ print(newRes)
		self.res = newRes
		pygame.display.set_mode(self.res, DOUBLEBUF|OPENGL)
		glViewport(0, 0, self.res[0], self.res[1]) #Reset viewport
		
		glMatrixMode(GL_PROJECTION) #Modify projection matrix
		glLoadIdentity() #Load in identity matrix
		glOrtho(0, self.res[0], self.res[1], 0, 0, 100) #New projection matrix
		
		glMatrixMode(GL_MODELVIEW) #Switch back to model matrix.
		glLoadIdentity() #Load an identity matrix into the model-view matrix
		
		#~ pygame.display.flip()
				
	def drawImage(self) :
		'''
		Draws an image to the screen.
		'''
		#~ print("\r", self.res, end="", sep="")
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
		
	def bindVBO(self, verts=np.array([[0,1,0],[-1,-1,0],[1,-1,0]], dtype='f')) :
		vertPos = vbo.VBO(verts)
		
		indices = np.array([[0, 1, 2]], dtype=np.int32)
		indPos = vbo.VBO(indices, target=GL_ELEMENT_ARRAY_BUFFER)
		
		return (vertPos, indPos)
		
	def bindFBO(self) :
		'''
		Create and bind a framebuffer for rendering (loading images) to.
		'''
		
		fbo = glGenFramebuffers(1) #Create framebuffer
		
		#Binding it makes the next read and write framebuffer ops affect the bound framebuffer.
		#You can also bind it specifically to read/write targets. GL_READ_FRAMEBUFFER and GL_DRAW_FRAMEBUFFER.
		glBindFramebuffer(GL_FRAMEBUFFER, fbo)
		
		#It needs 1+ same sampled buffers (color, depth, stencil) and a "complete" color attachment.
		
		#Create a texture to render to. Empty for now; size is screen size.
		tex = self.bindTex(None, res=self.res) #Fill it up with nothing, for now. It's our color attachment.
		
		glBindTexture(GL_TEXTURE_2D, 0)
		
		#Target is framebuffer, attachment is color, textarget is 2D texture, the texture is tex, the mipmap level is 0.
		#We attach the texture to the frame buffer.
		glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT1, GL_TEXTURE_2D, tex, 0)
		
		#Renderbuffers are write-only; can't be sampled, just displayed. Often used as depth and stencil. So useless here :).
		
		if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE :
			print("Framebuffer not complete!")
			
		glBindFramebuffer(GL_FRAMEBUFFER, 0); #Finally - bind the framebuffer!
		
		#We're now rendering to the framebuffer texture. How cool!
		
		return fbo
		
				
	def bindTex(self, img, res=None)	:
		'''
		Binds the image contained the numpy float array img to a 2D texture on the GPU.
		'''
		if not res: res = img.shape
		
		tex = glGenTextures(1)
		
		glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
		glBindTexture(GL_TEXTURE_2D, tex)
		
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP) #Clamp to edge
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR) #Mag/Min Interpolation
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, res[1], res[0], 0, GL_RGB, GL_FLOAT, img)
		
		return tex
		
	def display(self, fbo = 1, tex = 1) :
		'''
		Repaints the window.
		'''
		
		#Here, we do things to the framebuffer. Not the screen. Important.
		#~ glBindFramebuffer(GL_FRAMEBUFFER, fbo)
		#~ glClearColor(0, 0, 0, 1.0)
		glClear(GL_COLOR_BUFFER_BIT)
		glMatrixMode(GL_MODELVIEW)
		
		#This render is rendering to framebuffer
		glEnable(GL_TEXTURE_2D)
		self.drawImage()
		
		#~ #Back to the screen.
		#~ glBindFramebuffer(GL_FRAMEBUFFER, 0)
		#~ glClearColor(0, 1, 1, 1)
		#~ glClear(GL_COLOR_BUFFER_BIT)
		
		#~ glUseProgram(self.shader)
		#~ glBindTexture(GL_TEXTURE_2D, tex)
		
		#~ glBindVertexArray(0)
		#~ glUseProgram(0)
		
		#Updates the display.
		pygame.display.flip()
		
	def close() :
		print()
		#~ glUseProgram(0)
		pygame.quit()
		
	def run(img, xRes, yRes, title = "OpenLUT Image Viewer") :
		'''
		img is an rgb array.
		'''
		if not MOD_OPENGL: print("OpenGL not enabled. Viewer won't start."); return
		
		v = Viewer((xRes, yRes), title)
		gpuImg = v.bindTex(img)
		#~ gpuBuf = v.bindFBO()
		
		FPS = None
		clock = pygame.time.Clock()
		
		while True :			
			for event in pygame.event.get() :
				if event.type == pygame.QUIT: Viewer.close(); break
				
				if event.type == pygame.VIDEORESIZE :
					v.resizeWindow((event.w, event.h))
					
				if event.type == pygame.KEYDOWN :
					if str(event.key) == "27": Viewer.close(); break #Need to catch ESC to close the window.
					
					try :
						{
							
						}[event.key]()
					except KeyError as key :
						print("Key not mapped!")
			else :
				#This else will only run if the event loop is completed.
				#~ v.display(fbo = gpuBuf, tex = gpuImg)
				v.display()
				
				#Smooth playback at FPS.
				if FPS: clock.tick(FPS)
				else: clock.tick()
				#~ print("\r", clock.get_fps(), end="", sep="")
				
				continue
				
			break #This break will only run if the event loop is broken out of.
			
