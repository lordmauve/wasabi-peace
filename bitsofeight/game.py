import os.path
import pyglet
import random
import math
import threading
from pyglet.event import EventDispatcher

from euclid import Point3, Vector3
import posixpath

from wasabisg.scenegraph import Camera, Scene, ModelNode
from wasabisg.lighting import Sunlight, Light
from Queue import Queue, Empty


# Configure loader before importing any game assets
pyglet.resource.path += [posixpath.join('assets', d) for d in [
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
from .physics import Physics
from .sea import sea_shader, SeaNode
from .ai import ShipAI
from .server import serve, send_msg

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 9000

WIDTH = 1024
HEIGHT = 600

FPS = 60

tau = 2 * math.pi


class World(EventDispatcher):
    def __init__(self):
        self.objects = []
        self.emitters = []
        self.physics = Physics()
        self.wind_angle = 0.0

        self.create_scene()
        self.camera = Camera(
            pos=Point3(10, 5, 10),
            look_at=Point3(0, 1, 0),
            width=WIDTH,
            height=HEIGHT
        )
        self.t = 0.0
        self.clock = pyglet.clock.Clock(time_function=self.time)

    def time(self):
        return self.t

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
        if hasattr(obj, 'body'):
            self.physics.add(obj.body)
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
        if hasattr(obj, 'body'):
            self.physics.remove(obj.body)

        obj.world = None

    def update(self, dt):
        """Update the world through the given time step (in seconds)."""
        self.t += dt
        self.clock.tick()
        pyglet.media.listener.position = self.camera.pos
        pyglet.media.listener.forward_orientation = self.camera.eye_vector()

        for e in self.emitters:
            e.update()
        particles.update(dt)
        for o in self.objects:
            o.update(dt)
        self.physics.do_collisions()

    def create_scene(self):
        """Initialise the scene with static objects."""
        self.scene = Scene(
            ambient=(0.2, 0.2, 0.2, 1.0),
        )

        for m in Ship.MODELS:
            self.scene.prepare_model(m)

        # Add the particle system
        self.scene.add(particles)

        # Sun
        self.scene.add(Sunlight(
            direction=Vector3(0.82, 0.31, 0.48),
            colour=(1.0, 0.85, 0.6, 1.0),
            intensity=1,
        ))

        # Sky dome
        self.skydome = ModelNode(skydome, rotation=(59, 0, 1, 0))
        self.scene.add(self.skydome)

        # Sea
        self.sea = SeaNode(sea_model)
        self.sea.shader = sea_shader
        self.scene.add(self.sea)

    def spawn_ships(self):
        for i in range(5):
            self.spawn_one_ship()

    def spawn_one_ship(self):
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
        ShipAI(s).start()

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
        self.camera.look_at = self.ship.pos + Vector3(0, 2, 0)
        m = self.ship.get_matrix()
        if self.ship.alive:
            self.camera.pos = m * Point3(0, 6, -14)


class SideCamera(ChaseCamera):
    def update(self, dt):
        self.camera.look_at = self.ship.pos + Vector3(0, 3, 0)
        m = self.ship.get_matrix()
        if self.ship.alive:
            self.camera.pos = m * Point3(8, 3, 0)


class IsometricCamera(object):
    def __init__(self, camera, ship):
        self.camera = camera
        self.ship = ship

    def update(self, dt):
        self.camera.look_at = self.ship.pos
        self.camera.pos = self.ship.pos +  Vector3(10, 5, 10)


class OverheadCamera(object):
    """Overhead camera. Useful for AI testing."""
    def __init__(self, camera, ship):
        self.camera = camera
        self.ship = ship

    def update(self, dt):
        self.camera.look_at = self.ship.pos
        self.camera.pos = self.ship.pos +  Vector3(0, 80, 5)


class BattleMode(object):
    """Sailing on the open ocean!"""
    def __init__(self, game):
        self.game = game
        self.window = game.window
        self.world = World()

        self.ship = Ship(max_health=5)
        self.ship.faction = 0
        self.world.spawn(self.ship)
        self.ship.push_handlers(
            self.on_kill
        )

        # Uncomment this to give the player ship AI, eg for testing
        # ShipAI(self.ship, debug=True).start()

        self.system_queue = Queue()
        self.orders_queue = OrdersQueue(self.ship)
        self.orders_queue.push_handlers(self.on_order)
        self.scroll = 0
        #self.keys = KeyControls(self.orders_queue)

        self.camera_controller = ChaseCamera(self.world.camera, self.ship)
        #self.camera_controller = OverheadCamera(self.world.camera, self.ship)

        self.hud = HUD(WIDTH, HEIGHT)

        self.t = 0
        self.music = Music(['battletrack.mp3'])
        self.sounds = Sound(['cannon1.mp3', 'cannon2.mp3'])

        self.connect_message = None
        self.started = False
        self.on_disconnect()

        pyglet.clock.schedule_interval(self.send_data, 0.05)

    def send_data(self, dt):
        if self.ship.world:
            send_msg(math.degrees(self.ship.get_wind_angle()))

    KILL_SOUNDS = [
        pyglet.resource.media('get_back_to_shore_you_landlubber.wav', streaming=False),
        pyglet.resource.media('pass_me_greetings_to_davy_jones.wav', streaming=False),
    ]

    def on_kill(self, *args):
        sound = random.choice(self.KILL_SOUNDS)
        sound.play()
        self.hud.add_booty(100)
        self.world.spawn_one_ship()

    def on_order(self, o):
        if self.scroll:
            self.clear_order()
            pyglet.clock.unschedule(self.clear_order)
        self.scroll = (
            self.hud.create_scroll(o.get_message(self.ship), 130, 30),
            self.hud.create_sprite('captain', 10, 10)
        )
        pyglet.clock.schedule_once(self.clear_order, 2.0)

    def clear_order(self, *args):
        if self.scroll:
            scroll, sprite = self.scroll
            scroll.delete()
            sprite.delete()
            self.scroll = None

    def start(self):
        pyglet.clock.schedule_interval(self.update, 1.0 / FPS)

        #self.keys.push_handlers(self.window)
        self.world.spawn_ships()
        self.music.play()

    def stop(self):
        self.window.pop_handlers()
        pyglet.clock.unschedule(self.update)

    def draw(self):
        self.world.draw()
        self.hud.draw()

    def on_disconnect(self):
        if not self.connect_message:
            msg = "Please connect to http://%s:%d/ with a browser or smartphone" % (
                get_ip_address(), SERVER_PORT
            )
            self.connect_message = (
                self.hud.create_sprite('logo', 10, HEIGHT - 287),
                self.hud.create_scroll(msg, 145, 100),
            )
        self.started = False

    def on_connect(self):
        if self.started:
            return
        if self.connect_message:
            sprite, scroll = self.connect_message
            sprite.delete()
            scroll.delete()
        self.connect_message = None
        self.started = True

    def update(self, dt):
        #self.keys.update(dt)
        try:
            msg = self.system_queue.get_nowait()
        except Empty:
            pass
        else:
            if msg == 'connected':
                self.on_connect()
            elif msg == 'disconnected':
                self.on_disconnect()

        if self.started:
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


ipaddr = None

def get_ip_address():
    global ipaddr
    import socket
    if not ipaddr:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ipaddr = s.getsockname()[0]
        s.close()
    return ipaddr


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
        # start the command websockets server in the background
        com_thread = threading.Thread(target=serve,
                                      args=(SERVER_HOST, SERVER_PORT, game.gamestate.orders_queue, game.gamestate.system_queue)
                                      )
        com_thread.daemon = True
        com_thread.start()

        print "Please connect to http://%s:%d/ with a mobile browser (or desktop browser) for the controls" % (
            get_ip_address(), SERVER_PORT
        )

        pyglet.app.run()


if __name__ == '__main__':
    main()
