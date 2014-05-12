import random
from collections import deque
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
