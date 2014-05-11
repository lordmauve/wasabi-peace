import pyglet


class Sound(pyglet.media.Player):
    def __init__(self, sounds):
        """The sound object will load a list of sounds into memory, ready for playing."""

        self.player = pyglet.media.Player()
        self.sounds = {}
        self.playlist = []

        for sound in sounds:
            self.sounds[sound] = pyglet.resource.media(sound, streaming=False)

    def set_playlist(self, sounds):
        """Create a playlist for looping a group of sounds."""
        for sound in sounds:
            self.player.queue(self.sounds[sound])

    def play_playlist(self):
        """Plays songs in the playlist, looping throug them."""
        self.player.play()

    def play_sound(self, sound):
        self.sounds[sound].play()