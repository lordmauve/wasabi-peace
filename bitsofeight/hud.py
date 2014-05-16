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

    def delete(self):
        if self.list:
            self.list.delete()
            self.list = None


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

    def delete(self):
        self.label.delete()
        self.left.delete()
        self.right.delete()
        self.bg.delete()



class HUD(object):
    SPRITES = {
        'captain': 'captain.png',
    }

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.batch = Batch()
        self.load_sprites()

    def load_sprites(self):
        load = pyglet.resource.image
        self.sprites = dict((k, load(v)) for k, v in self.SPRITES.items())

    def create_scroll(self, text, x, y):
        return Scroll(text, (x, y), self.batch)

    def remove_scroll(self, scroll):
        scroll.delete()

    def create_sprite(self, name, x, y):
        return Sprite(self.sprites[name], x, y, batch=self.batch)

    def draw(self):
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(0, self.width, 0, self.height, 1, -1)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        self.batch.draw()
