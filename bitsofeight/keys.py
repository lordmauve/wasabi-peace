from pyglet.window import key

from .orders import OrderProcessor


class KeyControls(key.KeyStateHandler):
    """Process events from keys, and turn them into orders."""

    def __init__(self, order_queue):
        self.order_processor = OrderProcessor()
        self.bindings = {
            key.A: self.order_processor.turn_left,
            key.D: self.order_processor.turn_right,
            key.W: self.order_processor.speed_up,
            key.S: self.order_processor.slow_down,
            key.SPACE: self.order_processor.fire
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
                    o = func(self.t - v)
                    self.orders_queue.put(o)
                    del self.key_timer[key]

    def push_handlers(self, window):
        window.push_handlers(self)

