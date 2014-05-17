from math import pi

tau = 2 * pi


def map_angle(a):
    """Map an angle into the [-pi, pi] range."""
    if a < -pi:
        return a + tau
    if a > pi:
        return a - tau

    return a

