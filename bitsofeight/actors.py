import math
import random
from math import pow, sin, degrees
from pyglet.event import EventDispatcher
from pyglet.resource import media
from wasabisg.scenegraph import ModelNode, GroupNode
from wasabisg.lighting import Light

from euclid import Point3, Vector3, Quaternion

from .sound import SoundPlayer
from .models import (
    hull_model, mast_models, cannonball_model
)
from .physics import Positionable, Sphere, Body, LineSegment
from .particles import WakeEmitter, spawn_smoke, spawn_splinters
from .sailing import get_sail_power, get_heeling_moment, get_sail_setting
from .utils import map_angle


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

    def interpolate(self, t):
        s = sin(t * self.hpi)
        return s * s


class InterpolatingController(object):
    interpolater = CosineInterpolation

    def __init__(self, v, response_time=1.0):
        self.current = v
        self.response_time = 1.0
        self.interpolation = None

    def set(self, v):
        if self.interpolation and self.interpolation.tov == v:
            return
        self.interpolation = self.interpolater(self.current, v, self.response_time)

    def set_immediate(self, v):
        self.interpolation = None
        self.current = v

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
    HIT_SOUND = SoundPlayer('explode.mp3')
    SPLASH_SOUND = SoundPlayer('watersplash.mp3')

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
                self.HIT_SOUND.play(hit)
                spawn_splinters(hit, self.v)
                self.world.destroy(self)
                o.dispatch_event('on_hit', self.owner, hit)
                killed = o.damage()
                if killed:
                    self.owner.dispatch_event('on_kill', o)
                else:
                    self.owner.dispatch_event('on_enemy_hit', o, hit)
                return

        self.pos += s

        if self.pos.y < 0:
            self.world.destroy(self)
            self.SPLASH_SOUND.play(self.pos, volume=0.5)
        else:
            self.model.pos = self.pos


class MuzzleFlash(object):
    def __init__(self, pos):
        self.model = Light(
            pos,
            colour=(1, 0.6, 0.3, 1.0),
            intensity=10,
            falloff=0.5
        )
        self.age = 0

    def update(self, dt):
        self.age += dt
        if self.age > 1.0:
            self.world.destroy(self)
        self.model.intensity *= pow(0.01, dt)


