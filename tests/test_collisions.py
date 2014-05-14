from nose.tools import eq_
from mock import patch
from euclid import Point3, Vector3
from bitsofeight.physics import Sphere, Body, Positionable, Physics


def test_collision():
    """The physics engine detects colliding bodies."""
    shapes = [Sphere()]
    physics = Physics()
    b1 = Body(
        Positionable(Point3(1.75, 0, 0)),
        shapes
    )
    b2 = Body(
        Positionable(),
        shapes
    )
    physics.add(b1)
    physics.add(b2)
    with patch.object(physics, 'handle_collision') as handle_collision:
        physics.do_collisions()

    handle_collision.assert_called_with(b1, b2, Vector3(-0.25, 0, 0))


def test_resolve_collision():
    """The physics engine resolves a collision."""
    shapes = [Sphere()]
    physics = Physics()
    b1 = Body(
        Positionable(Point3(-1.75, 0, 0), vel=Vector3(1, 0, 0)),
        shapes
    )
    b2 = Body(
        Positionable(),
        shapes
    )
    physics.add(b1)
    physics.add(b2)

    physics.do_collisions()

    out = [
        b1.positionable.pos,
        b2.positionable.pos,
        b1.positionable.vel,
        b2.positionable.vel
    ]
    expected = [
        Point3(-2, 0, 0),
        Point3(0, 0, 0),
        Vector3(0.35, 0, 0),
        Vector3(0.65, 0, 0)
    ]
    eq_(out, expected)


def test_resolve_collision_static():
    """The physics engine resolves a collision between static bodies"""
    shapes = [Sphere()]
    physics = Physics()
    b1 = Body(
        Positionable(Point3(0.5, 0, 0)),
        shapes
    )
    b2 = Body(
        Positionable(Point3(-0.5, 0, 0)),
        shapes
    )
    physics.add(b1)
    physics.add(b2)

    physics.do_collisions()

    out = [
        b1.positionable.pos,
        b2.positionable.pos,
        b1.positionable.vel,
        b2.positionable.vel
    ]
    expected = [
        Point3(1, 0, 0),
        Point3(-1, 0, 0),
        Vector3(0, 0, 0),
        Vector3(0, 0, 0)
    ]
    eq_(out, expected)
