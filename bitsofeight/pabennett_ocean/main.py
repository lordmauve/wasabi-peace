""" 
The aim of this project is to emulate the light patterns known as water caustics
typically seen on on the bottom of a swimming pool. 
"""

__author__ = "Peter Bennett"
__copyright__ = "Copyright 2012, Peter A Bennett"
__license__ = "LGPL"
__maintainer__ = "Peter Bennett"
__email__ = "pab850@gmail.com"
__contact__ = "www.bytebash.com"

import os
import ConfigParser
from pyglet import *
from pyglet.gl import *
from source import scene as sourceScene
from source import camera as sourceCamera

def getOptions():
    options = ConfigParser.RawConfigParser()
    path = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'options.ini')
    options.read(path)
    return options

def getWindow(options):
    window = pyglet.window.Window(
        caption='FFT ocean with definitely no caustics!',
        width=options.getint('Options', 'screenwidth'),
        height=options.getint('Options', 'screenheight'),
        config=Config(
            buffers=options.getint('Options', 'buffers'),
            samples=options.getint('Options', 'samples')
        ),
        vsync=False,
        fullscreen=options.getboolean('Options', 'fullscreen')
    )
    window.set_exclusive_mouse(options.getboolean('Options', 'mousefocus'))
    return window

def getCamera(options):
    camera = sourceCamera.Camera(
        options.getint('Options', 'screenwidth'),
        options.getint('Options', 'screenheight'),
        options.getfloat('Options', 'vfov'),
        0.1,
        3000.0
    )
    # Offset and orient the camera so that it is looking at the water.
    camera.setpos(100.0, 140.0, 150.0)
    camera.orient(225.0,-55.0,0.0)
    return camera

def getScene(window, options):
    return sourceScene.Scene(window, getCamera(options), options)

window = None
scene = None

# Main Render Loop
def on_draw(dt):
    window.clear()
    scene.draw(dt)

def main():
    options = getOptions()
    glClearColor(0.0, 0.49, 1.0 ,1.0)
    glViewport(0, 0,
        options.getint('Options', 'screenwidth'),
        options.getint('Options', 'screenheight')
    )
    glEnable(GL_DEPTH_TEST)

    global window
    global scene
    window = getWindow(options)
    scene = getScene(window, options)

    clock.schedule_interval(on_draw, 1.0 / float(options.getint('Options', 'maxfps')))
    pyglet.app.run()

if __name__ == '__main__':
    main()



