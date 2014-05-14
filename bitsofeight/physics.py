"""A crude physics engine based on spheres.

Spheres are very quick to detect collisions on.

"""
from math import sqrt
from euclid import Point3, Vector3, Quaternion, Matrix4


class Sphere(object):
    def __init__(self, centre=Point3(0, 0, 0), radius=1.0):
        self.centre = centre
        self.radius = radius

    def collides(self, s):
        """Is this sphere colliding with another sphere?"""
        dist2 = (self.centre - s.centre).magnitude_squared()
        r = self.radius + s.radius
        return dist2 <= r * r

    def __eq__(self, ano):
        """Return True if ano describes the same sphere."""
        return (
            (self.centre - ano.centre).magnitude() < 1e-6 and
            abs(self.radius - ano.radius) < 1e-6
        )

    def __contains__(self, p):
        """Return True if the point p is within the Sphere."""
        dist2 = (self.centre - p).magnitude_squared()
        r = self.radius
        return dist2 <= r * r

    def transformed(self, m):
        """Return a new sphere whose position is transformed by the matrix m.

        Radius will not be affected.

        """
        return Sphere(m * self.centre, self.radius)

    def translated(self, v):
        """Return a new sphere translated by the vector v."""
        return Sphere(self.centre + v, self.radius)


class Positionable(object):
    """Base class for things that are positionable."""
    pos = Point3()
    rot = Quaternion()

    def __init__(self, pos=None, rot=None):
        if pos:
            self.pos = pos
        if rot:
            self.rot = rot

    def local_to_world(self, v):
        return self.rot * v + self.pos

    def get_matrix(self):
        r = self.rot.get_matrix()
        t = Matrix4.new_translate(*self.pos)
        return t * r


class Body(object):
    def __init__(self, positionable, shapes):
        self.positionable = positionable
        self._shapes = shapes
        self._volume = self._bound_volume()

    def _bound_volume(self):
        """Compute an untransformed bounding volume for the body's shapes."""
        centroid = (
            sum((s.centre for s in self._shapes), Vector3(0, 0, 0)) *
            (1.0 / len(self._shapes))
        )
        r = 0.0
        for s in self._shapes:
            r = max(r, (s.centre - centroid).magnitude() + s.radius)
        return Sphere(centroid, r)

    def bounds(self):
        return self._volume.translated(self.positionable.pos)

    def __len__(self):
        return len(self._shapes)

    def __iter__(self):
        pos = self.positionable.pos
        return (s.translated(pos) for s in self._shapes)

    def collide(self, b):
        """Detect whether b is colliding with this Body.

        If colliding, return a Vec3 which is the separation needed to part
        them.

        Otherwise, return None.

        """
        if not self.bounds().collides(b.bounds()):
            return None

        for s in self:
            for bs in b:
                if s.collides(bs):
                    v = s.centre - bs.centre
                    dist = v.magnitude()
                    need = s.radius + bs.radius
                    return ((need - dist) / dist) * v


class LineSegment(object):
    @classmethod
    def from_points(cls, point1, point2):
        return cls(point1, point2 - point1)

    def __init__(self, pos, vec):
        self.o = pos
        self.length = length = vec.magnitude()
        self.l = vec * (1.0 / length)  # normalize l
        self._bounds = None

    def bounds(self):
        if self._bounds is not None:
            return self._bounds
        r = self.length * 0.5
        b = self._bounds = Sphere(self.o + r * self.l, r)
        return b

    def collide_body(self, body):
        """Find the closest intersection with body, or return None if no intersection."""
        pos = None
        if self.bounds().collides(body.bounds()):
            mind = float('inf')
            for s in body:
                i = self.first_intersection(s)
                if i is None:
                    continue
                d, p = i
                if d < mind:
                    pos = p
                    mind = d
        return pos

    def first_intersection(self, sphere):
        """Get the first point of intersection between the line and the given sphere."""
        o = self.o
        l = self.l
        length = self.length

        c = sphere.centre
        r = sphere.radius

        co = o - c

        b = l.dot(co)
        discriminant = b * b - co.magnitude_squared() + r * r
        if discriminant < 0:
            return None

        sqrt_discriminant = sqrt(discriminant)
        mb = -b
        d1 = mb - sqrt_discriminant

        if d1 > length:
            return None

        d2 = mb + sqrt_discriminant

        if d2 < 0:
            return None

        if d1 < 0:
            return 0, o

        return d1, o + d1 * l


class Physics(object):
    def __init__(self):
        self.bodies = []

    def add(self, body):
        self.bodies.append(body)

    def remove(self, body):
        self.bodies.remove(body)
