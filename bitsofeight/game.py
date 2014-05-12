import time
import math
from collections import deque
import random

import pyglet
from pyglet.window import key
from pyglet.event import EventDispatcher, EVENT_HANDLED

from euclid import Point3, Vector3, Quaternion, Matrix4

from wasabisg.scenegraph import Camera, Scene, v3, ModelNode
from wasabisg.lighting import Sunlight

# Configure loader before importing any game assets
pyglet.resource.path += [
    'assets/sounds/',
    'assets/textures/',
    'assets/sprites/',
    'assets/fonts/'
]
pyglet.resource.reindex()
pyglet.resource.add_font('benegraphic.ttf')

# Import other modules here
from .sound import Music, Sound
from .hud import HUD
from .models import (
    ship_model, skydome, cannonball_model, sea_model
)

WIDTH = 1024
HEIGHT = 600

FPS = 60


class Interpolation(object):
    def __init__(self, fromv, tov, dur=1.0):
        self.fromv = fromv
        self.delta = tov - fromv
        self.dur = float(dur)
        self.t = 0

    def get(self, dt):
        self.t = min(self.t + dt / self.dur, 1)
        v = self.fromv + self.interpolate(self.t) * self.delta
        return v

    def finished(self):
        return self.t == 1


class LinearInterpolation(Interpolation):
    def interpolate(self, t):
        return t


class CosineInterpolation(Interpolation):
    hpi = math.pi * 0.5
    sin = math.sin  # Don't know why it's called cosine interpolation, sin^2
                    # is easier

    def interpolate(self, t):
        sin = self.sin(t / self.hpi)
        return sin * sin


class Cannonball(object):
    GRAVITY = Vector3(0, -1.0, 0)

    def __init__(self, pos, v):
        self.model = ModelNode(cannonball_model)
        self.pos = pos
        self.v = v

    def update(self, dt):
        u = self.v
        self.v += self.GRAVITY * dt
        self.pos += 0.5 * (u + self.v) * dt

        if self.pos.y < 0:
            self.world.destroy(self)
        else:
            self.model.pos = self.pos


class Ship(object):
    # Y up, -z forward
    GUNS = [
        (Point3(1.17, 1.44, 1.47), Vector3(15, 0.2, 0)),
        (Point3(-1.17, 1.44, 1.47), Vector3(-15, 0.2, 0)),
    ]

    def __init__(self):
        self.model = ModelNode(ship_model)

        self.pos = Point3(0, 0, 0)
        self.angle = 0
        self.helm = 0
        self._next_helm = None
        self.speed = 1
        self.t = 0
        self.rot = Quaternion()

    def set_helm(self, helm):
        self._next_helm = CosineInterpolation(self.helm, helm, dur=2)

    def local_to_world(self, v):
        return self.rot * v + self.pos

    def get_matrix(self):
        r = self.rot.get_matrix()
        t = Matrix4.new_translate(*self.pos)
        return t * r

    def fire(self):
        m = self.get_matrix()
        for pos, v in self.GUNS:
            wvec = m * v
            wpos = m * pos
            self.world.spawn(Cannonball(wpos, wvec))

    def update(self, dt):
        self.t += dt

        # interpolate over the helm input
        if self._next_helm:
            self.helm = self._next_helm.get(dt)
            if self._next_helm.finished():
                self._next_helm = None

        # Compute some bobbing motion
        roll = 0.05 * math.sin(self.t) + 0.2 * self.helm
        pitch = 0.02 * math.sin(0.31 * self.t)

        # Update ship angle and position
        self.angle += self.helm * self.speed * 0.2 * dt
        q = Quaternion.new_rotate_axis(self.angle, Vector3(0, 1, 0))
        v = q * Vector3(0, 0, 1) * self.speed * dt
        self.pos += v

        # Apply ship angle and position to model
        self.rot = (
            q *
            Quaternion.new_rotate_axis(pitch, Vector3(1, 0, 0)) *
            Quaternion.new_rotate_axis(roll, Vector3(0, 0, 1))
        )
        rotangle, (rotx, roty, rotz) = self.rot.get_angle_axis()
        self.model.rotation = (math.degrees(rotangle), rotx, roty, rotz)
        self.model.pos = self.pos


class ShipOrderHelm(object):
    messages = [
        u'Rudder amidships!',
        u'A little to {self.direction}!',
        u'Turn to {self.direction}!',
        u'Hard ta {self.direction}!'
    ]

    def __init__(self, direction, strength):
        assert direction in ('port', 'starboard')
        assert 0 <= strength <= 3
        self.direction = direction
        self.strength = -strength if direction == 'starboard' else strength

    def get_message(self, ship):
        return self.messages[abs(self.strength)].format(self=self)

    def act(self, ship):
        ship.set_helm(self.strength)


class ShipOrderAccelerate(object):
    messages = [
        u'',
        u'A touch more sail!',
        u'More sail!',
        u'Give me every scrap of sail!',
    ]

    def __init__(self, strength):
        assert 0 <= strength <= 3
        self.strength = strength

    def get_message(self, ship):
        return self.messages[self.strength].format(self=self)

    def act(self, ship):
        ship.speed = min(3, ship.speed + 1)


