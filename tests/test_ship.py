from nose.tools import eq_
from math import radians
from bitsofeight.sailing import get_sail_power, get_heeling_moment


def test_downwind():
    """Sailing downwind is pretty fast."""
    eq_(get_sail_power(radians(0)), 0.7)


def test_beam_reach():
    """Sailing across the wind is fastest."""
    eq_(get_sail_power(radians(90)), 1.0)


def test_beam_reach2():
    """Sailing across the wind is fastest."""
    eq_(get_sail_power(radians(-90)), 1.0)


def test_close_hauled():
    """Close-hauled sailing is fast too."""
    p = get_sail_power(radians(135))
    assert 0.7 <= p <= 0.85, \
        "%f is not in [0.7, 0.85]" % p


def test_close_hauled2():
    """Close-hauled sailing is fast too."""
    p = get_sail_power(radians(-135))
    assert 0.7 <= p <= 0.85, \
        "%f is not in [0.7, 0.85]" % p


def test_upwind():
    """Can't really sail to windward."""
    eq_(get_sail_power(radians(180)), 0.2)


def test_heeling_downwind():
    """Downwind we don't heel."""
    eq_(get_heeling_moment(0), 0.0)


def test_heeling_upwind():
    """Anywhere to windward, we don't really heel."""
    assert abs(get_heeling_moment(170)) < 0.1


def test_heeling_beam():
    """Heeling moment is strong if we're sailing across the wind."""
    assert get_heeling_moment(90) > 0.5


def test_heeling_beam2():
    """Heeling moment is strong if we're sailing across the wind."""
    assert get_heeling_moment(-90) < -0.5
