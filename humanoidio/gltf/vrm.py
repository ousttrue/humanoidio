from enum import Enum, auto


class HumanoidBones(Enum):
    unknown = auto()

    hips = auto()

    # region leg
    leftUpperLeg = auto()
    rightUpperLeg = auto()
    leftLowerLeg = auto()
    rightLowerLeg = auto()
    leftFoot = auto()
    rightFoot = auto()
    # endregion

    # region spine
    spine = auto()
    chest = auto()
    neck = auto()
    head = auto()
    # endregion

    # region arm
    leftShoulder = auto()
    rightShoulder = auto()
    leftUpperArm = auto()
    rightUpperArm = auto()
    leftLowerArm = auto()
    rightLowerArm = auto()
    leftHand = auto()
    rightHand = auto()
    # endregion

    leftToes = auto()
    rightToes = auto()
    leftEye = auto()
    rightEye = auto()
    jaw = auto()

    # region fingers
    leftThumbProximal = auto()
    leftThumbIntermediate = auto()
    leftThumbDistal = auto()
    leftIndexProximal = auto()
    leftIndexIntermediate = auto()
    leftIndexDistal = auto()
    leftMiddleProximal = auto()
    leftMiddleIntermediate = auto()
    leftMiddleDistal = auto()
    leftRingProximal = auto()
    leftRingIntermediate = auto()
    leftRingDistal = auto()
    leftLittleProximal = auto()
    leftLittleIntermediate = auto()
    leftLittleDistal = auto()
    rightThumbProximal = auto()
    rightThumbIntermediate = auto()
    rightThumbDistal = auto()
    rightIndexProximal = auto()
    rightIndexIntermediate = auto()
    rightIndexDistal = auto()
    rightMiddleProximal = auto()
    rightMiddleIntermediate = auto()
    rightMiddleDistal = auto()
    rightRingProximal = auto()
    rightRingIntermediate = auto()
    rightRingDistal = auto()
    rightLittleProximal = auto()
    rightLittleIntermediate = auto()
    rightLittleDistal = auto()
    # endregion

    upperChest = auto()

    @classmethod
    def from_name(cls, name):
        for e in HumanoidBones:
            if e.name == name:
                return e
        raise ValueError(f'{name} not found')


SPINE = [
    HumanoidBones.hips,
    HumanoidBones.spine,
    HumanoidBones.chest,
    HumanoidBones.upperChest,
    HumanoidBones.neck,
]

HEAD = [
    HumanoidBones.head,
    HumanoidBones.leftEye,
    HumanoidBones.rightEye,
    HumanoidBones.jaw,
]

LEGS = [
    HumanoidBones.leftUpperLeg,
    HumanoidBones.leftLowerArm,
    HumanoidBones.leftFoot,
    HumanoidBones.leftToes,
    HumanoidBones.rightUpperLeg,
    HumanoidBones.rightLowerArm,
    HumanoidBones.rightFoot,
    HumanoidBones.rightToes,
]

ARMS = [
    HumanoidBones.leftUpperArm,
    HumanoidBones.leftLowerArm,
    HumanoidBones.leftHand,
    HumanoidBones.rightUpperArm,
    HumanoidBones.rightLowerArm,
    HumanoidBones.rightHand,
]

LEFT_FINGERS = [
    HumanoidBones.leftThumbProximal,
    HumanoidBones.leftThumbIntermediate,
    HumanoidBones.leftThumbDistal,
    HumanoidBones.leftIndexProximal,
    HumanoidBones.leftIndexIntermediate,
    HumanoidBones.leftIndexDistal,
    HumanoidBones.leftMiddleProximal,
    HumanoidBones.leftMiddleIntermediate,
    HumanoidBones.leftMiddleDistal,
    HumanoidBones.leftRingProximal,
    HumanoidBones.leftRingIntermediate,
    HumanoidBones.leftRingDistal,
    HumanoidBones.leftLittleProximal,
    HumanoidBones.leftLittleIntermediate,
    HumanoidBones.leftLittleDistal,
]

RIGHT_FINGERS = [
    HumanoidBones.rightThumbProximal,
    HumanoidBones.rightThumbIntermediate,
    HumanoidBones.rightThumbDistal,
    HumanoidBones.rightIndexProximal,
    HumanoidBones.rightIndexIntermediate,
    HumanoidBones.rightIndexDistal,
    HumanoidBones.rightMiddleProximal,
    HumanoidBones.rightMiddleIntermediate,
    HumanoidBones.rightMiddleDistal,
    HumanoidBones.rightRingProximal,
    HumanoidBones.rightRingIntermediate,
    HumanoidBones.rightRingDistal,
    HumanoidBones.rightLittleProximal,
    HumanoidBones.rightLittleIntermediate,
    HumanoidBones.rightLittleDistal,
]
