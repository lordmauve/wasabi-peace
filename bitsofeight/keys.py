from pyglet.window import key

from .orders import (
    ShipOrderHelm, ShipOrderAccelerate, ShipOrderDecelerate, ShipOrderFire
)


class KeyControls(key.KeyStateHandler):
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

