__author__ = "Peter Bennett"
__copyright__ = "Copyright 2012, Peter A Bennett"
__license__ = "LGPL"
__maintainer__ = "Peter Bennett"
__email__ = "pab850@gmail.com"
__contact__ = "www.bytebash.com"

''' 
This class implements the ocean surface algorithms detailed in Tessendorf's
"Simulating Ocean Water". A 2D heightmap representing the surface of a body
of water is generated.
'''

""" Renderer Imports """
from pyglet import *
from pyglet.gl import *
from ctypes import pointer, sizeof
from pyglet.window import key, mouse
from vector import Vector2, Vector3
from water import Ocean
from skybox import Skybox
import shader
       
class Scene():
    def __init__(self, window, camera, options):
        ''' Constructor '''
        # Options
        self.options = options
        # Register the renderer for control input
        self.keys = key.KeyStateHandler()
        self.pressedKeys = {}
        self.window = window
        self.window.push_handlers(self.on_key_press)
        self.window.push_handlers(self.on_key_release)
        self.window.push_handlers(self.on_mouse_motion)
        self.window.push_handlers(self.keys)   
        # Window size
        (szx, szy) = self.window.get_size()
        self.windowWidth = szx
        self.windowHeight = szy
        self.camera = camera
        
        self.time = 0.0
        
        # Ocean Render Parameters
        self.wireframe = False
        self.oceanDepth = self.options.getfloat('Scene', 'oceandepth')
        self.enableUpdates = True
        self.oceanWind = Vector2(
                            self.options.getfloat('Scene', 'oceanwindx'),
                            self.options.getfloat('Scene', 'oceanwindy'))
        self.oceanWaveHeight = self.options.getfloat('Scene', 'oceanwaveheight')
        self.oceanTileSize = self.options.getint('Scene', 'oceantilesize')
        self.oceanTiles = Vector2(
                            self.options.getint('Scene', 'oceantilesx'),
                            self.options.getint('Scene', 'oceantilesy'))
        self.period = self.options.getfloat('Scene', 'period')
        self.env_path = self.options.get('Scene', 'env_path')
        self.frame = 0
        self.skyboxScale = 640.0
        self.skyboxOffset = Vector3(0.0,0.0,0.0)

        # Compile the shader
        self.skyboxShader = shader.openfiles('shaders/skybox.vertex', 'shaders/skybox.fragment')

        # Renderables
        self.scene = []
        
        self.skybox = Skybox(
            self.skyboxShader,
            self.camera,
            self.skyboxScale,
            self.skyboxOffset,
            xpos_path=self.env_path + '/xpos.tga',
            ypos_path=self.env_path + '/ypos.tga',
            zpos_path=self.env_path + '/zpos.tga',
            xneg_path=self.env_path + '/xneg.tga',
            yneg_path=self.env_path + '/yneg.tga',
            zneg_path=self.env_path + '/zneg.tga',
        )
        self.scene.append(self.skybox)
                                
        self.ocean = Ocean(
            self.camera,
            cubemap=self.skybox,
            depth=self.oceanDepth,
            waveHeight=self.oceanWaveHeight,
            wind=self.oceanWind,
            tileSize=self.oceanTileSize,
            tilesX=self.oceanTiles.x,
            tilesZ=self.oceanTiles.y,
            period=self.period
        )
        self.scene.append(self.ocean)        

        
    def statusUpdates(self, dt):
        '''
        Called periodically by main loop for onscreen text updates
        '''
        self.status.setParameter('Wind', self.oceanWind)
        self.status.setParameter('Wave height', self.oceanWaveHeight)
        self.status.setParameter('Ocean depth', self.oceanDepth)
        self.status.setParameter('Time', self.time)

    def draw(self, dt):
    
        # Set depth
        if self.isKeyPressed(key.C):
            self.oceanDepth += 1
            self.ocean.setDepth(self.oceanDepth)
        elif self.isKeyPressed(key.V) and self.oceanDepth > 0:
            self.oceanDepth -= 1
            self.ocean.setDepth(self.oceanDepth)
    
        # Update camera orientation and position
        self.cameraUpdate(dt)
        
        if self.enableUpdates:
            self.time += dt
        else:
            dt = 0.0
        
        # Draw scene
        if self.wireframe:
            glPolygonMode(GL_FRONT, GL_LINE)
        else:
            glPolygonMode(GL_FRONT, GL_FILL)
        
        for drawable in self.scene:
            drawable.draw(dt)

        glPolygonMode(GL_FRONT, GL_FILL)

    
    def cameraUpdate(self, dt):
        self.camera.update(dt)
        
        if self.isKeyPressed(key.W):
            self.camera.addVelocity(0.0, 0.0, 2.0)
        if self.isKeyPressed(key.S):
            self.camera.addVelocity(0.0, 0.0, -2.0)
        if self.isKeyPressed(key.A):
            self.camera.addVelocity(-2.0, 0.0, 0.0)
        if self.isKeyPressed(key.D):
            self.camera.addVelocity(2.0, 0.0, 0.0)
        if self.isKeyPressed(key.Q):
            self.camera.addAngularVelocity(0.0, 0.0, 2)
        if self.isKeyPressed(key.E):
            self.camera.addAngularVelocity(0.0, 0.0, -2)
    def on_key_press(self, symbol, modifiers):
        """ Handle key press events"""
        
        # Set the pressedKeys dict to allow us to have while-key-pressed actions
        self.pressedKeys[symbol] = True
        
        if symbol == key.L:
            self.wireframe = not self.wireframe
        if symbol == key.SPACE:
            self.enableUpdates = not self.enableUpdates

        if symbol == key.NUM_1:
            self.oceanWind.x *= 2.0
            self.ocean.setWind(self.oceanWind)
        if symbol == key.NUM_2:
            self.oceanWind.x /= 2.0
            self.ocean.setWind(self.oceanWind)
        if symbol == key.NUM_4:
            self.oceanWind.y *= 2.0
            self.ocean.setWind(self.oceanWind)
        if symbol == key.NUM_5:
            self.oceanWind.y /= 2.0
            self.ocean.setWind(self.oceanWind)
        if symbol == key.NUM_7:
            self.oceanWaveHeight *= 2.0
            self.ocean.setWaveHeight(self.oceanWaveHeight)
        if symbol == key.NUM_8:
            self.oceanWaveHeight /= 2.0
            self.ocean.setWaveHeight(self.oceanWaveHeight)
        if symbol == key.P:
            self.ocean.reloadShaders()
            
    def isKeyPressed(self, symbol):
        if symbol in self.pressedKeys:
            return self.pressedKeys[symbol]
        return False
          
    def on_key_release(self, symbol, modifiers):
        """ Handle key release events """
        self.pressedKeys[symbol] = False
        
    def on_mouse_motion(self, x, y, dx, dy):
        """ Handle mouse motion events """
        self.camera.addAngularVelocity(-dx/2., dy/2., 0.0)