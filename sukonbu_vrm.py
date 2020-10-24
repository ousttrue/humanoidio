import pathlib
from sukonbu.sukonbu.json_schema import JsonSchema
from typing import NamedTuple, Any, List, Dict, Optional, TextIO
from sukonbu.sukonbu.json_schema_parser import JsonSchemaParser
from sukonbu.sukonbu.generators import python, dlang, cpp
import argparse
HERE = pathlib.Path(__file__).absolute().parent


def main():
    '''
    sukonbu_vrm.py {json_path} [--lang python] [--dst dir]

    * meshes[].extras.targetNames
    * meshes[].primitives[].extras.targetNames
    * extensions.VRM

    TODO: 1.0系の
    * extensions.VRMC_VRM
    '''
    parser = argparse.ArgumentParser(description='sukonbu.')
    parser.add_argument('json', help='target json file.')
    parser.add_argument('--lang',
                        default='python',
                        choices=['python', 'dlang', 'cpp'],
                        help='generate language.')
    parser.add_argument('--dst', help='output directory.')
    parser.add_argument('--namespace', default='sukonbu')
    args = parser.parse_args()

    # source json path
    if not args.json:
        parser.print_help()
    path = pathlib.Path(args.json)
    if not path.exists():
        raise FileExistsError(path)

    # parse
    gltf_path = pathlib.Path(path)
    js_parser = JsonSchemaParser()
    js_parser.process(gltf_path)

    # extensions
    unlit_path = gltf_path.parent.parent.parent.parent / 'extensions/2.0/Khronos/KHR_materials_unlit/schema/gltf.KHR_materials_unlit.schema.json'
    unlit = JsonSchemaParser(gltf_path.parent)
    unlit.process(unlit_path)
    js_parser.set('materials[].extensions.KHR_materials_unlit', unlit)

    vrm_path = HERE / 'vrm-specification/specification/0.0/schema/vrm.schema.json'
    vrm = JsonSchemaParser(gltf_path.parent)
    vrm.process(vrm_path)
    js_parser.set('extensions.VRM', vrm)

    # extras
    meshTargetNames = JsonSchemaParser()
    meshTargetNames.root = JsonSchema(type='array',
                                      title='meshTargetNames',
                                      items=JsonSchema(type='str'))
    js_parser.set('meshes[].extras.targetNames', meshTargetNames)

    primTargetNames = JsonSchemaParser()
    primTargetNames.root = JsonSchema(type='array',
                                      title='primTargetNames',
                                      items=JsonSchema(type='str'))
    js_parser.set('meshes[].primitives[].extras.targetNames', meshTargetNames)
    
    if args.dst:
        dst = pathlib.Path(args.dst)
        if args.lang == 'python':
            python.generate(js_parser, dst)
        elif args.lang == 'dlang':
            dlang.generate(js_parser, dst)
        elif args.lang == 'cpp':
            cpp.generate(js_parser, dst, args.namespace)
        else:
            raise NotImplementedError(args.lang)

    else:
        js_parser.print()


if __name__ == '__main__':
    main()
