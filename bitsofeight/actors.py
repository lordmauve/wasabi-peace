import math
from wasabisg.scenegraph import ModelNode

from euclid import Point3, Vector3, Quaternion, Matrix4

from .models import (
    ship_model, cannonball_model
)
from .particles import WakeEmitter
from .physics import Positionable, Sphere, Body, LineSegment


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
    GUNS = [
        (Point3(1.17, 1.44, 1.47), Vector3(15, 0.2, 0)),
        (Point3(-1.17, 1.44, 1.47), Vector3(-15, 0.2, 0)),
    ]

    SHAPES = [
        Sphere(Point3(0, 1, z), 1.3)
        for z in xrange(-3, 4, 2)
    ]

    def __init__(self, pos=Point3(0, 0, 0), angle=0):
        self.model = ModelNode(ship_model)
        self.emitters = [WakeEmitter(self)]
        self.body = Body(self, self.SHAPES)

        self.pos = pos
        self.angle = angle
        self.helm = 0
        self._next_helm = None
        self.speed = 1
        self.t = 0
        self.rot = Quaternion()

    def set_helm(self, helm):
        self._next_helm = CosineInterpolation(self.helm, helm, dur=3)

    def fire(self):
        """Fire all guns!"""
        m = self.get_matrix()
        for pos, v in self.GUNS:
            wvec = m * v
            wpos = m * pos
            self.world.spawn(Cannonball(wpos, wvec, owner=self))

    def update(self, dt):
        self.t += dt

        # interpolate over the helm input
        if self._next_helm is not None:
            self.helm = self._next_helm.get(dt)
            if self._next_helm.finished():
                self.helm = self._next_helm.tov
                self._next_helm = None

        # Compute some bobbing motion
        roll = 0.05 * math.sin(self.t) + 0.05 * self.helm
        pitch = 0.02 * math.sin(0.31 * self.t)

        # Update ship angle and position
        self.angle += self.helm * self.speed * 0.05 * dt
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
