import bpy
from logging import getLogger
logger = getLogger()


def debug_print(*args):
    print(*args)


def export_attrs(input, *excludes):
    return {attr: to_val(getattr(input, attr)) for attr in dir(input) if valid_attr(input, attr, excludes)}


def export_node(node):
    obj = {
        'bl_idname': node.bl_idname,
        'type': node.type,
        'attr': export_attrs(node, 'node_tree', 'parent'),
        'inputs': [export_attrs(ip) for ip in node.inputs],
        'outputs': [export_attrs(op) for op in node.outputs],
    }
    if node.type == 'GROUP':
        obj['GROUP_NAME'] = node.node_tree.name
    return obj


def export_link(nodes, link):
    return {
        'from_node': nodes.index(link.from_node),
        'from_socket': list(link.from_node.outputs).index(link.from_socket),
        'to_node': nodes.index(link.to_node),
        'to_socket': list(link.to_node.inputs).index(link.to_socket)
    }


def valid_attr(obj, attr, excludes):
    if attr in excludes:
        return False

    if attr.startswith("__"):
        return False

    val = getattr(obj, attr)
    valid = None
    try:
        setattr(obj, attr, val)
        return True
    except:
        return False


def to_val(val):
    if isinstance(val, str) or isinstance(val, int) or isinstance(val, float) or isinstance(val, bool) or val == None:
        return val
    else:
        return list(val)


def export_group(grp):
    return {
        'name': grp.node_tree.name,
        'bl_idname': grp.node_tree.bl_idname,
        'nodes': [export_node(node) for node in grp.node_tree.nodes],
        'links': [export_link(list(grp.node_tree.nodes), link) for link in grp.node_tree.links],
        'tree_attr': export_attrs(grp.node_tree, 'active_output', 'active_input', 'use_fake_user'),
        'inputs': [export_attrs(ip) for ip in grp.node_tree.inputs],
        'outputs': [export_attrs(op) for op in grp.node_tree.outputs],
    }


def export_groups(node_groups):
    return [export_group(grp) for grp in reversed(node_groups)]


def import_g(inputs, n):
    for x in inputs:
        logger.debug(str(x))
        inputs.remove(x)
    logger.debug('group: %s: %d %d' ,inputs, len(inputs), len(n))
    for src in n:
        logger.debug('in %s', src)
        if 'bl_socket_idname' in src:
            t = src['bl_socket_idname']
        elif 'bl_idname' in src:
            t = src['bl_idname']
        dst = inputs.new(name=src['name'], type=t)
        # if t!='NodeSocketVirtual' and 'NodeSocketVirtual' in str(dst):
        #    raise Exception('NodeSocketVirtual')
        # if dst.bl_idname!=src['bl_idname']:
        #    raise Exception('different bl_idname: ' + dst.bl_idname)
        for k, v in src.items():
            if k == 'name' or k == 'bl_idname':
                continue
            logger.debug('    %s %s %s %s', inputs, dst, k, v)
            setattr(dst, k, v)


def import_inout(node, n):
    logger.debug('inout %s', node)
    if len(node.inputs) != len(n['inputs']):
        raise Exception()
    for dst, src in zip(node.inputs, n['inputs']):
        for k, v in src.items():
            #logger.debug('    ', node, dst, k, v)
            setattr(dst, k, v)

    if len(node.outputs) != len(n['outputs']):
        raise Exception()
    for dst, src in zip(node.outputs, n['outputs']):
        for k, v in src.items():
            #logger.debug('    ', node, dst, k, v)
            setattr(dst, k, v)


def import_groups(src):
    groups = {}
    for g in src:
        #
        # group
        #
        if g['bl_idname'] != 'ShaderNodeTree':
            raise Exception('not ShaderNodeTree')
        group = bpy.data.node_groups.new(g['name'], g['bl_idname'])
        logger.debug('%s', group)

        group.use_fake_user = True
        groups[g['name']] = group

        logger.debug('## tree_attr')
        for k, v in g['tree_attr'].items():
            if k == 'name' or k == 'bl_idname':
                continue
            logger.debug('%s %s %s', group, k, v)
            setattr(group, k, v)

        logger.debug('## tree in out')
        import_g(group.inputs, g['inputs'])
        import_g(group.outputs, g['outputs'])

        logger.debug('## nodes')
        nodes = []
        for n in g['nodes']:
            node = group.nodes.new(n['bl_idname'])
            if 'GROUP_NAME' in n:
                node.node_tree = groups[n['GROUP_NAME']]
            nodes.append(node)

            import_inout(node, n)

            for k, v in n['attr'].items():
                setattr(node, k, v)

        logger.debug('## links: %d', len(nodes))
        for l in g['links']:
            logger.debug('%s', l)
            from_node = nodes[l['from_node']]
            logger.debug('%s %d %d', from_node, len(from_node.inputs), len(from_node.outputs))
            to_node = nodes[l['to_node']]
            logger.debug('%s %d %d', to_node, len(to_node.inputs), len(to_node.outputs))
            from_socket = from_node.outputs[l['from_socket']]
            to_socket = to_node.inputs[l['to_socket']]
            group.links.new(from_socket, to_socket, verify_limits=False)
    return groups


if __name__ == '__main__':
    logger.debug('####')
    size = 0.0
    main_area = None
    for area in bpy.context.screen.areas:
        if area.type == 'NODE_EDITOR' and area.width * area.height > size:
            size = area.width * area.height
            main_area = area
    active_group = main_area.spaces[0].node_tree.nodes.active

    groups = [active_group]
    index = 0
    while len(groups) > index:
        for node in groups[index].node_tree.nodes:
            if node.type == 'GROUP':
                groups.append(node)
            index += 1

    remove = []
    for i in range(0, len(groups)):
        grp1 = groups[i]
        for j in range(i+1, len(groups)):
            grp2 = groups[j]
            if grp1 != grp2 and grp1.node_tree == grp2.node_tree:
                remove.append(grp1)
    for x in remove:
        groups.remove(x)

    exported = export_groups(groups)

    import_groups(exported)

    # print(repr(exported))

    #import json
    #print(json.dumps(exported, indent=2))
