import random
import Queue
from pyglet.event import EventDispatcher


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
        ship.helm.set(self.strength)


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
        ship.sail.set(min(3, ship.sail.target + 1))


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
