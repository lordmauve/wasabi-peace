from itertools import product
from euclid import Vector3
from wasabisg.loaders.objloader import ObjFileLoader
from wasabisg.model import Material, Model, Mesh
from wasabisg.plane import Plane
from wasabisg.sphere import Sphere

from .sea import sea_shader


model_loader = ObjFileLoader()
hull_model = model_loader.load_obj('assets/models/hull.obj')
skydome = model_loader.load_obj('assets/models/skydome.obj')

mast_models = [
    model_loader.load_obj('assets/models/%s%s.obj' % (mast, state))
    for mast in ['foremast', 'mainmast', 'mizzenmast']
    for state in ['-furled', '-half', '']
]

sea_model = Model(meshes=[
    Plane(
        size=1000,
        material=Material(
            name='sea',
            Kd=(0.2, 0.4, 0.6),
            Ks=(1.0, 1.0, 1.0, 1.0),
            Ns=30.0,
            illum=1,
        )
    )
])

cannonball_model = Model(meshes=[
    Sphere(
        radius=0.1,
        latitude_divisions=3,
        longitude_divisions=6,
        material=model_loader.mtl_loader.get_material('Gunmetal')
    )
])
