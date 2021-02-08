import pathlib
from typing import NamedTuple, Any, List, Dict, Optional
from sukonbu.sukonbu.json_schema_parser import JsonSchemaParser
from sukonbu.sukonbu.generators import python
HERE = pathlib.Path(__file__).absolute().parent


class Generation(NamedTuple):
    dst: pathlib.Path
    gltf: pathlib.Path
    extension: Optional[pathlib.Path]

    def generate(self):
        js_parser = None
        if self.extension:
            # extensions
            js_parser = JsonSchemaParser(self.gltf.parent)
            js_parser.process(self.extension)
        else:
            # gltf
            js_parser = JsonSchemaParser()
            js_parser.process(self.gltf)
        dst = pathlib.Path(self.dst)
        python.generate(js_parser, dst)


def main():
    '''
    TODO: 1.0系の
    * extensions.VRMC_VRM
    '''

    generations = [
        Generation(
            HERE / 'lib/formats/generated/gltf.py',
            HERE / 'sukonbu/glTF/specification/2.0/schema/glTF.schema.json',
            None),
        Generation(
            HERE / 'lib/formats/generated/KHR_materials_unlit.py',
            HERE / 'sukonbu/glTF/specification/2.0/schema/glTF.schema.json',
            HERE /
            'sukonbu/glTF/extensions/2.0/Khronos/KHR_materials_unlit/schema/gltf.KHR_materials_unlit.schema.json'
        ),
        Generation(
            HERE / 'lib/formats/generated/vrm.py',
            HERE / 'sukonbu/glTF/specification/2.0/schema/glTF.schema.json',
            HERE /
            'vrm-specification/specification/0.0/schema/vrm.schema.json')
    ]

    for g in generations:
        g.generate()


if __name__ == '__main__':
    main()
