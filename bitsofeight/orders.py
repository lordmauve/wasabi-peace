import random
import Queue
from pyglet.event import EventDispatcher
from pyglet.resource import media
from pyglet.media import MediaException


class ShipOrderHelm(object):
    messages = [
        u'Rudder amidships!',
        u'A little to {self.direction}!',
        u'Turn to {self.direction}!',
        u'Hard ta {self.direction}!'
    ]

    SOUNDS = {
        'centre': media('rudder_amidships.wav', streaming=False),
        'port': [
            media('a_little_to_port.wav', streaming=False),
            media('turn_to_port.wav', streaming=False),
            media('hard_to_port.wav', streaming=False),
        ],
        'starboard': [
            media('a_little_to_starboard.wav', streaming=False),
            media('turn_to_starboard.wav', streaming=False),
            media('hard_to_starboard.wav', streaming=False),
        ],
    }

    def __init__(self, direction, strength):
        assert direction in ('port', 'starboard')
        assert 0 <= strength <= 3
        self.direction = direction
        self.strength = -strength if direction == 'starboard' else strength

    def get_message(self, ship):
        return self.messages[abs(self.strength)].format(self=self)

    def act(self, ship):
        if self.strength == 0:
            sound = self.SOUNDS['centre']
        else:
            sound = self.SOUNDS[self.direction][abs(self.strength) - 1]
        try:
            sound.play()
        except MediaException:
            pass
        ship.helm.set(self.strength)


class ShipOrderAccelerate(object):
    messages = [
        u'',
        u'A touch more sail!',
        u'More sail!',
        u'Give me every scrap of sail!',
    ]

    SOUND = media('more_sail.wav', streaming=False)

    def __init__(self, strength):
        assert 0 <= strength <= 3
        self.strength = strength

    def get_message(self, ship):
        return self.messages[self.strength].format(self=self)

    def act(self, ship):
        try:
            self.SOUND.play()
        except MediaException:
            pass
        ship.sail.set(min(3, ship.sail.target + 1))


class ShipOrderFire(object):
    messages = [
        u"Let 'em have it!",
        u"Fire!",
        u"Give 'em a full broadside!",
    ]

    SOUNDS = [
        media('let_em_have_it.wav', streaming=False),
        media('fire.wav', streaming=False),
        media('give_em_full_broadside.wav', streaming=False),
    ]

    def __init__(self):
        self.message, self.sound = random.choice(zip(self.messages, self.SOUNDS))

    def get_message(self, ship):
        return self.message

    def act(self, ship):
        try:
            self.sound.play()
        except MediaException:
            pass
        ship.fire()


class ShipOrderDecelerate(ShipOrderAccelerate):
    messages = [
        u'',
        u"Ease off the mails'l!",
        u"Ease off all sail!",
        u"All stop!"
    ]

    SOUND = media('ease_off_the_mainsl.wav', streaming=False)

    def act(self, ship):
        try:
            self.SOUND.play()
        except MediaException:
            pass
        ship.sail.set(max(0, ship.sail.target - 1))


class OrdersQueue(EventDispatcher):
    """Handle queueing of orders and applying them at intervals.

    Some orders may be contradictory; this class should sort them out.

    """
    INTERVAL = 0.5

    def __init__(self, ship):
        self.queue = Queue.Queue()
        self.ship = ship
        self.wait = 0

    def put(self, order):
        # TODO: work out how this order might supercede other orders
        # already in the queue.
        self.queue.put(order)

    def update(self, dt):
        if self.wait > 0:
            self.wait -= dt
            if self.wait <= 0:
                self.dispatch_event('on_ready_for_orders')
        elif self.queue:
            try:
                o = self.queue.get_nowait()
                self.dispatch_event('on_order', o)
                o.act(self.ship)
                self.wait = self.INTERVAL
            except Queue.Empty:
                pass

OrdersQueue.register_event_type('on_order')
OrdersQueue.register_event_type('on_ready_for_orders')


class OrderProcessor(object):
    """Process events from Web interface, and turn them into orders."""
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

    def turn_left(self):
        return ShipOrderHelm('port', 2)

    def hard_left(self):
        return ShipOrderHelm('port', 3)

    def turn_right(self):
        return ShipOrderHelm('starboard', 2)

    def hard_right(self):
        return ShipOrderHelm('starboard', 3)

    def centre(self):
        return ShipOrderHelm('starboard', 0)

    def speed_up(self):
        return ShipOrderAccelerate(1)

    def slow_down(self):
        return ShipOrderDecelerate(1)

    def fire(self):
        return ShipOrderFire()
