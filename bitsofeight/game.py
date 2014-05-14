import os.path
import pyglet
import random
import math
from pyglet.event import EventDispatcher

from euclid import Point3, Vector3

from wasabisg.scenegraph import Camera, Scene, ModelNode
from wasabisg.lighting import Sunlight, Light


# Configure loader before importing any game assets
pyglet.resource.path += [os.path.join('assets', d) for d in [
    'sounds',
    'textures',
    'sprites',
    'fonts'
]]
pyglet.resource.reindex()
pyglet.resource.add_font('benegraphic.ttf')

# Import other modules here
from .sound import Music, Sound
from .hud import HUD
from .models import (
    skydome, sea_model
)
from .orders import OrdersQueue
from .keys import KeyControls
from .actors import Ship
from .particles import particles


WIDTH = 1024
HEIGHT = 600

FPS = 60


class World(EventDispatcher):
    def __init__(self):
        self.objects = []
        self.emitters = []

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
        if hasattr(obj, 'emitters'):
            for e in obj.emitters:
                self.emitters.append(e)
                e.start()
        obj.world = self

    def destroy(self, obj):
        self.objects.remove(obj)

        try:
            model = obj.model
        except AttributeError:
            pass
        else:
            self.scene.remove(model)
        if hasattr(obj, 'emitters'):
            for e in obj.emitters:
                e.stop()
            self.emitters = [o for o in self.emitters if o not in obj.emitters]

        obj.world = None

    def update(self, dt):
        """Update the world through the given time step (in seconds)."""
        for e in self.emitters:
            e.update()
        particles.update(dt)
        for o in self.objects:
            o.update(dt)

    def create_scene(self):
        """Initialise the scene with static objects."""
        self.scene = Scene(
            ambient=(0.2, 0.2, 0.2, 1.0),
        )

        # Add the particle system
        self.scene.add(particles)

        # Sun
        self.scene.add(Sunlight(
            direction=Vector3(0.82, 0.31, 0.48),
            colour=(1.0, 0.8, 0.5, 1.0),
            intensity=1,
        ))

        # Sky dome
        self.skydome = ModelNode(skydome)
        self.scene.add(self.skydome)

        # Sea
        self.sea = ModelNode(sea_model)
        self.scene.add(self.sea)

    def spawn_ships(self):
        tau = 2 * math.pi
        for i in range(5):
            bearing = random.uniform(0, tau)
            rng = random.uniform(50, 100)
            x = rng * math.sin(bearing)
            z = rng * math.cos(bearing)

            angle = random.uniform(0, tau)
            s = Ship(
                pos=Point3(x, 0, z),
                angle=angle
            )
            self.spawn(s)

    def draw(self):
        x, _, z = self.camera.pos
        self.skydome.pos = Point3(x, 0, z)
        self.sea.pos = Point3(x, 0, z)
        self.scene.render(self.camera)


class ChaseCamera(object):
    def __init__(self, camera, ship):
        self.camera = camera
        self.ship = ship

    def update(self, dt):
        self.camera.look_at = self.ship.pos
        m = self.ship.get_matrix()
        self.camera.pos = m * Point3(0, 6, -16)


class SideCamera(ChaseCamera):
    def update(self, dt):
        self.camera.look_at = self.ship.pos + Vector3(0, 3, 0)
        m = self.ship.get_matrix()
        self.camera.pos = m * Point3(8, 3, 0)


class IsometricCamera(object):
    def __init__(self, camera, ship):
        self.camera = camera
        self.ship = ship

    def update(self, dt):
        self.camera.look_at = self.ship.pos
        self.camera.pos = self.ship.pos +  Vector3(10, 5, 10)


class BattleMode(object):
    """Sailing on the open ocean!"""
    def __init__(self, game):
        self.game = game
        self.window = game.window
        self.world = World()

        self.ship = Ship()
        self.ship.speed = 0
        self.world.spawn(self.ship)
        self.orders_queue = OrdersQueue(self.ship)
        self.orders_queue.push_handlers(self.on_order)
        self.scroll = 0
        self.keys = KeyControls(self.orders_queue)

        self.camera_controller = ChaseCamera(self.world.camera, self.ship)

        self.hud = HUD()

	self.t = 0
        self.music = Music(['battletrack.mp3'])
        self.sounds = Sound(['cannon1.mp3', 'cannon2.mp3'])

    def on_order(self, o):
        if self.scroll:
            self.hud.remove_scroll(self.scroll)
            pyglet.clock.unschedule(self.clear_order)
        self.scroll = self.hud.create_scroll(o.get_message(self.ship), (25, 10))
        pyglet.clock.schedule_once(self.clear_order, 2.0)

    def clear_order(self, *args):
        if self.scroll:
            self.scroll.delete()
            self.scroll = None

    def start(self):
        pyglet.clock.schedule_interval(self.update, 1.0 / FPS)

        self.keys.push_handlers(self.window)
        #self.sounds.sound_on_event('cannon2.mp3', self.window, 'on_mouse_press')
        self.world.spawn_ships()
        self.music.play()

    def stop(self):
        self.window.pop_handlers()
        pyglet.clock.unschedule(self.update)

    def draw(self):
        self.world.draw()
        self.hud.draw()

    def update(self, dt):
        self.keys.update(dt)
        self.orders_queue.update(dt)
        self.world.update(dt)
        self.camera_controller.update(dt)
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
            self.window = pyglet.window.Window(
                fullscreen=True
            )
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
    parser.add_option(
        '-p', '--profile',
        action='store_true',
        help='Run with profiler'
    )

    options, args = parser.parse_args()

    game = Game(
        windowed=not options.fullscreen
    )

    if options.profile:
        import cProfile
        pr = cProfile.Profile()
        pr.runcall(pyglet.app.run)
        pr.print_stats('cumulative')
    else:
        pyglet.app.run()


if __name__ == '__main__':
    main()
