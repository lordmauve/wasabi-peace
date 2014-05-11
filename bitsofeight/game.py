import pyglet
from pyglet.window import key
from pyglet.event import EventDispatcher, EVENT_HANDLED
from pyglet import gl


WIDTH = 1024
HEIGHT = 600

FPS = 60


class World(EventDispatcher):
    def __init__(self, keyboard):
        self.keyboard = keyboard
        self.objects = []

    def draw(self):
        # draw a black background
        gl.glClearColor(0, 0, 0, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
#        gl.glMatrixMode(gl.GL_PROJECTION)
#        gl.glLoadIdentity()
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        gl.glDisable(gl.GL_DEPTH_TEST)
#        self.camera.set_matrix()
        
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glEnable(gl.GL_BLEND)

#        vp = self.camera.get_viewport()



class GameState(object):
    def __init__(self, game):
        self.game = game
        self.window = game.window
        self.keyboard = key.KeyStateHandler()

        # load the sprites for objects
        #load_all()

        # initialise the World and start the game
        self.world = World(self.keyboard)
        #self.world.set_handler('on_player_death', self.on_player_death)

    def start(self):
        self.window.push_handlers(
            self.keyboard
        )
        self.window.push_handlers(self.on_key_press)
        pyglet.clock.schedule_interval(self.update, 1.0 / FPS)
        self.start_mission()

    def stop(self):
        self.window.pop_handlers()
        self.window.pop_handlers()
        pyglet.clock.unschedule(self.update)

    def draw(self):
        self.world.draw()

    def update(self, ts):
        pass
        #self.world.update(ts)


class Game(object):
    def __init__(self, windowed):
        global WIDTH, HEIGHT
        if windowed:
            self.window = pyglet.window.Window(
                width=WIDTH,
                height=HEIGHT
            )
        else:
            self.window = pyglet.window.Window(fullscreen=True)
            WIDTH = self.window.width
            HEIGHT = self.window.height
        self.game = None
        self.menu = None
        self.gamestate = None

        self.window.push_handlers(self.on_draw)

    def start_menu(self):
        self.gamestate = GameState(self)

    def run(self):
        while True:
            try:
                pyglet.app.run()
            except Exception:
                import traceback
                traceback.print_exc()
            else:
                break

    def on_draw(self):
        self.gamestate.draw()



def main():
    from optparse import OptionParser
    parser = OptionParser('%prog [-f]')
    parser.add_option('-f', '--fullscreen', action='store_true', help='Start in full screen mode')
    
    options, args = parser.parse_args()

    game = Game(
        windowed=not options.fullscreen
    )
    
    game.start_menu()

    game.run()


if __name__ == '__main__':
    main()
