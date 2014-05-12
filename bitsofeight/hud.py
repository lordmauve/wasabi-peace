from pyglet import gl
import pyglet.resource
from pyglet.graphics import Batch, OrderedGroup
from pyglet.sprite import Sprite, SpriteGroup
from pyglet.text import Label

FONT_NAME = 'Benegraphic'
COLOUR = (0x2c, 0x21, 0x21, 0xff)  # Brown colour


scroll_left = pyglet.resource.image('scroll-left.png')
scroll_left.anchor_x = 10
scroll_right = pyglet.resource.image('scroll-right.png')
scroll_right.anchor_x = 10
scroll_bg = pyglet.resource.image('scroll-bg.png')


class ScrollBG(object):
    def __init__(self, left, right, bottom, batch, group=None):
        w = scroll_bg.width
        h = scroll_bg.height
        top = bottom + h

        group = SpriteGroup(
            texture=scroll_bg,
            blend_src=gl.GL_SRC_ALPHA,
            blend_dest=gl.GL_ONE_MINUS_SRC_ALPHA,
            parent=group
        )

        vb = scroll_bg.tex_coords[1]
        vt = scroll_bg.tex_coords[7]
        ul = scroll_bg.tex_coords[0]
        ur = scroll_bg.tex_coords[3]

        frac = min((right - left) / float(w), 1.0)
        ur = ul + (ur - ul) * frac

        self.list = batch.add(
            4, gl.GL_QUADS, group,
            ('v2f', [
                left, bottom,
                left, top,
                right, top,
                right, bottom
            ]),
            ('t2f', [
                ul, vb,
                ul, vt,
                ur, vt,
                ur, vb
            ])
        )


class Scroll(object):
    def __init__(self, text, pos, batch):
        self.text = text
        x, y = self.pos = pos

        group = OrderedGroup(1)
        self.label = Label(
            text,
            font_name=FONT_NAME,
            font_size=28,
            color=COLOUR,
            x=x + 20,
            y=y + 15,
            group=group,
            batch=batch
        )
        w = self.label.content_width + 40
        self.bg = ScrollBG(
            x, x + w, y,
            batch=batch,
            group=OrderedGroup(0)
        )
        self.left = Sprite(scroll_left, x=x, y=y, group=group, batch=batch)
        self.right = Sprite(scroll_right, x=x + w, y=y, group=group, batch=batch)


class HUD(object):
    def __init__(self):
        self.batch = Batch()
        self.objects = []

    def create_scroll(self, text, pos):
        s = Scroll(text, pos, self.batch)
        self.objects.append(s)
        return s

    def destroy_scroll(self, scroll):
        self.objects.remove(scroll)

    def clear(self):
        del self.objects[:]

    def draw(self):
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(0, 800, 0, 600, 1, -1)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        self.batch.draw()
