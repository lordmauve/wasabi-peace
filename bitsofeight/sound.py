from itertools import cycle

from pyglet.media import Player
from pyglet.resource import media, ResourceNotFoundException


class Music(Player):
    def __init__(self, songs):
        """The Music object will keep a playlist of songs, looping through them when played."""

        super(Music, self).__init__()

        for song in songs:
            song = media(song)
            self.queue(song)

        self.songs = cycle(songs)
        self.queue(media(self.songs.next()))

    def on_eos(self):
        """Ensure that the sound queue is looped."""
        super(Music, self).on_eos()
        self.queue(media(self.songs.next()))


class Sound(object):
    def __init__(self, sounds):
        """Loud sounds into memory for immediate playing."""

        self.sounds = {}
        for sound in sounds:
            try:
                self.sounds[sound] = media(sound, streaming=False)
            except ResourceNotFoundException:
                pass

    def play_sound(self, sound):
        self.sounds[sound].play()

    def sound_on_event(self, sound, event_handler, event):
        """Register a sound with an event on and EventHanlder.

        That sound will play whenever the event is fired.

        """
        if event in self.__dict__:
            return

        self.__dict__[event] = lambda *args: self.play_sound(sound)
        self.__dict__[event].__name__ = event
        event_handler.push_handlers(self.__dict__[event])