class ShipOrderFire(object):
    messages = [
        u"Let 'em have it!",
        u"Fire!",
        u"Give 'em a full broadside!",
    ]

    def __init__(self):
        self.message = random.choice(self.messages)

    def get_message(self, ship):
        return self.message

    def act(self, ship):
        ship.fire()


class ShipOrderDecelerate(ShipOrderAccelerate):
    messages = [
        u'',
        u"Ease off the mails'l!",
        u"Ease off all sail!",
        u"All stop!"
    ]

    def act(self, ship):
        ship.speed = max(0, ship.speed - 1)


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
        obj.world = self

    def destroy(self, obj):
        self.objects.remove(obj)

        try:
            model = obj.model
        except AttributeError:
            pass
        else:
            self.scene.remove(model)

        obj.world = None

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
        self.sea = ModelNode(sea_model)
        self.scene.add(self.sea)

    def draw(self):
        x, _, z = self.camera.pos
        self.skydome.pos = Point3(x, 0, z)
        self.sea.pos = Point3(x, 0, z)
        self.scene.render(self.camera)


class KeyControls(pyglet.window.key.KeyStateHandler):
    """Process events from keys, and turn them into orders."""
    # Maximum Key press durations for different strength actions
    LIGHT = 0.2
    MEDIUM = 0.5

    def get_strength(self, held):
        if held < self.LIGHT:
            return 1
        elif held < self.MEDIUM:
            return 2
        else:
            return 3

    def turn_left(self, held):
        self.orders_queue.put(
            ShipOrderHelm('port', self.get_strength(held))
        )

    def turn_right(self, held):
        self.orders_queue.put(
            ShipOrderHelm('starboard', self.get_strength(held))
        )

    def speed_up(self, held):
        s = self.get_strength(held)
        if s == 1:
            o = ShipOrderHelm('port', 0)
        else:
            o = ShipOrderAccelerate(s - 1)
        self.orders_queue.put(o)

    def slow_down(self, held):
        s = self.get_strength(held)
        if s == 1:
            o = ShipOrderHelm('port', 0)
        else:
            o = ShipOrderDecelerate(s - 1)
        self.orders_queue.put(o)

    def fire(self, held):
        self.orders_queue.put(ShipOrderFire())

    def __init__(self, order_queue):
        self.bindings = {
            key.A: self.turn_left,
            key.D: self.turn_right,
            key.W: self.speed_up,
            key.S: self.slow_down,
            key.SPACE: self.fire
        }
        self.key_timer = {}
        self.t = 0
        self.orders_queue = order_queue

    def update(self, dt):
        # Would like to do this with on_press/on_release events, but they both
        # appear to fire repeatedly, so we can't.
        self.t += dt
        for key, func in self.bindings.items():
            if self[key]:
                if key not in self.key_timer:
                    self.key_timer[key] = self.t
            else:
                v = self.key_timer.get(key)
                if v is not None:
                    func(self.t - v)
                    del self.key_timer[key]

    def push_handlers(self, window):
        window.push_handlers(self)


class OrdersQueue(EventDispatcher):
    """Handle queueing of orders and applying them at intervals.

    Some orders may be contradictory; this class should sort them out.

    """
    INTERVAL = 2

    def __init__(self, ship):
        self.queue = deque()
        self.ship = ship
        self.wait = 0

    def put(self, order):
        # TODO: work out how this order might supercede other orders
        # already in the queue.
        self.queue.append(order)

    def update(self, dt):
        if self.wait > 0:
            self.wait -= dt
            if self.wait <= 0:
                self.dispatch_event('on_ready_for_orders')
        elif self.queue:
            o = self.queue.popleft()
            self.dispatch_event('on_order', o)
            o.act(self.ship)
            self.wait = self.INTERVAL

OrdersQueue.register_event_type('on_order')
OrdersQueue.register_event_type('on_ready_for_orders')


class BattleMode(object):
    """Sailing on the open ocean!"""
    def __init__(self, game):
        self.game = game
        self.window = game.window
        self.world = World()

        self.ship = Ship()
        self.world.spawn(self.ship)
        self.orders_queue = OrdersQueue(self.ship)
        self.orders_queue.push_handlers(self.on_order)
        self.scroll = 0
        self.keys = KeyControls(self.orders_queue)

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

    def stop(self):
        self.window.pop_handlers()
        pyglet.clock.unschedule(self.update)

    def draw(self):
        from pyglet import gl
        flags = gl.GL_ALL_ATTRIB_BITS
        gl.glPushAttrib(flags)
        self.world.draw()
        gl.glPopAttrib()
        self.hud.draw()

    def update(self, dt):
        self.keys.update(dt)
        self.orders_queue.update(dt)
        self.world.update(dt)
        self.world.camera.look_at = self.ship.pos
        self.world.camera.pos = self.ship.pos + Vector3(10, 5, 10)
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
