import pyglet.resource
from euclid import Point3, Vector3
from lepton import Particle
from lepton.emitter import StaticEmitter
from lepton import controller
from wasabisg.particles import ParticleSystemNode


# The global particle system
# Groups within here will be renderer
# Actors should define emitters; the world will spawn these
particles = ParticleSystemNode()


def load(name):
    return pyglet.resource.texture(name)


wake_particles = particles.create_group(
    controllers=[
        #        Drag(0.1, 0.0, (0, 0, 0)),
        controller.Movement(),
        controller.Lifetime(5),
        controller.Fader(
            start_alpha=0.0,
            max_alpha=0.3,
            end_alpha=0.0,
            fade_in_end=0.2,
            fade_out_start=0.3,
            fade_out_end=5.0
        )
    ],
    texture=load('foam.png')
)


class WakeEmitter(object):
    group = wake_particles

    # position, velocity, rate for each emitter
    emitter_positions = [
        (Point3(1.3, 0.2, 3), Vector3(0.5, 0, 0), 5),  # port bow
        (Point3(-1.3, 0.2, 3), Vector3(-0.5, 0, 0), 5),  # starboard bow
        (Point3(0, 0.2, -3), Vector3(0, 0, 0), 20),  # stern
    ]

    def __init__(self, ship):
        self.ship = ship

        self.emitters = [
            StaticEmitter(
                template=Particle(
                    position=tuple(p),
                    velocity=tuple(v),
                    size=(0.2, 0.2, 0.2),
                    color=(1, 1, 1, 0.2),
                ),
                deviation=Particle(
                    position=(0.02, 0.0, 0.02) if i < 2 else (0.2, 0.0, 0.2),
                    velocity=(0.04, 0.0, 0.04),
                ),
                rate=5 if i < 2 else 20
            ) for i, (p, v, rate) in enumerate(self.emitter_positions)
        ]

    def start(self):
        """Bind all emitters to their groups so that they will emit"""
        wake_particles.bind_controller(*self.emitters)

    def stop(self):
        """Unbind all emitters from their groups"""
        wake_particles.unbind_controller(*self.emitters)

    def update(self):
        """Update the emitters."""
        m = self.ship.get_matrix()
        for e, (p, v, r) in zip(self.emitters, self.emitter_positions):
            px, _, pz = m * p
            e.template.position = px, 0.1, pz
            vx, _, vz = m * v
            e.template.velocity = vx, 0.0, vz
            e.rate = self.ship.vel.magnitude() * r
