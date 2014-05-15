import math
from math import pow, sin, cos
from wasabisg.scenegraph import ModelNode, GroupNode
from wasabisg.model import Material, Model, Mesh
from wasabisg.sphere import Sphere as SphereMesh

from euclid import Point3, Vector3, Quaternion, Matrix4

from .models import (
    hull_model, foremast_model, mainmast_model, mizzenmast_model,
    cannonball_model
)
from .physics import Positionable, Sphere, Body, LineSegment
from .particles import WakeEmitter
from .sailing import get_sail_power, get_heeling_moment, get_sail_setting


class Interpolation(object):
    def __init__(self, fromv, tov, dur=1.0):
        self.fromv = fromv
        self.tov = tov
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
        sin = self.sin(t * self.hpi)
        return sin * sin


class InterpolatingController(object):
    interpolater = CosineInterpolation

    def __init__(self, v, response_time=1.0):
        self.current = v
        self.response_time = 1.0
        self.interpolation = None

    def set(self, v):
        self.interpolation = self.interpolater(self.current, v, self.response_time)

    @property
    def target(self):
        return self.interpolation.tov if self.interpolation else self.current

    def update(self, dt):
        if self.interpolation is not None:
            self.current = self.interpolation.get(dt)
            if self.interpolation.finished():
                self.current = self.interpolation.tov
                self.interpolation = None


class Cannonball(object):
    GRAVITY = Vector3(0, -1.0, 0)

    def __init__(self, pos, v, owner):
        self.model = ModelNode(cannonball_model)
        self.pos = self.lastpos = pos
        self.v = v
        self.owner = owner

    def update(self, dt):
        u = self.v
        self.v += self.GRAVITY * dt
        s = 0.5 * (u + self.v) * dt

        line = LineSegment(self.pos, s)
        for o in self.world.objects:
            if not isinstance(o, Ship) or o is self.owner:
                continue
            hit = line.collide_body(o.body)
            if hit:
                print "Hit at", hit
                self.world.destroy(self)
                return

        self.pos += s

        if self.pos.y < 0:
            self.world.destroy(self)
        else:
            self.model.pos = self.pos


class Ship(Positionable):
    # Y up, -z forward
    GUNS = {
        'port': [
            (Point3(1.17, 1.44, 1.47), Vector3(15, 0.2, 0)),
            (Point3(1.17, 1.44, 0), Vector3(15, 0.2, 0)),
        ],
        'starboard': [
            (Point3(-1.17, 1.44, 1.47), Vector3(-15, 0.2, 0)),
            (Point3(-1.17, 1.44, 0), Vector3(-15, 0.2, 0)),
        ],
    }

    SHAPES = [
        Sphere(Point3(0, 1, z), 1.3)
        for z in xrange(-3, 4)
    ]

    WIND = Vector3(1, 0, 0)

    def __init__(self, pos=Point3(0, 0, 0), angle=0):
        super(Ship, self).__init__(pos)
        self.model = GroupNode([
            ModelNode(hull_model),
            ModelNode(foremast_model, pos=Point3(0, 1.18, 2.67)),
            ModelNode(mainmast_model, pos=Point3(0, 1.08, 0.61)),
            ModelNode(mizzenmast_model, pos=Point3(0, 1.18, -1.2)),
        ])
        self.emitters = [WakeEmitter(self)]
        self.body = Body(self, self.SHAPES)

        self.angle = angle
        self.helm = InterpolatingController(0)
        self.sail = InterpolatingController(1)  # amount of sail we have up
        self.roll = 0.0
        self.t = 0
        self.last_broadside = 'port'

    def get_targets(self, lookahead=10, range=30):
        """Get a dictionary of potential targets on either side.

        We look for targets that are within a distance of range units and up to
        lookahead units ahead or astern of us.

        """
        targets = {
            'port': [],
            'starboard': []
        }

        m = self.get_matrix()
        forward = m * Vector3(0, 0, -1)
        port = m * Vector3(1, 0, 0)
        range2 = range * range

        for o in self.world.objects:
            if isinstance(o, Ship) and o is not self:
                rel = o.pos - self.pos
                if abs(rel.dot(forward)) < lookahead and rel.magnitude_squared() < range2:
                    side = 'port' if rel.dot(port) > 0 else 'starboard'
                    targets[side].append(o)
        return targets

    def fire(self):
        """Fire the cannons!

        This is an automagical firing system that will work out whether either
        side has a promising target. In the case that they both do, alternate
        sides.

        """
        targets = self.get_targets()

        if bool(targets['port']) ^ bool(targets['starboard']):
            side = 'port' if targets['port'] else 'starboard'
#            print len(targets[side]), "targets to", side + " cap'n"
        else:
            side = 'port' if self.last_broadside == 'starboard' else 'starboard'
#            print "Haven't fired to", side, "for a while"

        m = self.get_matrix()
        for pos, v in self.GUNS[side]:
            wvec = m * v
            wpos = m * pos
            self.world.spawn(Cannonball(wpos, wvec, owner=self))
        self.last_broadside = side

    def update(self, dt):
        self.t += dt

        self.helm.update(dt)
        self.sail.update(dt)

        # damp roll
        self.roll *= pow(0.6, dt)

        # Compute some bobbing motion
        rollmoment = 0.05 * math.sin(self.t)
        pitch = 0.02 * math.sin(0.31 * self.t)

        # Compute the forward vector from the curent heading
        q = Quaternion.new_rotate_axis(self.angle, Vector3(0, 1, 0))
        forward = q * Vector3(0, 0, 1)

        angular_velocity = self.helm.current * min(forward.dot(self.vel), 2) * 0.02
        angle_to_wind = self.world.wind_angle - self.angle
        sail_power = get_sail_power(angle_to_wind)
        heeling_moment = get_heeling_moment(angle_to_wind)

        rollmoment += angular_velocity * 0.5  # lean over from centrifugal force of turn
        rollmoment -= heeling_moment * 0.05 * self.sail.current  # heel from wind force

        # Update ship angle and position
        self.angle += angular_velocity * dt
        accel = forward * self.sail.current * sail_power * 0.5 * dt
        self.vel += accel
        self.vel *= pow(0.7, dt)  # Drag
        self.pos += self.vel * dt + Vector3(0, -0.5, 0) * self.pos.y * dt

        self.roll += rollmoment * dt

        # Apply ship angle and position to model
        self.rot = (
            q *
            Quaternion.new_rotate_axis(pitch, Vector3(1, 0, 0)) *
            Quaternion.new_rotate_axis(self.roll, Vector3(0, 0, 1))
        )
        rotangle, (rotx, roty, rotz) = self.rot.get_angle_axis()
        self.model.rotation = (math.degrees(rotangle), rotx, roty, rotz)
        self.model.pos = self.pos

        # Adjust sail angle to wind direction
        sail_angle = get_sail_setting(angle_to_wind)
        for sail in self.model.nodes[1:]:
            sail.rotation = math.degrees(sail_angle), 0, 1, 0

