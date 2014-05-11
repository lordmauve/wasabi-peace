import pyglet
from pyglet.window import key
from pyglet.event import EventDispatcher, EVENT_HANDLED


from euclid import Point3

from wasabisg.plane import Plane
from wasabisg.scenegraph import Camera, Scene, v3, ModelNode
from wasabisg.loaders.objloader import ObjFileLoader
from wasabisg.model import Material
from wasabisg.lighting import Sunlight


WIDTH = 1024
HEIGHT = 600

FPS = 60


model_loader = ObjFileLoader()
ship_model = model_loader.load_obj('assets/models/ship.obj')



class World(EventDispatcher):
    def __init__(self):
        self.objects = []

        self.create_scene()
        self.camera = Camera(
            pos=Point3(10, 10, 10),
            look_at=Point3(0, 1, 0),
            width=WIDTH,
            height=HEIGHT
        )

    def update(self, dt):
        """Update the world through the given time step (in seconds)."""

    def create_scene(self):
        """Initialise the scene with static objects."""
        self.scene = Scene(
            ambient=(0.1, 0.15, 0.2, 1.0),
        )
        # Sun
        self.scene.add(Sunlight(
            direction=(1, 1, 1),
            colour=(1.0, 0.8, 0.5, 1.0),
            intensity=1,
        ))
        # Sea
        self.scene.add(
            Plane(
                size=1000,
                material=Material(
                    name='sea',
                    Kd=(0.2, 0.4, 0.6)
                )
            )
        )

        # Ship, created statically for now
        ship = ModelNode(ship_model, pos=(0, 0, 0))
        self.scene.add(ship)

    def draw(self):
        self.scene.render(self.camera)


class GameState(object):
    def __init__(self, game):
        self.game = game
        self.window = game.window
        self.world = World()

    def start(self):
        pyglet.clock.schedule_interval(self.update, 1.0 / FPS)

    def stop(self):
        self.window.pop_handlers()
        pyglet.clock.unschedule(self.update)

    def draw(self):
        self.world.draw()

    def update(self, dt):
        self.world.update(dt)


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
        self.gamestate = GameState(self)
        self.gamestate.start()
        self.window.push_handlers(self.on_draw)

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
    pyglet.app.run()


if __name__ == '__main__':
    main()
