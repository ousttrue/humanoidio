from lib import formats
EPSILON = 5e-3


def check_vec(_l, _r):
    for ll, rr in zip(_l, _r):
        d = abs(ll - rr)
        if d > EPSILON:
            return False
    return True


def check_seq(_l, _r):
    for l, r in zip(_l, _r):
        if not check_vec(l, r):
            return False
    return True


def check_mesh(l: formats.GltfContext, lm: formats.gltf.Mesh,
               r: formats.GltfContext, rm: formats.gltf.Mesh):
    if len(lm.primitives) != len(rm.primitives):
        return False

    lb = formats.BytesReader(l)
    rb = formats.BytesReader(r)

    for lp, rp in zip(lm.primitives, rm.primitives):
        # pos
        l_pos = [p for p in lb.get_bytes(lp.attributes['POSITION'])]
        r_pos = [p for p in rb.get_bytes(rp.attributes['POSITION'])]
        if len(l_pos) != len(r_pos):
            return False

        # normal

        # texcoord_0

        # weights_0

        # joints_0

        # indices
        if not isinstance(lp.indices, int):
            return False
        if not isinstance(rp.indices, int):
            return False
        li = [i for i in lb.get_bytes(lp.indices)]
        ri = [i for i in rb.get_bytes(rp.indices)]
        if len(li) != len(ri):
            return False
        # if not check_vec(li, ri):
        #     return False
        # a = 0

    return True


def is_unlit(material: formats.gltf.Material) -> bool:
    if not material.extensions:
        return False
    if not material.extensions.KHR_materials_unlit:
        return False
    return True


def check_material(l: formats.GltfContext, lm: formats.gltf.Material,
                   r: formats.GltfContext, rm: formats.gltf.Material):
    if not check_vec(lm.pbrMetallicRoughness.baseColorFactor,
                     rm.pbrMetallicRoughness.baseColorFactor):
        raise Exception('pbrMetallicRoughness.baseColorFactor')

    if lm.pbrMetallicRoughness.baseColorTexture and not rm.pbrMetallicRoughness.baseColorTexture:
        raise Exception('r has not colorTexture')
    if not lm.pbrMetallicRoughness.baseColorTexture and rm.pbrMetallicRoughness.baseColorTexture:
        raise Exception('l has not colorTexture')

    if is_unlit(lm) and not is_unlit(rm):
        raise Exception('r is not Unlit')
    elif not is_unlit(lm) and is_unlit(rm):
        raise Exception('l is not unlit')
    elif is_unlit(lm) and is_unlit(rm):
        # unlit
        pass
    else:
        # pbr
        pass
    return True


def check_texture(l: formats.GltfContext, lt: formats.gltf.Texture,
                   r: formats.GltfContext, rt: formats.gltf.Texture):
    ls = l.gltf.bufferViews[lt.source]
    rs = r.gltf.bufferViews[rt.source]


    return True

def check_gltf(l: formats.GltfContext, r: formats.GltfContext):
    '''
    import して再 export した結果が一致するか、緩く比較する
    '''

    # textures
    if l.gltf.textures and not r.gltf.textures:
        raise Exception('r.gltf.textures is None')
    elif not l.gltf.textures and r.gltf.textures:
        raise Exception('l.gltf.textures is None')
    elif l.gltf.textures and r.gltf.textures:
        if len(l.gltf.textures) != len(r.gltf.textures):
            raise Exception('len(l.gltf.textures) != len(r.gltf.textures)')
        for ll, rr in zip(l.gltf.textures, r.gltf.textures):
            if not check_texture(l, ll, r, rr):
                return False

    # materials
    if l.gltf.materials and not r.gltf.materials:
        raise Exception('r.gltf.materials is None')
    elif not l.gltf.materials and r.gltf.materials:
        raise Exception('l.gltf.materials is None')
    elif l.gltf.materials and r.gltf.materials:
        if len(l.gltf.materials) != len(r.gltf.materials):
            return Exception('len(l.gltf.materials) != len(r.gltf.materials)')
        for ll, rr in zip(l.gltf.materials, r.gltf.materials):
            if not check_material(l, ll, r, rr):
                return False

    # meshes
    if l.gltf.meshes and not r.gltf.meshes:
        raise Exception('r.gltf.meshes is None')
    elif not l.gltf.meshes and r.gltf.meshes:
        raise Exception('l.gltf.meshes is None')
    elif l.gltf.meshes and r.gltf.meshes:
        if len(l.gltf.meshes) != len(r.gltf.meshes):
            raise Exception('len(l.gltf.meshes) != len(r.gltf.meshes)')
        for ll, rr in zip(l.gltf.meshes, r.gltf.meshes):
            if not check_mesh(l, ll, r, rr):
                return False

    return True
