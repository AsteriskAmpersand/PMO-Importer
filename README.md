![Chomp!](https://cdn.discordapp.com/attachments/521438182311460879/800550381054328862/PMOImporter.fw.png)

# Blender MHFU PMO Importer
Developed partially from documentation by Seth VanHeulen and original research by myself (\*&).  
Thanks to IncognitoMan for his assistance in the logistics side of reversing the format.  
Seth research can be found here: https://gitlab.com/svanheulen/mhff

# Format Documentation

PMO (speculatively "Portable Model" or "Portable Media Object") files are broken into sections. The sections must be read sequentially, header declarations are missing buffer sizes and counts in most cases. Additionally the last section is a semi-imperative format which requires parsing control codes.

PMO contains model geometry and material data. Skeleton data is on a contiguous file, material data interfaces with a texture format that's also contiguous to the model file.+

Each major section is padded to int64 alignment this fact will be omitted from here on.

- [Format Documentation](#format-documentation)
  * [Header](#header)
  * [Mesh Headers](#mesh-headers)
  * [Tristrip Headers](#tristrip-headers)
  * [Material Remap](#material-remap)
  * [Bone Data](#bone-data)
  * [Bone Data Parsing Example](#bone-data-parsing-example)
      - [Sample Tristrip](#sample-tristrip)
      - [Sample Bone Data](#sample-bone-data)
      - [Sample Vertex](#sample-vertex)
    + [Parsing Example](#parsing-example)
      - [Step 0](#step-0)
      - [Step 1](#step-1)
      - [Step 1](#step-1-1)
      - [Step 2](#step-2)
      - [Step 3](#step-3)
  * [Material Data](#material-data)
  * [Mesh Data](#mesh-data)
  * [Semi-Imperative](#semi-imperative)
    + [BASE](#base)
    + [START](#start)
    + [IADDR](#iaddr)
    + [VADDR](#vaddr)
    + [VTYPE](#vtype)
    + [FACE](#face)
    + [PRIM](#prim)
    + [RET](#ret)
  * [Reading the Mesh Buffer](#reading-the-mesh-buffer)

## Header 
The structure begins with a header:
```
struct Header{
    char pmo[4];//null-terminated string consisting of "pmo\00".
    char ver[4];//null-terminated string consisting of "1.0\00"
    uint fileSize;
    float clippingDistance;//max of all dimensions on the scale
    float scale[3];
    ushort meshCount;
    ushort materialCount;
    uint meshHeaderOffset;
    uint tristripHeaderOffset;
    uint materialRemapOffset;
    uint boneDataOffset;
    uint materialDataOffset;
    uint meshDataOffset;
};
```
The header contains scene wide data (scale and clipping distance), the offsets to each section and the counts necessary to read the mesh headers and the material data.   
  
Because of data sufficiency:
1. To parse the tristrips headers it's necessary to parse the mesh headers. 
2. To parse the material remap it's necessary to parse the tristrips headers.
3. To parse the bone data it's necessary to parse the tristrips headers. 
4. To parse mesh data it's necessary to parse the tristrips headers. 


## Mesh Headers

```
struct MeshHeader{
    float uvScale[2];
    ubyte unkn1[8];
    ushort materialCount;
    ushort cumulativeMaterialCount;
    ushort tristripCount;
    ushort cumulativeTristripCount;
}
```
UV Scale multiplies the uv values of all vertices within the mesh. The material count is the number of remap entries corresponding to the mesh, each tristrip declares a material index offset that must be added to the cumulative material count of the mesh it belongs to. The tristrip count is the number of tristrips corresponding to the mesh.

To be able to parse the Material Remap section it's necessary to calculate the sum of material counts (alternatively add the cumulative to the count on the last mesh).

## Tristrip Headers

```
struct TristripHeader{
    ubyte materialOffset;
    byte weightCount;
    short cumulativeWeightCount;
    uint meshOffset;
    uint vertexOffset;
    uint indexOffset;
};
```
The material offset as indicated before is added to the cumulativeMaterialCount of the mesh the tristrip belongs to, this is the entry in the material remap array which corresponds to the tristrip.  
  
The weightCount represents the number of entries on the Bone Data Array the tristrips consumes. To be able to parse the Bone Data Array it's necessary to calculate the sum of all weightCount (alternatively add the weightCount to the cumulativeWeightCount on the last tristrip header).  
  
The vertex offset is the offset from the start of the Mesh Data section to the vertex data for the tristrip vertex data. Parsing the section however requires reading the semi-imperative section of the mesh data as vertex buffer structure is contained there, furthermore the face data is also required to calculate the vertex count.

The index offset is the offset from the start of the Mesh Data section to the face index metadata for the tristrip face data. Parsing the section however requires reading the semi-imperative section of the mesh data as the index buffer structure is contained there.

Each mesh header declares how many tristrips (and thus tristrip headers) it contains.

## Material Remap
```
struct MaterialRemapIndex{
    byte materialIndex;
};
```
Remaps tristrip material indices to an index in the material data array.  
  
Different tristrips on different meshes using the same material will have different material indices, the remap section maps them back to the same material. 

There are as many entries as the sum of materialCount on mesh headers.

## Bone Data
```
struct BoneData{
    byte index;
    byte boneIndex;
};
```
The Bone Data represents the bone indices that each tristrip pairs with it's weight data to determine the target of each weight on the vertex buffer.  
  
The bone data structure requires somewhat complicated parsing. An auxiliary structure is required which keeps track of the current active indexes. When the next tristrip is parsed, as many as weightCount entries are read from this array. For each entry the auxiliary structure replaces it's index-th entry with the boneIndex in the entry being parsed.

## Bone Data Parsing Example

For example, given the following example structures:

#### Sample Tristrip
| Tristrip Index  | Tristrip Bone Count |
| ------------- | ------------- |
| 0  | 3  |
| 1  | 2  |
| 2  | 0  |
| 3  | 1  |

#### Sample Bone Data
| Auxiliary Index  | Bone Index |
| ------------- | ------------- |
| 0  | 2  |
| 1  | 3  |
| 2  | 0  |
| 1  | 1  |
| 2  | 4  |
| 1  | 3  |

#### Sample Vertex
| Vertex Owner Tristrip | Weight 0 | Weight 1 | Weight 2 |
| ------------- | ------ | ------ | ------ |
| 0  | .2  | .3  | .5  |
| 1  | .3  | .45 | .25 |
| 2  | .1  | .2  | .7  |
| 3  | .7  | .18 | .12 |

### Parsing Example
#### Step 0
We initialize the auxiliary struct
| Current Tristrip | Bone Index 0 | Bone Index 1 | Bone Index 2 | ... |
| ------------- | ------ | ------ | ------ | ------ |
| -1  | -1  | -1  | -1  | ... |

#### Step 1
Parsing the first tristrip we get there are 3 Bone Data entries to parse
| Auxiliary Index  | Bone Index |
| ------------- | ------------- |
| 0  | 2  |
| 1  | 3  |
| 2  | 0  |

We update the auxiliary buffer  
| Current Tristrip | Bone Index 0 | Bone Index 1 | Bone Index 2 | ... |
| ------------- | ------ | ------ | ------ | ------ |
| 0  | 2  | 3  | 0 | ... |

Parsing the vertex on the tristrip

| Vertex Owner Tristrip | Weight 0 | Weight 1 | Weight 2 |
| ------------- | ------ | ------ | ------ |
| 0  | .2  | .3  | .5  |

We now know that for this vertex:
| Bone | Weight | 
| ---- | ------ | 
| 2  | .2  |
| 3  | .3  |
| 0  | .5  |

#### Step 1
Parsing the second tristrip we get there are 2 Bone Data entries to parse
| Auxiliary Index  | Bone Index |
| ------------- | ------------- |
| 1  | 1  |
| 2  | 4  |

We update the auxiliary buffer  
| Current Tristrip | Bone Index 0 | Bone Index 1 | Bone Index 2 | ... |
| ------------- | ------ | ------ | ------ | ------ |
| 1  | 2  | 1  | 4 | ... |

Parsing the vertex on the tristrip

| Vertex Owner Tristrip | Weight 0 | Weight 1 | Weight 2 |
| ------------- | ------ | ------ | ------ |
| 1  | .3  | .45 | .25 |

We now know that for this vertex:
| Bone | Weight | 
| ---- | ------ | 
| 2  | .3  |
| 1  | .45  |
| 4  | .25  |

#### Step 2
Parsing the second tristrip we get there are 0 Bone Data entries to parse

We don't update the auxiliary buffer  
| Current Tristrip | Bone Index 0 | Bone Index 1 | Bone Index 2 | ... |
| ------------- | ------ | ------ | ------ | ------ |
| 2  | 2  | 1  | 4 | ... |

Parsing the vertex on the tristrip

| Vertex Owner Tristrip | Weight 0 | Weight 1 | Weight 2 |
| ------------- | ------ | ------ | ------ |
| 1  | .1  | .2  | .7  |

We now know that for this vertex:
| Bone | Weight | 
| ---- | ------ | 
| 2  | .1  |
| 1  | .2  |
| 4  | .7  |

#### Step 3
Parsing the second tristrip we get there is 1 Bone Data entries to parse
| Auxiliary Index  | Bone Index |
| ------------- | ------------- |
| 1  | 3  |

We update the auxiliary buffer  
| Current Tristrip | Bone Index 0 | Bone Index 1 | Bone Index 2 | ... |
| ------------- | ------ | ------ | ------ | ------ |
| 1  | 2  | 3  | 4 | ... |

Parsing the vertex on the tristrip

| Vertex Owner Tristrip | Weight 0 | Weight 1 | Weight 2 |
| ------------- | ------ | ------ | ------ |
| 1  | .7  | .18 | .12 |

We now know that for this vertex:
| Bone | Weight | 
| ---- | ------ | 
| 2  | .7  |
| 3  | .18  |
| 4  | .12  |

## Material Data
```
struct MaterialContent{
    byte rgba[4];
    byte rgba2[4];
    int textureIndex;
    byte unkn[4];
};
```
The Material Data represents a very rudimentary material format. It consists of two rgba channels (the first is normally just set to be at full opacity with no colour filtering) and the second is more rarely used. The textureIndex is the index of the texture in the texture file. Some unpacking tools have an imprecision where textures are indexed in the order they are found. This order will match the way indices appear on the material array, not the textureID itself, which requires some care in the parsing to account for this cases.

## Mesh Data
The mesh data section contains a semi-imperative section which declares buffer structures which are used to read the vertex, index and face data that's also contained on the mesh data section. This sections are stored:
1. Semi-imperative Section
1. Vertex Data
1. Index Data
1. Face Data  
  
With padding to bring each section to int64 alignment at the end of each section.

## Semi-Imperative 
The semi-imperative section is read on Int32 strides. The top 8 bits determine the data contained on the field.
| Signature | Type | Action to Parse | Description
| ------------- | ------ | ------ | ------ |
| 0x00  | NOP  | Pass | Does Nothing |
| 0x14  | BASE  | Set Base Address | Marks the Base Pointer other Offsets apply to |
| 0x10  | START  | Pass/Validate | Marks Start of Useable Data |
| 0x02  | IADDR  | Set Index Address | Stores the offset to the Face Index Data |
| 0x01  | VADDR  | Set Vertex Address | Stores the offset to the Vertex Data |
| 0x12  | VTYPE  | Set Vertex Buffer  | Defines the vertex buffer used by the tristrip |
| 0x9B  | FACE   | Set Face Order     | Defines tristrip faces orientation |
| 0x04  | PRIM   | Set Index Count/Buffer | Defines the index buffer and face count used by the tristrip |
| 0x0B  | RET    | Return | Marks the end of the section |

### BASE
Set the base address to the current position (ftell() - 4 if already advanced over the int32).

### START
Do nothing.

### IADDR
The lower 24 bits contain the offset from the base to the start of the indexes section.

### VADDR
The lower 24 bits contain the offset from the base to the start of the vertices section.

### VTYPE
The entire vertex structure declaration fits within the int32 with the VTYPE signature on the higher bits.
```
struct VertexType{
    bits	uvClass[2];
    bits	colorClass[2];
    bits	colorUse[1];
    bits	normalClass[2];
    bits	positionClass[2];
    bits	weightClass[2];
    bits	indexClass[2];
    bits	padding1[1];
    bits	weightCount[4];
    bits	morphClass[3];
    bits	padding2[2];
    bits	bypass[1];
    bits	VTYPE[8];
};
```
xClass variables (with the exception of Morph Class which isn't used in MHFU) determine the binary type of the data:
| Class Value | Data Type |
| ----------- | --------- |
| 0 | Type not present |
| 1 | Byte |
| 2 | Short |
| 3 | Float |

The index class operates like vertex buffer classes, determining the index datatype:

| Class Value | Data Type |
| ----------- | --------- |
| 0 | Type not present |
| 1 | Byte |
| 2 | Short |
| 3 | Int32 |

The exception is the color class. Whether a color layer is present is determined by Color Use:
| Color Class | Data Type |
| ----------- | --------- |
| 0 | rgb565 |
| 1 | rgba5 |
| 2 | rgba4 |
| 3 | rgba8 |

The bypass bit determines if Position, Normals and UV Coordinates should NOT be normalized.

Normalization is done thus for non-colour types:

| Signed | Size | Normalization |
| ---- | ----|  --------- |
| Yes | Byte | 0x7F |
| Yes | Short | 0x7FFF |
| Yes | Float | 1.0 |
| No | Byte | 0x80 |
| No | Short | 0x8000 |
| No | Float | 1.0 |

The sign of each type is thus:

| Type | Signing |
| ---- | ------- |
| Position | Signed |
| Normal | Signed |
| UV | Unsigned
| Weight | Unsigned |

The vertex buffer has a specific ordering additionally the fields are followed by padding depending on the type of each field given by:
| Type | End of Section Alignment |
| ---- | ---------------------- |
| Weight | Int16 |
| UV | Int32 |
| Colour | None |
| Normal | Int32 |
| Position | None |
Note that the vertex buffer padding and thus size doesn't depend on the start of each vertex, padding is calculated once when building the buffer not when reading into it.

### FACE
The lowest bit determines if the tristrip faces should be flipped after reading.

### PRIM
The PRIM determines 
```
struct VertexType{
    bits	indexCount[16];
    bits	tristripType[3];
    bits	padding[5];
    bits	PRIM[8];
};
```
The tristrip type determines if it's a tristrip or an array of faces. For example [0,1,2,3,4,5] is  4 faces in tristrip mode or just 2 in independent face mode.

| Value | Mode |
| ---- | ---------------------- |
| 3 | Individual Faces |
| 4 | Tristrip Mode |

It also lists how many face indices are stored at the offset.

### RET
Determines the end of the section. Is followed by padding before the vertex buffer.

## Reading the Mesh Buffer
To read the mesh buffer, for each mesh and for every tristrip on the mesh one adds the tristrip meshOffset to the meshDataOffset to arrive at the semi-imperative section. Parsing this provides the indicesOffset and the vertexOffset from the base found on this section. A semi-imperative block can have multiple index sets, formally speaking each of those consists of a tristrip and the tristrip headers are actually "groupings of tristrips" that share the same vertex buffers, weights and materials. The index offset is the start of the section of those listings of faces. To get the vertex count one must parse all of the faces and find the max index found in them. The vertex count will be this value + 1. The vertex buffer is then seeked based on the vertex offset and the base and parsed based on the vertex buffer structure found on the semi-imperative section.  

Face indexing is on a per-tristrip basis.

```
def readMeshData(pmo):
    def info(op):
        pass
    index_counts = []
    while True:
        command = array.array('I', pmo.read(4))[0]
        command_type = command >> 24
        # NOP - No Operation
        if command_type == 0x00: info("NOP")
        # ??? - Origin Address (BASE)
        elif command_type == 0x14: info ("ORI_BASE")
        # BASE - Base Address Register
        elif command_type == 0x10: 
			info("BASE")
			base = pmo.tell()-4
        # IADDR - Index Address (BASE)
        elif command_type == 0x02:
            info("IADDR")
            index_address = base + (command & 0xffffff)        
        # VADDR - Vertex Address (BASE)
        elif command_type == 0x01:
            info("VADDR")
            vertex_address = base + (command & 0xffffff)
        # VTYPE - Vertex Type
        elif command_type == 0x12:
            info("VTYPE")
            index_buffer, vertex_buffer = vertexType(command)
        # FFACE - Front Face Culling Order
        elif command_type == 0x9b:
            info ("FACE_CULL")
            face_order = command & 1
            if command & 0xfffffE:
                print (bin(command & 0xfffffE))
        # PRIM - Primitive Kick
        elif command_type == 0x04:
            info("PRIM")
            index_counts.append(bitarray(command,primitiveTypeMap))
        # RET - Return from Call
        elif command_type == 0x0b:
            info("RET")
            break
        # ??? - Offset Address (BASE)
        elif command_type == 0x13: info("OFF_BASE")
        else:raise ValueError('Unknown GE command: 0x{:02X}'.format(command_type))
    faces = parseFaces(pmo,index_address,index_buffer,index_counts,face_order,info)
    vertices = parseVertices(pmo,vertex_address,vertex_buffer,max(map(max,faces))+1,info)
```

Using the following as auxiliary functions:
```
def bitarray(op,startStops):
    results = {}
    for key,(start,end) in startStops.items():
        results[key] = (op >> start) & (2**(end-start)-1)
    return results

vertexTypeMap = {
    "uvClass" : (0,2),        
    "colorClass" : (2,4),
    "colorUse" : (4,5),
    "normalClass" : (5,7),
    "positionClass" : (7,9),
    "weightClass" : (9,11),
    "indexClass" : (11,13),    
    "padding1" : (13,14),    
    "weightCount" : (14,18),
    "morphClass" : (18,21),    
    "padding2" : (21,23),    
    "bypass" : (23,24),
    "operator" : (24,32),
    }

alignment = C.Struct(
        "pos" / C.Tell,
        "padding" / C.Padding((-C.this.pos)%4)
    )

def weightSpan(count,classing):
    wspan = [0,1,2,4][classing]
    stride = wspan*count
    return ((-stride) % 2)

def vertexType(command):
    result = bitarray(command,vertexTypeMap)
    #print(result)
    if result["morphClass"]: raise ValueError("Morph Class not implemented")
    VertexBuffer = C.Struct(
                            "weight" / VWeight(result["weightClass"])[result["weightCount"]+1],   
                            "padding" / C.Int8ul[weightSpan(result["weightCount"]+1,result["weightClass"])],
                            "uv" / VUV(result["uvClass"],result["bypass"]),
                            "colour" / VRGB(result["colorUse"],result["colorClass"]),
                            "normal" / VNormal(result["normalClass"],result["bypass"]),
                            "position" / VPosition(result["positionClass"],result["bypass"]),
        )
    IndexBuffer = VIndex(result["indexClass"])
    return IndexBuffer, VertexBuffer

primitiveTypeMap = {
    "indexCount" : (0,16),
    "primitiveType" : (16,19),
    "unknown" : (19,24),
    "operator" : (24,32),
    }  

def parseFaces(pmo,index_address,index_buffer,index_counts,face_order,info):
    faces = []
    pmo.seek(index_address)
    for indexData in index_counts:
        count = indexData["indexCount"]
        primitive_type = indexData["primitiveType"]
        index = [ix.index for ix in C.Struct("index" / index_buffer[count]).parse_stream(pmo).index]
        #if face_order: index = list(reversed(index))          
        r = range(count - 2)
        if primitive_type == 3:
            r = range(0, count, 3)
        elif primitive_type != 4:
            ValueError('Unsupported primative type: 0x{:02X}'.format(primitive_type))            
        signum = 0 + face_order
        for i in r:
            face = (index[i+signum],index[i+1-signum], index[i+2])
            signum = (signum + 1)%2     
            faces.append(face)
    return faces

def parseVertices(pmo, vertex_address,vertexBuffer,index,info):
    vertices = []
    pmo.seek(vertex_address)
    for i in range(index):        
        vertex = vertexBuffer.parse_stream(pmo)
        vertices.append(vertex)
    return vertices
```
