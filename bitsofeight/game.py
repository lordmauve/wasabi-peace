import pyglet
from pyglet.window import key
from pyglet.event import EventDispatcher, EVENT_HANDLED


from euclid import Point3, Vector3, Quaternion

from wasabisg.plane import Plane
from wasabisg.scenegraph import Camera, Scene, v3, ModelNode
from wasabisg.loaders.objloader import ObjFileLoader
from wasabisg.model import Material, Model
from wasabisg.lighting import Sunlight
from sound import Music


pyglet.resource.path += [
    'assets/sounds',
    'assets/textures',
    'assets/sprites',
    'assets/fonts'
]
pyglet.resource.reindex()
pyglet.resource.add_font('benegraphic.ttf')

WIDTH = 1024
HEIGHT = 600

FPS = 60


model_loader = ObjFileLoader()
ship_model = model_loader.load_obj('assets/models/ship.obj')
skydome = model_loader.load_obj('assets/models/skydome.obj')


class Ship(object):
    def __init__(self):
        self.model = ModelNode(ship_model)

        self.pos = Point3(0, 0, 0)
        self.angle = 0
        self.speed = 1

    def update(self, dt):
        q = Quaternion.new_rotate_axis(self.angle, Vector3(1, 0, 0))
        v = q * Vector3(0, 0, 1) * self.speed * dt

        self.pos += v

        self.model.rotation = (self.angle, 0, 1, 0)
        self.model.pos = self.pos


class World(EventDispatcher):
    def __init__(self):
        self.objects = []

        self.create_scene()
        self.camera = Camera(
            pos=Point3(10, 5, 10),
            look_at=Point3(0, 1, 0),
            width=WIDTH,
            height=HEIGHT
        )

    def spawn(self, obj):
        self.objects.append(obj)
        try:
            model = obj.model
        except AttributeError:
            pass
        else:
            self.scene.add(model)

    def update(self, dt):
        """Update the world through the given time step (in seconds)."""
        for o in self.objects:
            o.update(dt)

    def create_scene(self):
        """Initialise the scene with static objects."""
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
        self.skydome = ModelNode(skydome)
        self.scene.add(self.skydome)

        # Sea
        self.sea = ModelNode(
            Model(meshes=[
                Plane(
                    size=1000,
                    material=Material(
                        name='sea',
                        Kd=(0.2, 0.4, 0.6)
                    )
                )
            ])
        )
        self.scene.add(self.sea)

    def draw(self):
        x, _, z = self.camera.pos
        self.skydome.pos = Point3(x, 0, z)
        self.sea.pos = Point3(x, 0, z)
        self.scene.render(self.camera)


class KeyControls(object):
    """Process events from keys, and turn them into orders."""
    LOW = 0.2
    MEDIUM = 0.5
    HARD = 0.8

    def turn_left(self, held):
        if held < self.LOW:
            # TODO - sound event "A little to port!"
            print 'light left turn'
            pass
        elif held < self.MEDIUM:
            # TODO - sound event "Turn to port!"
            print 'medium left turn'
            pass
        else:
            print 'hard left turn'
            # TODO - sound event "Hard to port!"
            pass

    def turn_right(self, held):
        if held < self.LOW:
            # TODO - sound event "A little to starboard!"
            print 'light right turn'
            pass
        elif held < self.MEDIUM:
            # TODO - sound event "Turn to starb'd!"
            print 'medium right turn'
            pass
        else:
            print 'hard right turn'
            # TODO - sound event "Hard to starb'd!"
            pass

    def speed_up(self, held):
        if held < self.LOW:
            # TODO - sound event "A touch more sail!"
            print 'small speed increase'
            pass
        elif held < self.MEDIUM:
            # TODO - sound event "More sail!"
            print 'medium speed increase'
            pass
        else:
            # TODO - sound event "Unfurl the mails'l!"
            print 'hard speed increase'
            pass

    def slow_down(self, held):
        if held < self.LOW:
            # TODO - sound event "Ease off the sail!"
            print 'small speed decrease'
            pass
        elif held < self.MEDIUM:
            # TODO - sound event "Ease off the mains'l!"
            print 'medium speed decrease'
            pass
        else:
            # TODO - sound event "All stop!"
            print 'hard speed decrease'
            pass

    def __init__(self):
        self.bindings = {
            key.A: self.turn_left,
            key.D: self.turn_right,
            key.W: self.speed_up,
            key.S: self.slow_down
        }
        self.key_timer = {}
        self.t = 0

    def update(self, dt):
        self.t += dt

    def on_key_press(self, symbol, modifiers):
        if symbol not in self.bindings:
            return
        self.key_timer[symbol] = self.t

    def on_key_release(self, symbol, modifiers):
        try:
            func = self.bindings[symbol]
        except KeyError:
            pass
        else:
            held = self.t - self.key_timer[symbol]
            func(held)

    def push_handlers(self, window):
        window.push_handlers(
            self.on_key_press,
            self.on_key_release
        )


class BattleMode(object):
    """Sailing on the open ocean!"""
    def __init__(self, game):
        self.game = game
        self.window = game.window
        self.world = World()

        self.ship = Ship()
        self.world.spawn(self.ship)
        self.keys = KeyControls()

    def start(self):
        pyglet.clock.schedule_interval(self.update, 1.0 / FPS)

        self.keys.push_handlers(self.window)
        music = Music(['battletrack.mp3'])
        self.t = 0
        # music.play()

    def stop(self):
        self.window.pop_handlers()
        pyglet.clock.unschedule(self.update)

    def draw(self):
        self.world.draw()

    def update(self, dt):
        self.keys.update(dt)
        self.world.update(dt)
        self.world.camera.look_at = self.ship.pos
        self.t += dt


class Game(object):
    """Entry point to the game, which allows switching between game states.

    Game states implement one mechanic, so a menu screen might be a game
    state, for example.

    """
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
        self.window.push_handlers(self.on_draw)
        self.gamestate = BattleMode(self)
        self.gamestate.start()

    def on_draw(self):
        self.gamestate.draw()


def main():
    from optparse import OptionParser
    parser = OptionParser('%prog [-f]')
    parser.add_option(
        '-f', '--fullscreen',
        action='store_true',
        help='Start in full screen mode'
    )

    options, args = parser.parse_args()

    game = Game(
        windowed=not options.fullscreen
    )
    pyglet.app.run()


if __name__ == '__main__':
    main()
