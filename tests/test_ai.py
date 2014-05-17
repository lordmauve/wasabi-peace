from math import pi, radians, degrees
from euclid import Vector3, Point3
from mock import Mock
from nose.tools import eq_

from bitsofeight import ai


def test_relative_bearing():
    """Straight ahead means an angle of 0.0"""
    s = Mock(
        pos=Point3(),
        angle=0.0
    )
    a = ai.ShipAI(s)
    eq_(
        a.relative_bearing(Point3(0, 0, 1)),
        0.0
    )


def test_relative_bearing2():
    """The ship's own angle is taken into account."""
    s = Mock(
        pos=Point3(),
        angle=0.5
    )
    a = ai.ShipAI(s)
    eq_(
        a.relative_bearing(Point3(0, 0, 1)),
        -0.5
    )


def approx_eq(a, b):
    assert abs(a - b) < 1e-5, \
        "%r !~== to %r" % (a, b)


def test_relative_bearing3():
    """Positive angles are to port."""
    s = Mock(
        pos=Point3(),
        angle=0.0
    )
    a = ai.ShipAI(s)
    approx_eq(
        a.relative_bearing(Point3(1, 0, 1)),
        pi / 4
    )


def test_relative_bearing4():
    """Behind and to the right of us is to starboard."""
    s = Mock(
        pos=Point3(),
        angle=0.0
    )
    a = ai.ShipAI(s)
    approx_eq(
        a.relative_bearing(Point3(-1, 0, -1)),
        pi * -0.75
    )


def test_relative_bearing5():
    s = Mock(
        pos=Point3(),
        angle=pi
    )
    a = ai.ShipAI(s)
    approx_eq(
        abs(a.relative_bearing(Point3(0, 0, 1))),
        pi
    )
