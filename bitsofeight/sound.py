import pyglet
from itertools import cycle


class Music(pyglet.media.Player):
    def __init__(self, songs):
        """The Music object will load keep a playlist of song, looping through them when played."""

        super(Music, self).__init__()

        for song in songs:
            song = pyglet.resource.media(song)
            self.queue(song)

        self.songs = cycle(songs)

    def on_eos(self):
        """Ensure that the sound queue is looped."""
        super(Music, self).on_eos()
        self.queue(pyglet.resource.media(self.songs.next()))
        self.play()