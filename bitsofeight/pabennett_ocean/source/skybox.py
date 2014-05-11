__author__ = "Peter Bennett"
__copyright__ = "Copyright 2013, Peter A Bennett"
__license__ = "LGPL"
__maintainer__ = "Peter Bennett"
__email__ = "pab850@gmail.com"
__contact__ = "www.bytebash.com"

from pyglet import *
from pyglet.gl import *

from matrix16 import Matrix16
from utilities import SkyboxVerts
from ctypes import pointer, sizeof, c_float
import numpy as np

class Skybox(object):
    def __init__(self,
        shaderProgram, camera, scale, offset,
        xpos_path, ypos_path, zpos_path,
        xneg_path, yneg_path, zneg_path
    ):
        self.camera = camera
        self.shader = shaderProgram
        self.verts, self.indices, self.vertexSize = SkyboxVerts()
        self.vertexCount = sizeof(self.indices) / sizeof(GLshort)
        
        self.positionHandle = glGetAttribLocation(self.shader.id, "vPosition")
        self.textureHandle = glGetUniformLocation(self.shader.id, "texture")
        self.modelMatrixHandle = glGetUniformLocation(self.shader.id, "model")
        self.viewMatrixHandle = glGetUniformLocation(self.shader.id, "view")
        self.projMatrixHandle = glGetUniformLocation(self.shader.id, "projection")
        
        self.view = Matrix16()
        self.modelMatrix = Matrix16()
        self.modelMatrix[0] = scale
        self.modelMatrix[5] = scale
        self.modelMatrix[10] = scale  

        self.modelMatrix[12] = offset.x
        self.modelMatrix[13] = offset.y
        self.modelMatrix[14] = offset.z
        
        # Load the skybox images and create a cubemap texture
        xneg_image = image.load(xneg_path)
        yneg_image = image.load(yneg_path)
        zneg_image = image.load(zneg_path)
        xpos_image = image.load(xpos_path)
        ypos_image = image.load(ypos_path)
        zpos_image = image.load(zpos_path)
        
        W, H, format = xneg_image.width, xneg_image.height, 'RGB'

        # Create a cubemap from the skybox images:
        glActiveTexture(GL_TEXTURE0)
        self.texture = GLuint()
        glGenTextures(1, self.texture)
        glBindTexture(GL_TEXTURE_CUBE_MAP, self.texture)
        
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)

        print ("Reading environment map images...")
        for texId, imageObj, name in (
            (GL_TEXTURE_CUBE_MAP_POSITIVE_X, xpos_image, 'xpos'),
            (GL_TEXTURE_CUBE_MAP_NEGATIVE_X, xneg_image, 'xneg'),
            (GL_TEXTURE_CUBE_MAP_POSITIVE_Y, ypos_image, 'ypos'),
            (GL_TEXTURE_CUBE_MAP_NEGATIVE_Y, yneg_image, 'yneg'),
            (GL_TEXTURE_CUBE_MAP_POSITIVE_Z, zpos_image, 'zpos'),
            (GL_TEXTURE_CUBE_MAP_NEGATIVE_Z, zneg_image, 'zneg'),
        ):
            glTexImage2D(texId, 0, GL_RGB, W, H, 0, GL_RGB, GL_UNSIGNED_BYTE, imageObj.get_data(format, -W * len(format)))
            print('%s loaded...' % name)

        glBindTexture(GL_TEXTURE_CUBE_MAP, 0)       
        '''
        Perform initial setup of this object's vertex array object, which stores
        the vertex VBO and indices VBO.
        '''
        # Vertex Array Object for Position VBOs
        self.VAO = GLuint()
        glGenVertexArrays(1,pointer(self.VAO))
        glBindVertexArray(self.VAO)
        # Vertex Buffer Objects (Positions and Indices)
        self.VBO = GLuint()
        self.IBO = GLuint()
        glGenBuffers(1, pointer(self.VBO))
        glGenBuffers(1, pointer(self.IBO))
        # Set up VBO (associated with VAO)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)      
        glBufferData(GL_ARRAY_BUFFER, sizeof(self.verts), self.verts, GL_STATIC_DRAW)
        # Positions
        glEnableVertexAttribArray(self.positionHandle) 
        glVertexAttribPointer(self.positionHandle, 3, GL_FLOAT, GL_FALSE, self.vertexSize, 0)
        # Set up IBO (associated with VAO)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.IBO)      
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, sizeof(self.indices), self.indices, GL_STATIC_DRAW)
        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        
    def draw(self, dt):
        ''' Draw this object. '''
        glUseProgram(self.shader.id)             
        glUniformMatrix4fv(self.projMatrixHandle, 1, False, self.camera.getProjection())
        glUniformMatrix4fv(self.viewMatrixHandle, 1, False, self.camera.getModelView())
        glUniformMatrix4fv(self.modelMatrixHandle, 1, False, self.modelMatrix.elements)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_CUBE_MAP, self.texture)
        glUniform1i(self.textureHandle, 0)
        glBindVertexArray(self.VAO)
        glDrawElements(GL_QUADS, self.vertexCount, GL_UNSIGNED_SHORT, 0)
        glActiveTexture(GL_TEXTURE0) 
        glBindTexture(GL_TEXTURE_CUBE_MAP, 0)        
        glBindVertexArray(0)
        glUseProgram(0)
