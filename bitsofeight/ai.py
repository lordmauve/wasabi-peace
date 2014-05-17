import random
import math
from math import pi, degrees
from euclid import Vector2, Vector3

from .utils import map_angle

tau = 2 * pi


def in_plane(vec3):
    """Convert from 3D vectors in space to 2D vectors on the plane.

    This should be easier for AI strategy calculations.

    """
    return Vector2(vec3.x, vec3.z)


class ShipAI(object):
    def __init__(self, ship, debug=False):
        self.world = ship.world
        self.ship = ship
        self.ship.push_handlers(
            self.on_death,
            self.on_hit
        )
        self.strategy = SailCourseStrategy(self)
        self.target = None

        self.ready_to_fire = True
        self.target_point = None

        # Aggressive ships will target anything in range
        self.aggressive = random.randint(0, 1)
        self.debug = debug

    def think(self, msg, *args):
        if self.debug:
            print msg % args

    def on_death(self):
        self.stop()

    def on_hit(self, ship, pos):
        """Set this as the current target."""
        if ship.faction != self.ship.faction:
            self.set_target(ship)
            self.consider_strategy()

    @property
    def clock(self):
        return self.world.clock

    def start(self):
        self.clock.schedule_interval(self.consider_strategy, 5.0)

    def stop(self):
        self.clock.unschedule(self.consider_strategy)

    def fire(self):
        if self.ready_to_fire:
            self.ship.fire()
            self.clock.schedule_once(self.reset_firing, 1.0)
            self.ready_to_fire = False

    def reset_firing(self, dt):
        self.ready_to_fire = True

    def change_strategy(self, strategy_class, *args, **kwargs):
        """Change to the given strategy class

        Any other will be passed to the strategy class.

        """
        self.think("Setting strategy to %s" % strategy_class.__name__)
        self.strategy.stop()
        self.strategy = strategy_class(self, *args, **kwargs)
        self.strategy.start()

    def have_shot(self, target):
        """Return True if we have a possible shot"""
        return abs(self.ship.get_forward().dot(target.pos - self.ship.pos)) < 6.0

    def is_aligned(self, target):
        """Return true if we're sailing in the same direction as target."""
        return self.ship.forward().dot(target.forward()) > 0.7

    def is_crossing(self, target):
        """Return True if we're sailing in the opposite direction to target."""
        return self.ship.forward().dot(target.forward()) < -0.7

    def relative_bearing(self, pos):
        """Get the angle of pos to the current heading. +ve is to port."""
        return self.absolute_bearing(pos) - self.ship.angle

    def is_beam_on(self, pos):
        """Return True if the given point is towards either beam."""
        return abs(self.ship.starboard().dot(pos - self.ship.pos)) > 0.7

    def absolute_bearing(self, pos):
        """Get the bearing of pos."""
        x, z = in_plane(pos) - in_plane(self.ship.pos)
        return math.atan2(x, z)

    def dist_to(self, pos):
        t = pos - self.ship.pos
        return t.magnitude()

    def dist_to_target(self, target):
        return self.dist_to(target.pos)

    def set_target(self, t):
        self.clear_target()
        self.target = t
        self.target.push_handlers(
            on_death=self.on_target_death
        )

    def clear_target(self):
        if not self.target:
            return
        self.target.remove_handlers(
            on_death=self.on_target_death
        )
        self.target = None

    def on_target_death(self):
        self.clear_target()
        self.consider_strategy()

    def pick_target(self):
        """Pick and return a promising target."""
        for lookahead, range in [(15, 30), (70, 70)]:
            targets = [
                t
                for side in self.ship.get_targets(lookahead, range).values()
                for t in side
                if t.faction != self.ship.faction
            ]
            if targets:
                self.set_target(random.choice(targets))
                return

    def consider_strategy(self, *args):
        """Consider a different strategy."""
        if self.aggressive:
            self.pick_target()
        if self.target:
            t = self.target.pos - self.ship.pos
            dist = t.magnitude()
            if dist < 20:
                return self.change_strategy(TurnForGuns)
            else:
                return self.change_strategy(SailTowards)

        self.change_strategy(SailCourseStrategy)

    def set_helm(self, helm):
        self.think("Steering %s", helm)
        self.ship.helm.set(helm)

    def steer_to_bearing(self, bearing):
        wind_angle = self.ship.world.wind_angle
        rel_wind_angle = map_angle(wind_angle - bearing)
        if -0.35 < rel_wind_angle < 0.35:
            # Sailing upwind!
            if rel_wind_angle > 0:
                bearing = wind_angle - 0.35
            else:
                bearing = wind_angle + 0.35

        self.think("Target bearing %d, my course is %d", degrees(bearing), degrees(self.ship.angle))
        rel = map_angle(bearing - self.ship.angle)
        if -0.1 < rel < 0.1:
            self.set_helm(0)
            return
        mag = abs(rel)
        sign = 1 if rel > 0 else -1

        if mag < 0.5:
            self.set_helm(sign * 1)
        elif mag < 1.5:
            self.set_helm(sign * 2)
        else:
            self.set_helm(sign * 3)

    def __del__(self):
        self.stop()


