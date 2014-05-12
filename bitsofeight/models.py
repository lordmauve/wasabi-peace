from wasabisg.loaders.objloader import ObjFileLoader
from wasabisg.model import Material, Model
from wasabisg.plane import Plane
from wasabisg.sphere import Sphere


model_loader = ObjFileLoader()
ship_model = model_loader.load_obj('assets/models/ship.obj')
skydome = model_loader.load_obj('assets/models/skydome.obj')

sea_model = Model(meshes=[
    Plane(
        size=1000,
        material=Material(
            name='sea',
            Kd=(0.2, 0.4, 0.6)
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
