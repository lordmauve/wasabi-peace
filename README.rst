Bits'o'Eight
============

All platforms
-------------

This game requires runs on Python 2.7. Installation requires the pip utility and optionally virtualenv.

Additional instructions for Windows users
-----------------------------------------

Download and install Pyglet 1.2 Alpha1 from the `Pyglet download page`_

: _Pyglet download page: https://code.google.com/p/pyglet/downloads/list

Installing the game from source
-------------------------------

Make a virtualenv, and checkout the project source code::

    mkdir bitsofeight
    virtualenv bitsofeight
    cd bitsofeight
    source bin/activate
    hg clone https://bitbucket.org/lordmauve/wasabi-peace src

Now you can use pip to build the project::

    pip install -e src

Currently, the game only supports Linux.


