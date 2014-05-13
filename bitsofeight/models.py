from euclid import Vector3
from wasabisg.loaders.objloader import ObjFileLoader
from wasabisg.model import Material, Model, Mesh
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
            Kd=(0.2, 0.4, 0.6),
            Ks=(1.0, 1.0, 1.0, 1.0),
            Ns=30.0,
            illum=1
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


def optimise_model(model):
    """Combine meshes with identical materials.

    This significantly improves drawing performance.

    """
    from array import array
    materials = {}
    meshes_by_mat = {}
    for m in model.meshes:
        matid = id(m.material)
        mode = m.mode
        materials[matid] = m.material
        meshes_by_mat.setdefault((mode, matid), []).append(m)

    out = []
    for (mode, matid), meshes in meshes_by_mat.items():
        vs = array('f')
        ns = array('f')
        uvs = array('f')
        indices = array('L')
        for m in meshes:
            offset = len(vs) // 3
            vs.extend(m.vertices)
            ns.extend(m.normals)
            uvs.extend(m.texcoords)
            indices.extend(i + offset for i in m.indices)
        out.append(Mesh(
            mode=mode,
            vertices=vs,
            normals=ns,
            texcoords=uvs,
            indices=indices,
            material=materials[matid]
        ))
    model.meshes = out


optimise_model(ship_model)
