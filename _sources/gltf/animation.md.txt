# Animation

<https://www.khronos.org/registry/glTF/specs/2.0/glTF-2.0.html#reference-animation>

```js
// https://github.com/KhronosGroup/glTF-Sample-Models/tree/master/2.0/AnimatedCube
{
   "animations" : [
      {          
         "samplers" : [
            {
               "input" : 0, // time
               "interpolation" : "LINEAR",
               "output" : 1 // value
            }
         ],
         "channels" : [
            {
               "sampler" : 0, // samplers[0]
               "target" : {
                  "node" : 0,
                  "path" : "rotation"
               }
            }
         ],
         "name" : "animation_AnimatedCube"
      }
   ],
}
```

## Sampler

Animation Curve.

* input: timeへのアクセッサー(`float`, `SCALAR`)
* output: valueへのアクセッサー
    * rotation: (`float`, `VEC4`)
    * translation: (`float`, `VEC3`)

## Channel

Sampler と Target を結びつける。

```js
"target" : {
    "node" : 0,
    "path" : "rotation" // "translation", "scale" or "weights" (morph target)
}
```

## Interpolation

`interpolation` が `CUBICSPLINE` の場合は、sampler の output は、キーフレームの３倍の要素数を持ち、
`left tangent`, `value`, `right tangent` というデータになる。