class Strategy(object):
    INTERVAL = 0.5  # interval between updates.

    def __init__(self, ai):
        self.ai = ai

    @property
    def ship(self):
        return self.ai.ship

    def start(self):
        self.ai.clock.schedule_interval(self.update_base, self.INTERVAL)

    def stop(self):
        self.ai.clock.unschedule(self.update_base)

    def update_base(self, dt):
        try:
            self.update(dt)
        except Exception:
            import traceback
            traceback.print_exc()

    def update(self, dt):
        """Strategies must implement this."""


class TurnForGuns(Strategy):
    """Turn the guns towards the target and take a shot."""
    INTERVAL = 0.1

    def update(self, dt):
        if not self.ai.target:
            self.ai.consider_strategy()
            return
        if self.ai.dist_to_target(self.ai.target) > 30:
            return self.ai.consider_strategy()

        ab = self.ai.absolute_bearing(self.ai.target.pos)
        rel = self.ai.relative_bearing(self.ai.target.pos)
        if rel > 0:
            self.ai.steer_to_bearing(ab - pi * 0.5)
        else:
            self.ai.steer_to_bearing(ab + pi * 0.5)
        if self.ai.have_shot(self.ai.target):
            self.ai.fire()


class SailCourseStrategy(Strategy):
    """Null strategy - sail in the same direction forever."""
    def update(self, dt):
        pass

    def start(self):
        self.ship.pos + self.ship.get_forward() * random.uniform(200.0, 600.0)

    def stop(self):
        pass


class SailToTarget(Strategy):
    INTERVAL = 1.0

    def get_target(self):
        """Subclasses must implement this."""

    def update(self, dt):
        t = self.get_target()

        self.ai.think("Target is %r, I'm at %r", t, self.ai.ship.pos)
        bearing = self.ai.absolute_bearing(t)
        self.ai.steer_to_bearing(bearing)

        dist = self.ai.dist_to(t)
        if dist < 15:
            self.ship.sail.set(1)
        elif dist < 30:
            self.ship.sail.set(2)
        else:
            self.ship.sail.set(3)


class SailToPoint(SailToTarget):
    """Sail to a fixed point."""
    def start(self):
        if not self.ship.target_point:
            self.ship.target_point = (
                self.ship.pos +
                Vector3(
                    random.uniform(200.0, 600.0),
                    0.0,
                    random.uniform(200.0, 600.0)
                )
            )
        super(SailToPoint, self).start()

    def get_target(self):
        return self.ai.target_point


class SailTowards(SailToTarget):
    """Sail towards the target."""
    def get_target(self):
        return self.ai.target.pos

    def update(self, dt):
        t = self.get_target()
        if self.ai.dist_to(t) < 20:
            self.ai.change_strategy(TurnForGuns)
        else:
            super(SailTowards, self).update(dt)
