# -*- coding: utf-8 -*-
"""
Created on Fri Jan 15 18:16:01 2021

@author: AsteriskAmpersand
"""

try:
    from .. import construct_plugin as C
except:
    #import construct as C
    pass

Position = lambda x,y,: C.Struct(
                    "raw_x" / x,
                    "raw_y" / x,
                    "raw_z" / x,
                    "x" / C.Computed(C.this.raw_x/y),
                    "y" / C.Computed(C.this.raw_y/y),
                    "z" / C.Computed(C.this.raw_z/y),
                    )  

BytePositionU =  Position(C.Int8sl,0x7F)
ShortPositionU = Position(C.Int16sl,0x7FFF)
FloatPositionU = Position(C.Float32l,1)
BytePositionR =  Position(C.Int8sl,1)
ShortPositionR = Position(C.Int16sl,1)
FloatPositionR = Position(C.Float32l,1)
VPosition = lambda x,y: [(C.Pass,C.Pass),
                            (BytePositionU,BytePositionR),
                            (ShortPositionU,ShortPositionR),
                            (FloatPositionU,FloatPositionR)][x][y]


Normal = lambda x,y,w: C.Struct(
                    "raw_x" / x,
                    "raw_y" / x,
                    "raw_z" / x,
                    "w" / w,
                    "x" / C.Computed(C.this.raw_x/y),
                    "y" / C.Computed(C.this.raw_y/y),
                    "z" / C.Computed(C.this.raw_z/y),
                    )  

ByteNormalU = Normal(C.Int8sl,0x7F,C.Int8sl)
ShortNormalU = Normal(C.Int16sl,0x7FFF,C.Int16sl)
FloatNormalU = Normal(C.Float32l,1,C.Pass)
ByteNormalR = Normal(C.Int8sl,1,C.Int8sl)
ShortNormalR = Normal(C.Int16sl,1,C.Int16sl)
FloatNormalR = Normal(C.Float32l,1,C.Pass)
VNormal = lambda x,y: [(C.Pass,C.Pass),
                            (ByteNormalU,ByteNormalR),
                            (ShortNormalU,ShortNormalR),
                            (FloatNormalU,FloatNormalR)][x][y]

Weight = lambda typing,normalizer: C.Struct(
                    "raw_weight" / typing,
                    "weight" / C.Computed(C.this.raw_weight/normalizer),
                    )  
ByteWeightU = Weight(C.Int8ul,0x80)
ShortWeightU = Weight(C.Int16ul,0x8000)
FloatWeightU = Weight(C.Float32l,1)
VWeight = lambda x: [C.Pass,
                        ByteWeightU,
                        ShortWeightU,
                        FloatWeightU,][x]

rgb565 = C.BitStruct(
    "raw_r" / C.BitsInteger(5),
    "raw_g" / C.BitsInteger(6),
    "raw_b" / C.BitsInteger(5),
    "r" / C.Computed(C.this.raw_r/(2**5-1)),
    "g" / C.Computed(C.this.raw_g/(2**6-1)),
    "b" / C.Computed(C.this.raw_b/(2**5-1)),
    "a" / C.Computed(1.0),
    )
rgba5 = C.BitStruct(
    "raw_r" / C.BitsInteger(5),
    "raw_g" / C.BitsInteger(5),
    "raw_b" / C.BitsInteger(5),
    "raw_a" / C.BitsInteger(1),
    "r" / C.Computed(C.this.raw_r/(2**5-1)),
    "g" / C.Computed(C.this.raw_g/(2**5-1)),
    "b" / C.Computed(C.this.raw_b/(2**5-1)),
    "a" / C.Computed(C.this.raw_a*1.0),
    )
rgba4 = C.BitStruct(
    "raw_r" / C.BitsInteger(4),
    "raw_g" / C.BitsInteger(4),
    "raw_b" / C.BitsInteger(4),
    "raw_a" / C.BitsInteger(4),
    "r" / C.Computed(C.this.raw_r/(2**4-1)),
    "g" / C.Computed(C.this.raw_g/(2**4-1)),
    "b" / C.Computed(C.this.raw_b/(2**4-1)),
    "a" / C.Computed(C.this.raw_a/(2**4-1)),
    )
rgba8 = C.BitStruct(
    "raw_r" / C.BitsInteger(8),
    "raw_g" / C.BitsInteger(8),
    "raw_b" / C.BitsInteger(8),
    "raw_a" / C.BitsInteger(8),
    "r" / C.Computed(C.this.raw_r/(2**8-1)),
    "g" / C.Computed(C.this.raw_g/(2**8-1)),
    "b" / C.Computed(C.this.raw_b/(2**8-1)),
    "a" / C.Computed(C.this.raw_a/(2**8-1)),
    )

VRGB = lambda w,x: [C.Pass,[rgb565,rgba5,rgba4,rgba8][x]][w]

UV = lambda typing,normalizer,pad: C.Struct(
                    "raw_u" / typing,
                    "raw_v" / typing,
                    "w" / pad,
                    "u" / C.Computed(C.this.raw_u/normalizer),
                    "v" / C.Computed(1-C.this.raw_v/normalizer),
                    )  
ByteUVU = UV(C.Int8ul,0x80,C.Int16ul)
ShortUVU = UV(C.Int16ul,0x8000,C.Pass)
FloatUVU = UV(C.Float32l,1,C.Pass)
ByteUVR = UV(C.Int8ul,1,C.Int16ul)
ShortUVR = UV(C.Int16ul,1,C.Pass)
FloatUVR = UV(C.Float32l,1,C.Pass)
VUV = lambda x,y: [(C.Pass,C.Pass),
                            (ByteUVU,ByteUVR),
                            (ShortUVU,ShortUVR),
                            (FloatUVU,FloatUVR)][x][y]


Index = lambda x: C.Struct("index" / x)
ByteIndex = Index(C.Int8ul)
ShortIndex = Index(C.Int16ul)
IntIndex = Index(C.Int32ul)
VIndex = lambda x: [C.Pass,ByteIndex,ShortIndex,IntIndex][x]