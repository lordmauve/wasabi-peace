import pyglet
from pyglet.window import key
from pyglet.event import EventDispatcher, EVENT_HANDLED


from euclid import Point3, Vector3

from wasabisg.plane import Plane
from wasabisg.scenegraph import Camera, Scene, v3, ModelNode
from wasabisg.loaders.objloader import ObjFileLoader
from wasabisg.model import Material
from wasabisg.lighting import Sunlight
from sound import Music


pyglet.resource.path += ['assets', 'assets/sounds', 'assets/textures']


WIDTH = 1024
HEIGHT = 600

FPS = 60


model_loader = ObjFileLoader()
ship_model = model_loader.load_obj('assets/models/ship.obj')
skydome = model_loader.load_obj('assets/models/skydome.obj')

# Test

class World(EventDispatcher):
    def __init__(self):
        self.objects = []

        self.create_scene()
        self.camera = Camera(
            pos=Point3(10, 10, 10),  # x, y (height), z
            look_at=Point3(0, 1, 0),
            width=WIDTH,
            height=HEIGHT
        )
        self.t = 0

    def update(self, dt):
        """Update the world through the given time step (in seconds)."""
        self.t += dt
        self.ship.rotation = (10 * self.t, 0, 1, 0)

    def create_scene(self):
        """Initialise the scene with static objects."""
        music = Music(['battletrack.mp3'])
        # music.play()

        self.scene = Scene(
            ambient=(0.1, 0.15, 0.2, 1.0),
        )
        # Sun
        self.scene.add(Sunlight(
            direction=Vector3(0.82, 0.31, 0.48),
            colour=(1.0, 0.8, 0.5, 1.0),
            intensity=3,
        ))

        # Sky dome
        self.scene.add(skydome)

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
        self.ship = ModelNode(ship_model, pos=(0, 0, 0))
        self.scene.add(self.ship)

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
        self.window.push_handlers(self.on_draw, self.on_key_press, self.on_key_release)
        self.key_timer = {key.A: pyglet.clock.Clock(),
                          key.W: pyglet.clock.Clock(),
                          key.S: pyglet.clock.Clock(),
                          key.D: pyglet.clock.Clock(),
                          }

    def on_key_press(self, symbol, modifiers):
        if not symbol in self.key_timer: return
        self.key_timer[symbol].update_time()
        if symbol == key.A:
            print 'A key was pressed'
        if symbol == key.D:
            print 'D key was pressed'
        if symbol == key.W:
            print 'W key was pressed'
        if symbol == key.S:
            print 'S key was pressed'

    def on_key_release(self, symbol, modifiers):
        if not symbol in self.key_timer: return
        held = self.key_timer[symbol].update_time()
        if symbol == key.A:
            if held < 1.0:
                # TODO - sound event "A little to port!"
                print 'light left turn'
                pass
            elif held < 2.0:
                # TODO - sound event "Turn to port!"
                print 'medium left turn'
                pass
            else:
                print 'hard left turn'
                # TODO - sound event "Hard to port!"
                pass
            print 'A key was released, held %r' % held

        if symbol == key.D:
            if held < 1.0:
                # TODO - sound event "A little to starboard!"
                print 'light right turn'
                pass
            elif held < 2.0:
                # TODO - sound event "Turn to starb'd!"
                print 'medium right turn'
                pass
            else:
                print 'hard right turn'
                # TODO - sound event "Hard to starb'd!"
                pass
            print 'D key was released, held %r' % held

        if symbol == key.W:
            if held < 1.0:
                # TODO - sound event "A touch more sail!"
                print 'small speed increase'
                pass
            elif held < 2.0:
                # TODO - sound event "More sail!"
                print 'medium speed increase'
                pass
            else:
                # TODO - sound event "Unfurl the mails'l!"
                print 'hard speed increase'
                pass
            print 'W key was released, held %r' % held

        if symbol == key.S:
            if held < 1.0:
                # TODO - sound event "Ease off the sail!"
                print 'small speed decrease'
                pass
            elif held < 2.0:
                # TODO - sound event "Ease off the mains'l!"
                print 'medium speed decrease'
                pass
            else:
                # TODO - sound event "Drop the anchor!"
                print 'hard speed decrease'
                pass
            print 'W key was released, held %r' % held

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
