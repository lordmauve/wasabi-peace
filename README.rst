Bits'o'Eight
============

A game of pirating on the high seas.

Tips
----

 * Sink as many enemy ships as you can.
 * You can't sail to windward. You should sail at 45 degrees to the wind and
   "tack" back and forth through the wind to go upwind. This is called "beating
   to windward".
 * Reduce the amount of sail you're using (your "windage") to reduce your
   heeling force. This will flatten out the boat and let your guns fire more
   horizontally.

Installation
------------

You will need the dependencies list in requirements.txt.

Note in particular that if you are on 64-bit you will need the `wasabi-lepton`__
fork of lepton that includes fixes for 64-bit support.

.. __: https://pypi.python.org/pypi/wasabi-lepton

Bits o' Eight has been developed and tested on Pyglet 1.2alpha1 from the
`Pyglet download page`_, though some performance improvements weren noticed
using the `trunk version of Pyglet`.

.. _Pyglet download page: https://code.google.com/p/pyglet/downloads/list
.. _trunk version of Pyglet: https://code.google.com/p/pyglet/source/browse/

Controls
--------

The game is intended to be controlled from your smartphone or tablet. A desktop
browser with Websocket support will work if no suitable handheld device is
available.

The game will show a URL for the controls when the game starts. Navigate to
this URL on your device to start the game.

Closing the controls page will pause the game.