class Ship(EventDispatcher, Positionable):
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

    MODELS = mast_models

    SINKING_SOUND = media('bubble1.mp3', streaming=False)
    CANNON_SOUND = media('cannon2.mp3', streaming=False)

    faction = 1

    def __init__(self, pos=Point3(0, 0, 0), angle=0, max_health=3):
        super(Ship, self).__init__(pos)
        self.model = GroupNode([
            ModelNode(hull_model),
            ModelNode(self.MODELS[0], pos=Point3(0, 1.18, 2.67)),
            ModelNode(self.MODELS[3], pos=Point3(0, 1.08, 0.61)),
            ModelNode(self.MODELS[6], pos=Point3(0, 1.18, -1.2)),
        ])
        self.emitters = [WakeEmitter(self)]
        self.body = Body(self, self.SHAPES)

        self.angle = angle
        self.helm = InterpolatingController(0)
        self.sail = InterpolatingController(2)  # amount of sail we have up
        self.roll = 0.0
        self.t = 0
        self.last_broadside = 'port'
        self.alive = True

        self.health = self.max_health = max_health

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

        # Fire one gun now, schedule the rest to fire over the next 0.5s
        guns = range(len(self.GUNS[side]))
        random.shuffle(guns)
        num = guns.pop()
        wpos = self.fire_gun(side, num)

        for num in guns:
            self.world.clock.schedule_once(
                lambda dt, num: self.fire_gun(side, num),
                random.uniform(0.0, 0.5),
                num
            )
        self.last_broadside = side
        self.world.spawn(MuzzleFlash(wpos))

    def fire_gun(self, side, num):
        pos, v = self.GUNS[side][num]
        m = self.get_matrix()
        v += Vector3(
            0.0,
            random.normalvariate(0.0, 0.2),
            random.normalvariate(0.0, 0.2)
        )
        wvec = m * v

        up = Vector3(0, 1, 0)
        wvec -= up * 0.5 * wvec.dot(up)
        wpos = m * pos
        p = self.CANNON_SOUND.play()
        p.position = wpos
        self.world.spawn(Cannonball(wpos, wvec, owner=self))
        spawn_smoke(wpos, wvec)
        return wpos

    def update_masts(self, sail):
        hull, foremast, mainmast, mizzenmast = self.model.nodes
        if sail < 0.7:
            foremast.model_instance = self.MODELS[0]
        elif sail < 2.3:
            foremast.model_instance = self.MODELS[1]
        else:
            foremast.model_instance = self.MODELS[2]

        if sail < 0.5:
            mainmast.model_instance = self.MODELS[3]
        elif sail < 1.5:
            mainmast.model_instance = self.MODELS[4]
        else:
            mainmast.model_instance = self.MODELS[5]

        if sail < 0.8:
            mizzenmast.model_instance = self.MODELS[6]
        elif sail < 2.0:
            mizzenmast.model_instance = self.MODELS[7]
        else:
            mizzenmast.model_instance = self.MODELS[8]

    def damage(self, amount=1):
        """Apply damage to this ship.

        Return True if the ship was killed as a result.

        """
        if not self.alive:
            return False
        self.health -= amount
        if self.health <= 0:
            self.kill()
            return True
        return False

    def kill(self):
        if self.alive:
            p = self.SINKING_SOUND.play()
            p.position = self.pos
            self.alive = False
            self.helm.set_immediate(0)
            self.sail.set_immediate(0)
            self.world.clock.schedule_once(
                lambda dt: self.world.destroy(self), 7.0)
            self.dispatch_event('on_death')

    def get_quaternion(self):
        """Get the Quarternion of the ship's current heading."""
        return Quaternion.new_rotate_axis(self.angle, Vector3(0, 1, 0))

    def get_forward(self):
        """Get the forward unit vector."""
        return self.get_quaternion() * Vector3(0, 0, 1)

    def get_starboard(self):
        """Get the starboard unit vector."""
        return self.get_quaternion() * Vector3(-1.0, 0, 0)

    def get_wind_angle(self):
        return map_angle(self.world.wind_angle - self.angle)

    def update(self, dt):
        self.t += dt

        if self.alive:
            self.helm.update(dt)
            self.sail.update(dt)

            self.update_masts(self.sail.current)

        # damp roll
        self.roll *= pow(0.6, dt)

        # Compute some bobbing motion
        rollmoment = 0.05 * sin(self.t)
        pitch = 0.02 * sin(0.31 * self.t)

        # Compute the forward vector from the curent heading
        q = self.get_quaternion()
        forward = q * Vector3(0, 0, 1)
        angular_velocity = self.helm.current * min(forward.dot(self.vel), 2) * 0.03
        angle_to_wind = map_angle(self.world.wind_angle - self.angle)
        sail_power = get_sail_power(angle_to_wind)
        heeling_moment = get_heeling_moment(angle_to_wind)

        rollmoment += angular_velocity * 0.5  # lean over from centrifugal force of turn
        rollmoment -= heeling_moment * 0.05 * self.sail.current  # heel from wind force

        # Update ship angle and position
        self.angle = map_angle(self.angle + angular_velocity * dt)
        accel = forward * self.sail.current * sail_power * 0.5 * dt
        self.vel += accel
        self.vel *= pow(0.7, dt)  # Drag
        self.pos += self.vel * dt

        # Float
        if self.alive:
            self.pos += Vector3(0, -0.5, 0) * self.pos.y * dt
        else:
            self.pos += Vector3(0, -1, 0) * dt

        self.roll += rollmoment * dt

        # Apply ship angle and position to model
        self.rot = (
            q *
            Quaternion.new_rotate_axis(pitch, Vector3(1, 0, 0)) *
            Quaternion.new_rotate_axis(self.roll, Vector3(0, 0, 1))
        )
        rotangle, (rotx, roty, rotz) = self.rot.get_angle_axis()
        self.model.rotation = (degrees(rotangle), rotx, roty, rotz)
        self.model.pos = self.pos

        # Adjust sail angle to wind direction
        if self.alive:
            sail_angle = get_sail_setting(angle_to_wind)
            for sail in self.model.nodes[1:]:
                sail.rotation = degrees(sail_angle), 0, 1, 0


# Triggered when this ship is killed
# Args: none
Ship.register_event_type('on_death')

# Triggered when this ship is shot by an enemy
# Args: attacking ship, hit position
Ship.register_event_type('on_hit')

# Triggered when this ship has shot an enemy
# Args: ship we shot, hit position
Ship.register_event_type('on_enemy_hit')

# This ship has killed an enemy
# Args: ship we killed
Ship.register_event_type('on_kill')
