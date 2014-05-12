from heightfields import Tessendorf
from surface import Surface

from pyglet import *
from pyglet.gl import *

from vector import Vector2, Vector3

import shader

class Ocean():
    def __init__(self,
        camera, cubemap=None, scale=20.0, tileSize=128, tilesX=1, tilesZ=1,
        depth=30.0, waveHeight=3.125e-5, wind=Vector2(64.0,128.0), period=10.0
    ):
        self.cubemapTexture = cubemap.texture if cubemap else None
            
        self.wind = wind                    # Ocean wind in X,Z axis
        self.waveHeight = waveHeight        # The phillips spectrum parameter
        self.oceanDepth = depth
        self.period = period                # Period of ocean surface anim
        
        self.tileSize = tileSize
        self.tilesX = tilesX
        self.tilesZ = tilesZ
        self.length = tileSize              # Ocean length parameter
        self.camera = camera
        self.scale = scale

        self.surfaceShader = shader.openfiles('shaders/ocean.vertex', 'shaders/ocean.fragment')
        
        # Use Tessendorf FFT synthesis to create a convincing ocean surface.
        self.heightfield = Tessendorf(self.tileSize, self.waveHeight,  self.wind, self.length, self.period)
                                           
        # The water surface
        self.surface = Surface(
            self.surfaceShader, self.camera, cubemapTexture=self.cubemapTexture,
            heightfield=self.heightfield, tileSize=self.tileSize, tilesX=self.tilesX,
            tilesZ=self.tilesZ, scale=self.scale, offset=Vector3(0.0,self.oceanDepth,0.0)
        )
                                
    def reloadShaders(self):
        with open('shaders/ocean.fragment') as f:
            fshader = shader.FragmentShader([f.read()])
        with open('shaders/ocean.vertex') as f:
            vshader = shader.VertexShader([f.read()])

        self.surfaceShader = shader.ShaderProgram(fshader, vshader)
        self.surfaceShader.use()
        self.surface.setShader(self.surfaceShader)
                                
    def setDepth(self, depth):
        self.oceanDepth = depth
        self.surface.setDepth(self.oceanDepth)
    
    def resetHeightfield(self):
        '''
        Recreate the heightfield engine with new initial parameters, this is
        required for heightfield engines such as Tessendorf as lookup tables
        are generated upon creation based on input paramters
        '''
        del self.heightfield
        self.heightfield = Tessendorf(self.tileSize, self.waveHeight, self.wind, self.length, self.period)
        self.surface.setHeightfield( self.heightfield)   
        
    def setWind(self, wind):
        self.wind = wind      
        self.resetHeightfield()
    def setWaveHeight(self, waveHeight):
        self.waveHeight = waveHeight                        
        self.resetHeightfield()  

    def draw(self,dt):
        self.surface.draw(dt)

        
