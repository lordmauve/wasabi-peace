"""Some sailing heuristics."""
from math import sin, cos, pi, radians

tau = 2 * pi
closest_starboard = radians(160)
closest_port = radians(200)


def get_sail_power(angle_to_wind):
    """Get an approximation for the amount of power the sail derives from the wind."""
    if closest_starboard < angle_to_wind % tau < closest_port:
        return 0.2
    s = sin(angle_to_wind)
    return (
        0.4 * s * s +
        0.1 * cos(angle_to_wind) +
        0.6  # get a little bit anyway
    )


def get_heeling_moment(angle_to_wind):
    """Get an approximation for the heeling moment at a given angle to the wind."""
    a = angle_to_wind % tau
    if a > pi:
        a -= tau
    if closest_starboard < a < closest_port:
        return 0
    return sin(0.5 * a) - 0.25 * sin(1.5 * a)


def get_sail_setting(angle_to_wind):
    return sin(angle_to_wind)
