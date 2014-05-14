import math
from nose.tools import eq_
from euclid import Point3, Matrix4, Vector3
from bitsofeight.physics import Sphere, LineSegment, Body, Positionable


def test_sphere_contains():
    """The origin lies within a unit sphere."""
    assert Point3(0, 0, 0) in Sphere()


def test_sphere_contains2():
    """The a point on the surface of a sphere is within the sphere."""
    assert Point3(0, 4, 0) in Sphere(Point3(0, 2, 0), radius=2)


def test_sphere_contains3():
    """A point slightly outside the sphere is not in the sphere."""
    assert Point3(0, 2, 0.1) not in Sphere(radius=2)


def test_sphere_collide():
    """Two overlapping spheres collide."""
    c = Point3(72, 27, 1)
    c2 = Point3(71, 26, 0)
    assert (c2 - c).magnitude() < 2
    assert Sphere(c, radius=1).collides(Sphere(c2, radius=1))


def test_sphere_collide2():
    """Non-overlapping spheres do not collide."""
    c = Point3(72, 27, 1.5)
    c2 = Point3(71, 26, 0)
    assert (c2 - c).magnitude() > 2
    assert not Sphere(c, radius=1).collides(Sphere(c2, radius=1))


def test_sphere_transform():
    """We can transform a sphere."""
    m = Matrix4.new_translate(0, 0, 5)
    assert Sphere(radius=2).transformed(m) == Sphere(Point3(0, 0, 5), 2)


def test_body_bounds():
    """Get the bounds for a body."""
    b = Body(
        Positionable(),
        shapes=[
            Sphere(Point3(-1, 0, 0), 2),
            Sphere(Point3(1, 0, 0), 1),
        ]
    )
    assert b.bounds() == Sphere(radius=3)


def test_body_bounds_transformed():
    """Get the bounds for a body."""
    b = Body(
        Positionable(pos=Point3(10, 10, 10)),
        shapes=[
            Sphere(Point3(-1, 0, 0), 2),
            Sphere(Point3(1, 0, 0), 1),
        ]
    )
    assert b.bounds() == Sphere(Point3(10, 10, 10), radius=3)


def test_body_collision():
    """We can get a separation vector if two bodies collide."""
    shapes = [Sphere(Point3(0, 0, 0), 2)]
    b1 = Body(
        Positionable(pos=Point3(1, 0, 0)),
        shapes
    )
    b2 = Body(
        Positionable(pos=Point3(4.75, 0, 0)),
        shapes
    )
    col = b1.collide(b2)
    assert col is not None
    eq_(col, Vector3(-0.25, 0, 0))


def test_line_segment_bounds():
    """Get a bounding sphere for a line segment."""
    l = LineSegment(Point3(5, 5, 5), Vector3(-10, -10, -10))
    eq_(l.bounds(), Sphere(radius=math.sqrt(75)))


def test_construct_line_segment():
    """We can initialise a line segment."""
    line = LineSegment(Point3(0, 0, -10), Vector3(0, 0, 10))
    eq_(line.o, Point3(0, 0, -10))
    eq_(line.l, Vector3(0, 0, 1))
    eq_(line.length, 10)


def test_line_sphere_intersection():
    """Get the point of first intersection between a line and a sphere.

    Hit the sphere right in the centre.

    """
    s = Sphere()
    l = LineSegment(Point3(0, 0, -10), Vector3(0, 0, 10))
    i = l.first_intersection(s)
    assert i is not None
    eq_(i, (9, Point3(0, 0, -1)))


def test_line_sphere_intersection2():
    """Point of intersection if we're already past the sphere."""
    s = Sphere()
    l = LineSegment(Point3(0, 0, 1.5), Vector3(0, 0, 2))
    i = l.first_intersection(s)
    assert i is None


def test_line_sphere_intersection3():
    """Point of intersection if we stop short of the sphere."""
    s = Sphere()
    l = LineSegment(Point3(0, 0, -2.5), Vector3(0, 0, 1))
    i = l.first_intersection(s)
    assert i is None


def test_line_sphere_intersection4():
    """Point of intersection if we start inside the sphere."""
    s = Sphere()
    l = LineSegment(Point3(), Vector3(0, 0, 2))
    i = l.first_intersection(s)
    assert i is not None
    eq_(i, (0, Point3()))


def test_line_sphere_intersection5():
    """Point of intersection if we hit the sphere at an oblique angle."""
    s = Sphere()
    l = LineSegment(Point3(0.5, 0, -5), Vector3(0, 0, 5))
    i = l.first_intersection(s)
    assert i is not None
    eq_(i[0], 5 - math.sqrt(0.75))
