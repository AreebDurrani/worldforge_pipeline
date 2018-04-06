# Copyright (C) 2010 Brett Hartshorn
# Copyright (C) 2014 Anisim Kalugin
# Copyright (C) 2014 Erik Ogenvik
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''
Tool depends on Blender to Ogre exporter http://code.google.com/p/blender2ogre
'''
import math

bl_info = {
    'name': 'Pipeline Tools',
    'category': 'WorldForge',
    'author': 'anisimkalugin.com, erik@ogenvik.org',
    'version': (0, 0, 1),
    'blender': (2, 71, 0),
    'description': 'Worldforge Pipeline Tools',
    'warning': '',
    'wiki_url': ''
}

import bpy, shutil, subprocess, tempfile, fnmatch, traceback
from bpy.types import Operator
# from bpy.props import FloatVectorProperty
from bpy_extras.object_utils import AddObjectHelper


# from mathutils import Vector
class RigAnimationUtilities:
    def __init__(self):
        self.DEBUG = False

    def clean_vertex_groups(self, context):
        sel = bpy.context.selected_objects

        for ob in sel:
            vertex_groups = ob.vertex_groups
            if len(ob.modifiers) > 0:
                rig = ob.modifiers[-1].object  # get the rig
                bones = rig.data.bones

                if self.DEBUG:
                    print(ob.name)
                    print(rig.name)
                    print(bones)
                # get data
                vgrp_list = [grp.name for grp in ob.vertex_groups]
                bone_list = [bone.name for bone in rig.data.bones if bone.use_deform]

                # compare lists
                del_group = [itm for itm in vgrp_list if itm not in bone_list]
                mkv_groups = [itm for itm in bone_list if itm not in vgrp_list]

                # add vertex groups based on armatures deformable bones
                [ob.vertex_groups.new(name) for name in mkv_groups]

                # remove groups that are not part of the current armatures deformable bones
                # list comprehension code may be a bit too long
                [ob.vertex_groups.remove(ob.vertex_groups[ob.vertex_groups.find(group)]) for group in del_group]
                return True

        return False


class OgreMaterialManager:
    '''Worldforge material management utilites'''

    def __init__(self):
        self.DEBUG = False

    def get_base_name(self, path):
        bad_names_l = ['//..']
        tkns = path.split(os.sep)[1:-1]
        seps = []
        for i in range(len(tkns)):
            itm = tkns[i]
            if not itm in bad_names_l:
                seps.append(itm)
        if seps == []:
            return 'blender file name'
        # bpy.path.display_name_from_filepath(bpy.data.filepath)
        return seps[-1]

    def open_ogre_materials(self, context):
        '''opens ogre.material based on the texture file path'''
        sel = bpy.context.selected_objects
        tmp_txt = bpy.data.texts.new('{tmp}')  # hacky shit

        for ob in sel:
            for slot in ob.material_slots:
                mat = slot.material

                if mat.active_texture == None:
                    continue

                image_path = mat.active_texture.image.filepath
                ogre_mat_file = bpy.path.abspath(image_path)[:-5] + 'ogre.material'
                if os.path.isfile(ogre_mat_file):
                    txt_datablock = bpy.data.texts

                    filepaths = [itm.filepath for itm in bpy.data.texts]

                    for dat in filepaths:
                        exists = ogre_mat_file in filepaths
                        if exists == False:
                            bpy.ops.text.open(filepath=ogre_mat_file)

                        if self.DEBUG == True:
                            print('---- debug statements ----')
                            print(image_path)
                            print(ogre_mat_file)
                            print(filepaths)
                            print(exists)
        bpy.data.texts.remove(tmp_txt)

    #
    def get_ogre_mat_name(self, relative_path):
        '''retrieves ogre.material based on the current image'''
        # ogre_mat_file = relative_path[:-5] + 'ogre.material'
        ogre_mat_file = bpy.path.abspath(relative_path)[:-5] + 'ogre.material'
        # ogre_mat_file = testPath[:-5] + 'ogre.material'
        matNames = []
        if os.path.isfile(ogre_mat_file):
            f = open(ogre_mat_file, 'r')
            for line in f:
                if line[:8] == 'material':
                    matNames.append(line.split(' ')[1])
            f.close()

        return matNames

    def write_to_text_datablock(self, b_list):
        '''writes out the list to a ogre mat textblock'''
        ogre_tdb = self.get_text_datablock()
        ogre_tdb.write('--------------\n')
        for itm in b_list:
            ogre_tdb.write('%s \n' % itm)

    def get_text_datablock(self, tdb='ogre_mats'):
        '''gets/creates a text data block (tdb)'''
        txt_datablock = bpy.data.texts.find(tdb)
        if txt_datablock == -1:
            return bpy.data.texts.new(tdb)
        return bpy.data.texts[tdb]

    def wf_fix_materials(self, context):
        '''tries to fix material names based on ogre.material files'''
        sel = bpy.context.selected_objects
        for ob in sel:
            for slot in ob.material_slots:
                mat = slot.material

                if mat.active_texture == None:
                    continue

                image_path = mat.active_texture.image.filepath  # = 'asdfsadf' manipulate the file path

                # image_names_list = self.get_ogre_mat_name( image_path )
                image_names_list = [itm for itm in self.get_ogre_mat_name(image_path) if itm[-12:] != 'shadowcaster']
                if image_names_list != []:
                    if len(image_names_list) > 1:
                        self.write_to_text_datablock(image_names_list)
                    else:
                        mat.name = image_names_list[0]

                image_type = (bpy.path.display_name(image_path)).lower()
                asset_name = self.get_base_name(image_path)
                image_name = '_'.join([asset_name, image_type])

                mat.active_texture.name = image_name
                mat.active_texture.image.name = image_name

                if self.DEBUG == True:
                    print(image_path)
                    print(image_type)
                    print(asset_name)
                    print(image_name)
                    print(image_names_list)


from xml.sax.saxutils import quoteattr


class SimpleSaxWriter():
    def __init__(self, output, root_tag, root_attrs):
        self.output = output
        self.root_tag = root_tag
        self.indent = 0
        output.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        self.start_tag(root_tag, root_attrs)

    def _out_tag(self, name, attrs, isLeaf):
        # sorted attributes -- don't want attributes output in random order, which is what the XMLGenerator class does
        self.output.write(" " * self.indent)
        self.output.write("<%s" % name)
        sortedNames = sorted(attrs.keys())  # sorted list of attribute names
        for name in sortedNames:
            value = attrs[name]
            # if not of type string,
            if not isinstance(value, str):
                # turn it into a string
                value = str(value)
            self.output.write(" %s=%s" % (name, quoteattr(value)))
        if isLeaf:
            self.output.write("/")
        else:
            self.indent += 4
        self.output.write(">\n")

    def start_tag(self, name, attrs):
        self._out_tag(name, attrs, False)

    def end_tag(self, name):
        self.indent -= 4
        self.output.write(" " * self.indent)
        self.output.write("</%s>\n" % name)

    def leaf_tag(self, name, attrs):
        self._out_tag(name, attrs, True)

    def close(self):
        self.end_tag(self.root_tag)


class RElement(object):
    def appendChild(self, child):
        self.childNodes.append(child)

    def setAttribute(self, name, value):
        self.attributes[name] = value

    def __init__(self, tag):
        self.tagName = tag
        self.childNodes = []
        self.attributes = {}

    def toprettyxml(self, lines, indent):
        s = '<%s ' % self.tagName
        sortedNames = sorted(self.attributes.keys())
        for name in sortedNames:
            value = self.attributes[name]
            if not isinstance(value, str):
                value = str(value)
            s += '%s=%s ' % (name, quoteattr(value))
        if not self.childNodes:
            s += '/>'
            lines.append(('  ' * indent) + s)
        else:
            s += '>'
            lines.append(('  ' * indent) + s)
            indent += 1
            for child in self.childNodes:
                child.toprettyxml(lines, indent)
            indent -= 1
            lines.append(('  ' * indent) + '</%s>' % self.tagName)


class RDocument(object):
    def __init__(self):
        self.documentElement = None
        self.comments = []

    def appendChild(self, root):
        self.documentElement = root

    def addComment(self, text):
        self.comments.append("<!-- {} -->".format(text))

    def createElement(self, tag):
        e = RElement(tag)
        e.document = self
        return e

    def toprettyxml(self):
        indent = 0
        lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        lines += self.comments
        self.documentElement.toprettyxml(lines, indent)
        return '\n'.join(lines)


import os, time, sys, logging
import mathutils


class ReportSingleton(object):
    def __init__(self):
        self.reset()

    def show(self):
        bpy.ops.wm.call_menu(name='MT_mini_report')

    def reset(self):
        self.materials = []
        self.meshes = []
        self.lights = []
        self.cameras = []
        self.armatures = []
        self.armature_animations = []
        self.shape_animations = []
        self.textures = []
        self.vertices = 0
        self.orig_vertices = 0
        self.faces = 0
        self.triangles = 0
        self.warnings = []
        self.errors = []
        self.messages = []
        self.paths = []

    def report(self):
        r = ['Report:']
        ex = ['Extended Report:']
        if self.errors:
            r.append('  ERRORS:')
            for a in self.errors: r.append('    - %s' % a)

        if self.warnings:
            r.append('  WARNINGS:')
            for a in self.warnings: r.append('    - %s' % a)

        if self.messages:
            r.append('  MESSAGES:')
            for a in self.messages: r.append('    - %s' % a)
        if self.paths:
            r.append('  PATHS:')
            for a in self.paths: r.append('    - %s' % a)

        if self.vertices:
            r.append('  Original Vertices: %s' % self.orig_vertices)
            r.append('  Exported Vertices: %s' % self.vertices)
            r.append('  Original Faces: %s' % self.faces)
            r.append('  Exported Triangles: %s' % self.triangles)
            ## TODO report file sizes, meshes and textures

        for tag in 'meshes lights cameras armatures armature_animations shape_animations materials textures'.split():
            attr = getattr(self, tag)
            if attr:
                name = tag.replace('_', ' ').upper()
                r.append('  %s: %s' % (name, len(attr)))
                if attr:
                    ex.append('  %s:' % name)
                    for a in attr: ex.append('    . %s' % a)

        txt = '\n'.join(r)
        ex = '\n'.join(ex)  # console only - extended report
        print('_' * 80)
        print(txt)
        print(ex)
        print('_' * 80)
        return txt


Report = ReportSingleton()

invalid_chars = '\/:*?"<>|'


def clean_object_name(value):
    global invalid_chars
    for invalid_char in invalid_chars:
        value = value.replace(invalid_char, '_')
    value = value.replace(' ', '_')
    return value


def swap(vec):
    if len(vec) == 3:
        return mathutils.Vector([vec.x, vec.z, -vec.y])
    elif len(vec) == 4:
        return mathutils.Quaternion([vec.w, vec.x, vec.z, -vec.y])


def timer_diff_str(start):
    return "%0.2f" % (time.time() - start)


def dot_mesh(target_file):
    """
    export the vertices of an object into a .mesh file

    ob: the blender object
    target_file: the path to save the .mesh file to. path MUST exist
    """

    objects = bpy.context.selected_objects

    if len(objects) == 0:
        return

    multimeshes = len(objects) > 1

    arm = objects[0].find_armature()

    for object in objects:
        if arm != object.find_armature():
            logging.error("Multiple meshes selected, but armatures differ.")
            return

    obj_name = target_file

    start = time.time()

    if logging:
        print('      - Generating:', '%s.mesh.xml' % obj_name)

    try:
        with open(target_file, 'w') as f:
            f.flush()
    except Exception as e:
        logging.error("Invalid mesh object name: " + obj_name)
        return

    with open(target_file, 'w') as f:
        doc = SimpleSaxWriter(f, 'mesh', {})

        submeshes = []
        for ob in objects:

            submesh = {}

            # blender per default does not calculate these. when querying the quads/tris
            # of the object blender would crash if calc_tessface was not updated
            ob.data.update(calc_tessface=True)

            Report.meshes.append(obj_name)
            Report.faces += len(ob.data.tessfaces)
            Report.orig_vertices += len(ob.data.vertices)

            #Copy object so we can alter it
            copy = ob.copy()
            rem = []
            for mod in copy.modifiers:  # remove armature and array modifiers before collapse
                if mod.type in 'ARMATURE ARRAY'.split(): rem.append(mod)
            for mod in rem: copy.modifiers.remove(mod)
            #Check if there already are triangles, or if we need to apply the TRIANGULATE modifier.
            needs_triangulate = False
            for poly in copy.data.polygons:
                if poly.loop_total > 4:
                    needs_triangulate = True
                    break

            if needs_triangulate:
                #Check if there's already a triangulation modifier, otherwise add one
                for mod in copy.modifiers:
                    if mod.type == 'TRIANGULATE':
                        needs_triangulate = False
                        break

            if needs_triangulate:
                copy.modifiers.new("Triangulate", "TRIANGULATE")

            # bake mesh
            mesh = copy.to_mesh(bpy.context.scene, True, "PREVIEW")  # collapse

            mesh.calc_tangents()

            submesh['mesh'] = mesh
            submesh['ob'] = ob
            submesh['copy'] = copy

            submeshes.append(submesh)

        # Very ugly, have to replace number of vertices later
        doc.start_tag('sharedgeometry', {'vertexcount': '__TO_BE_REPLACED_VERTEX_COUNT__'})

        if logging:
            print('      - Writing shared geometry')

        first_mesh = submeshes[0]['mesh']
        doc.start_tag('vertexbuffer', {
            'positions': 'true',
            'normals': 'true',
            'colours_diffuse': str(bool(first_mesh.vertex_colors)),
            'texture_coords': '%s' % len(first_mesh.uv_textures) if first_mesh.uv_textures.active else '0',
            'tangents': 'true',
            'tangent_dimensions': '3',
            'binormals': 'true'
        })

        shared_vertices = {}
        vertex_groups = {}
        _remap_verts_ = []
        numverts = 0

        for submesh in submeshes:
            mesh = submesh['mesh']
            ob = submesh['ob']
            # Vertex colors, note that you can define a vertex color
            # material. see 'vertex_color_materials' below!
            vcolors = None
            vcolors_alpha = None
            if len(mesh.tessface_vertex_colors):
                vcolors = mesh.tessface_vertex_colors[0]
                for bloc in mesh.tessface_vertex_colors:
                    if bloc.name.lower().startswith('alpha'):
                        vcolors_alpha = bloc
                        break

            # Materials
            # saves tuples of material name and material obj (or None)
            materials = []
            for mat in ob.data.materials:
                mat_name = "_missing_material_"
                if mat:
                    #Look for a texture named "D.png", which indicates a diffuse texture, and generate the material name based on that
                    for texture_slot in mat.texture_slots:
                        if texture_slot and texture_slot.texture:
                            if type(texture_slot.texture) is bpy.types.ImageTexture and texture_slot.texture.image:
                                filepath = texture_slot.texture.image.filepath
                                if (filepath.endswith('D.png')):
                                    _, filepath = filepath.split('//', 1)
                                    if (filepath[0] is not "/"):
                                        filepath = os.path.abspath(os.path.dirname(bpy.data.filepath) + os.sep + filepath)
                                    path_tokens = filepath.split(os.sep)
                                    intersect = len(path_tokens) - 1 - path_tokens[::-1].index('assets')
                                    if intersect != -1:
                                        mat_name = "/" + "/".join(path_tokens[intersect + 1:-1])
                                        break

                    materials.append((mat_name, False, mat))
                else:
                    print('[WARNING:] Bad material data in', ob)
                    materials.append(('_missing_material_', True, None))  # fixed dec22, keep proper index
            if not materials:
                materials.append(('_missing_material_', True, None))
            material_faces = []
            for matidx, mat in enumerate(materials):
                material_faces.append([])

            # Textures
            dotextures = False
            uvcache = []  # should get a little speed boost by this cache
            if mesh.tessface_uv_textures.active:
                dotextures = True
                for layer in mesh.tessface_uv_textures:
                    uvs = []
                    uvcache.append(uvs)  # layer contains: name, active, data
                    for uvface in layer.data:
                        uvs.append((uvface.uv1, uvface.uv2, uvface.uv3, uvface.uv4))


            for F in mesh.tessfaces:
                smooth = F.use_smooth
                faces = material_faces[F.material_index]
                # Ogre only supports triangles
                tris = []
                tris.append((F.vertices[0], F.vertices[1], F.vertices[2]))
                if len(F.vertices) >= 4:
                    tris.append((F.vertices[0], F.vertices[2], F.vertices[3]))
                a = []
                b = []
                uvtris = [a, b]
                if dotextures:
                    for layer in uvcache:
                        uv1, uv2, uv3, uv4 = layer[F.index]
                        a.append((uv1, uv2, uv3))
                        b.append((uv1, uv3, uv4))

                # Pass polygons and loops along with tessfaces
                P = mesh.polygons[F.index]
                ptris = []
                ptris.append((P.loop_indices[0], P.loop_indices[1], P.loop_indices[2]))
                if len(P.loop_indices) >= 4:
                    ptris.append((P.loop_indices[0], P.loop_indices[2], P.loop_indices[3]))

                for tidx, tri in enumerate(tris):
                    face = []
                    for vidx, idx in enumerate(tri):
                        vtri = tris[tidx]
                        ltri = ptris[tidx]
                        v = mesh.vertices[vtri[vidx]]
                        l = mesh.loops[ltri[vidx]]

                        #transform the vertex according to the rotation and scale set on the object
                        transformed_vertex = mathutils.Vector(x * y for x, y in zip(v.co, ob.scale))
                        transformed_vertex.rotate(ob.rotation_euler)
                        #if multiple meshes are selected, we need to make the location relative to the active object
                        if multimeshes:
                            transformed_vertex += (ob.location - bpy.context.active_object.location)

                        x, y, z = swap(transformed_vertex)  # xz-y is correct!

                        if smooth:
                            nx, ny, nz = swap(l.normal)
                        else:
                            nx, ny, nz = swap(F.normal)

                        export_vertex_color, color_tuple = \
                            extract_vertex_color(vcolors, vcolors_alpha, F, idx)
                        r, g, b, ra = color_tuple

                        # Texture maps
                        vert_uvs = []
                        if dotextures:
                            for layer in uvtris[tidx]:
                                vert_uvs.append(layer[vidx])

                        # Tangent
                        tx, ty, tz = swap(l.tangent)
                        # Bitangent
                        btx, bty, btz = swap(l.bitangent)

                        ''' Check if we already exported that vertex with same normal, do not export in that case,
                            (flat shading in blender seems to work with face normals, so we copy each flat face'
                            vertices, if this vertex with same normals was already exported,
                            todo: maybe not best solution, check other ways (let blender do all the work, or only
                            support smooth shading, what about seems, smoothing groups, materials, ...)
                        '''
                        vert = VertexNoPos(numverts, nx, ny, nz, r, g, b, ra, vert_uvs)
                        alreadyExported = False
                        if idx in shared_vertices:
                            for vert2 in shared_vertices[idx]:
                                # does not compare ogre_vidx (and position at the moment)
                                if vert == vert2:
                                    face.append(vert2.ogre_vidx)
                                    alreadyExported = True
                                    # print(idx,numverts, nx,ny,nz, r,g,b,ra, vert_uvs, "already exported")
                                    break
                            if not alreadyExported:
                                face.append(vert.ogre_vidx)
                                shared_vertices[idx].append(vert)
                                # print(numverts, nx,ny,nz, r,g,b,ra, vert_uvs, "appended")
                        else:
                            face.append(vert.ogre_vidx)
                            shared_vertices[idx] = [vert]
                            # print(idx, numverts, nx,ny,nz, r,g,b,ra, vert_uvs, "created")

                        if alreadyExported:
                            continue

                        numverts += 1
                        _remap_verts_.append(v)

                        doc.start_tag('vertex', {})
                        doc.leaf_tag('position', {
                            'x': '%6f' % x,
                            'y': '%6f' % y,
                            'z': '%6f' % z
                        })

                        doc.leaf_tag('normal', {
                            'x': '%6f' % nx,
                            'y': '%6f' % ny,
                            'z': '%6f' % nz
                        })

                        if export_vertex_color:
                            doc.leaf_tag('colour_diffuse', {'value': '%6f %6f %6f %6f' % (r, g, b, ra)})

                        # Texture maps
                        if dotextures:
                            for uv in vert_uvs:
                                doc.leaf_tag('texcoord', {
                                    'u': '%6f' % uv[0],
                                    'v': '%6f' % (1.0 - uv[1])
                                })

                        doc.leaf_tag('tangent', {
                            'x': '%6f' % tx,
                            'y': '%6f' % ty,
                            'z': '%6f' % tz
                            })

                        doc.leaf_tag('binormal', {
                            'x': '%6f' % btx,
                            'y': '%6f' % bty,
                            'z': '%6f' % btz
                            })

                        doc.end_tag('vertex')

                    append_triangle_in_vertex_group(mesh, ob, vertex_groups, face, tri)
                    faces.append((face[0], face[1], face[2]))

            Report.vertices += numverts

            submesh['materials'] = materials
            submesh['material_faces'] = material_faces

            del uvcache

        doc.end_tag('vertexbuffer')
        doc.end_tag('sharedgeometry')

        if logging:
            print('        Done at', timer_diff_str(start), "seconds")
            print('      - Writing submeshes')

        doc.start_tag('submeshes', {})
        for submesh in submeshes:
            materials = submesh['materials']
            material_faces = submesh['material_faces']

            for matidx, (mat_name, extern, mat) in enumerate(materials):
                if not len(material_faces[matidx]):
                    Report.warnings.append(
                        'BAD SUBMESH "%s": material %r, has not been applied to any faces - not exporting as submesh.' % (
                        obj_name, mat_name))
                    continue  # fixes corrupt unused materials

                submesh_attributes = {
                    'usesharedvertices': 'true',
                    # Maybe better look at index of all faces, if one over 65535 set to true;
                    # Problem: we know it too late, postprocessing of file needed
                    "use32bitindexes": str(bool(numverts > 65535)),
                    "operationtype": "triangle_list"
                }
                if mat_name != "_missing_material_":
                    submesh_attributes['material'] = mat_name

                doc.start_tag('submesh', submesh_attributes)
                doc.start_tag('faces', {
                    'count': str(len(material_faces[matidx]))
                })
                for fidx, (v1, v2, v3) in enumerate(material_faces[matidx]):
                    doc.leaf_tag('face', {
                        'v1': str(v1),
                        'v2': str(v2),
                        'v3': str(v3)
                    })
                doc.end_tag('faces')
                doc.end_tag('submesh')
                Report.triangles += len(material_faces[matidx])

        for name, ogre_indices in vertex_groups.items():
            if len(ogre_indices) <= 0:
                continue
            submesh_attributes = {
                'usesharedvertices': 'true',
                "use32bitindexes": str(bool(numverts > 65535)),
                "operationtype": "triangle_list",
                "material": "none",
            }
            doc.start_tag('submesh', submesh_attributes)
            doc.start_tag('faces', {
                'count': len(ogre_indices)
            })
            for (v1, v2, v3) in ogre_indices:
                doc.leaf_tag('face', {
                    'v1': str(v1),
                    'v2': str(v2),
                    'v3': str(v3)
                })
            doc.end_tag('faces')
            doc.end_tag('submesh')

        del shared_vertices
        doc.end_tag('submeshes')

        # Submesh names
        doc.start_tag('submeshnames', {})

        idx = 0
        for submesh in submeshes:
            materials = submesh['materials']
            for matidx, (mat_name, extern, mat) in enumerate(materials):

                submesh_name = obj_name
                if matidx > 0:
                    submesh_name += str(matidx)
                doc.leaf_tag('submesh', {
                    'name': submesh_name,
                    'index': str(idx + matidx)
                })
            idx += len(materials)
        for name in vertex_groups.keys():
            name = name[len('ogre.vertex.group.'):]
            doc.leaf_tag('submesh', {'name': name, 'index': idx})
            idx += 1
        doc.end_tag('submeshnames')

        if logging:
            print('        Done at', timer_diff_str(start), "seconds")


        # if arm:
        #     doc.leaf_tag('skeletonlink', {
        #         'name': '%s.skeleton' % obj_name
        #     })
        #     doc.start_tag('boneassignments', {})
        #     boneOutputEnableFromName = {}
        #     boneIndexFromName = {}
        #     for bone in arm.pose.bones:
        #         boneOutputEnableFromName[bone.name] = True
        #     boneIndex = 0
        #     for bone in arm.pose.bones:
        #         boneIndexFromName[bone.name] = boneIndex
        #         if boneOutputEnableFromName[bone.name]:
        #             boneIndex += 1
        #     badverts = 0
        #     for vidx, v in enumerate(_remap_verts_):
        #         check = 0
        #         for vgroup in v.groups:
        #             if vgroup.weight > 0.01:
        #                 groupIndex = vgroup.group
        #                 if groupIndex < len(copy.vertex_groups):
        #                     vg = copy.vertex_groups[groupIndex]
        #                     if vg.name in boneIndexFromName:  # allows other vertex groups, not just armature vertex groups
        #                         bnidx = boneIndexFromName[vg.name]  # find_bone_index(copy,arm,vgroup.group)
        #                         doc.leaf_tag('vertexboneassignment', {
        #                             'vertexindex': str(vidx),
        #                             'boneindex': str(bnidx),
        #                             'weight': '%6f' % vgroup.weight
        #                         })
        #                         check += 1
        #                 else:
        #                     print('WARNING: object vertex groups not in sync with armature', copy, arm, groupIndex)
        #         if check > 4:
        #             badverts += 1
        #             print(
        #                 'WARNING: vertex %s is in more than 4 vertex groups (bone weights)\n(this maybe Ogre incompatible)' % vidx)
        #     if badverts:
        #         Report.warnings.append(
        #             '%s has %s vertices weighted to too many bones (Ogre limits a vertex to 4 bones)\n[try increaseing the Trim-Weights threshold option]' % (
        #             mesh.name, badverts))
        #     doc.end_tag('boneassignments')
        #
        # # Updated June3 2011 - shape animation works
        # if ob.data.shape_keys and len(ob.data.shape_keys.key_blocks):
        #     print('      - Writing shape keys')
        #
        #     doc.start_tag('poses', {})
        #     for sidx, skey in enumerate(ob.data.shape_keys.key_blocks):
        #         if sidx == 0: continue
        #         if len(skey.data) != len(mesh.vertices):
        #             failure = 'FAILED to save shape animation - you can not use a modifier that changes the vertex count! '
        #             failure += '[ mesh : %s ]' % mesh.name
        #             Report.warnings.append(failure)
        #             print(failure)
        #             break
        #
        #         doc.start_tag('pose', {
        #             'name': skey.name,
        #             # If target is 'mesh', no index needed, if target is submesh then submesh identified by 'index'
        #             # 'index' : str(sidx-1),
        #             # 'index' : '0',
        #             'target': 'mesh'
        #         })
        #
        #         for vidx, v in enumerate(_remap_verts_):
        #             pv = skey.data[v.index]
        #             x, y, z = swap(pv.co - v.co)
        #             # for i,p in enumerate( skey.data ):
        #             # x,y,z = p.co - ob.data.vertices[i].co
        #             # x,y,z = swap( ob.data.vertices[i].co - p.co )
        #             # if x==.0 and y==.0 and z==.0: continue        # the older exporter optimized this way, is it safe?
        #             doc.leaf_tag('poseoffset', {
        #                 'x': '%6f' % x,
        #                 'y': '%6f' % y,
        #                 'z': '%6f' % z,
        #                 'index': str(vidx)  # is this required?
        #             })
        #         doc.end_tag('pose')
        #     doc.end_tag('poses')
        #
        #     if logging:
        #         print('        Done at', timer_diff_str(start), "seconds")
        #
        #     if ob.data.shape_keys.animation_data and len(ob.data.shape_keys.animation_data.nla_tracks):
        #         print('      - Writing shape animations')
        #         doc.start_tag('animations', {})
        #         _fps = float(bpy.context.scene.render.fps)
        #         for nla in ob.data.shape_keys.animation_data.nla_tracks:
        #             for idx, strip in enumerate(nla.strips):
        #                 doc.start_tag('animation', {
        #                     'name': strip.name,
        #                     'length': str((strip.frame_end - strip.frame_start) / _fps)
        #                 })
        #                 doc.start_tag('tracks', {})
        #                 doc.start_tag('track', {
        #                     'type': 'pose',
        #                     'target': 'mesh'
        #                     # If target is 'mesh', no index needed, if target is submesh then submesh identified by 'index'
        #                     # 'index' : str(idx)
        #                     # 'index' : '0'
        #                 })
        #                 doc.start_tag('keyframes', {})
        #                 for frame in range(int(strip.frame_start), int(strip.frame_end) + 1,
        #                                    bpy.context.scene.frame_step):  # thanks to Vesa
        #                     bpy.context.scene.frame_set(frame)
        #                     doc.start_tag('keyframe', {
        #                         'time': str((frame - strip.frame_start) / _fps)
        #                     })
        #                     for sidx, skey in enumerate(ob.data.shape_keys.key_blocks):
        #                         if sidx == 0: continue
        #                         doc.leaf_tag('poseref', {
        #                             'poseindex': str(sidx - 1),
        #                             'influence': str(skey.value)
        #                         })
        #                     doc.end_tag('keyframe')
        #                 doc.end_tag('keyframes')
        #                 doc.end_tag('track')
        #                 doc.end_tag('tracks')
        #                 doc.end_tag('animation')
        #         doc.end_tag('animations')
        #         print('        Done at', timer_diff_str(start), "seconds")

        ## Clean up and save
        for submesh in submeshes:
            copy = submesh['copy']
            mesh = submesh['mesh']
            copy.user_clear()
            bpy.data.objects.remove(copy)
            mesh.user_clear()
            bpy.data.meshes.remove(mesh)
            del copy
            del mesh

        del _remap_verts_
        doc.close()  # reported by Reyn
        f.close()

        if logging:
            print('      - Created .mesh.xml at', timer_diff_str(start), "seconds")

    # todo: Very ugly, find better way
    def replaceInplace(f, searchExp, replaceExp):
        import fileinput
        for line in fileinput.input(f, inplace=1):
            if searchExp in line:
                line = line.replace(searchExp, replaceExp)
            sys.stdout.write(line)
        fileinput.close()  # reported by jakob

    replaceInplace(target_file, '__TO_BE_REPLACED_VERTEX_COUNT__' + '"', str(numverts) + '"')  # + ' ' * (ls - lr))
    del (replaceInplace)

    # note that exporting the skeleton does not happen here anymore
    # it moved to the function dot_skeleton in its own module

    logging.info('      - Created .mesh in total time %s seconds', timer_diff_str(start))


def append_triangle_in_vertex_group(mesh, obj, vertex_groups, ogre_indices, blender_indices):
    vertices = [mesh.vertices[i] for i in blender_indices]
    names = set()
    for v in vertices:
        for g in v.groups:
            if g.group >= len(obj.vertex_groups):
                return
            group = obj.vertex_groups.get(g.group)
            if not group.name.startswith("ogre.vertex.group."):
                return
            names.add(group.name)
    match_group = lambda name, v: name in [obj.vertex_groups[x.group].name for x in v.groups]
    for name in names:
        all_in_group = all([match_group(name, v) for v in vertices])
        if not all_in_group:
            continue
        if name not in vertex_groups:
            vertex_groups[name] = []
        vertex_groups[name].append(ogre_indices)


class VertexNoPos(object):
    def __init__(self, ogre_vidx, nx, ny, nz, r, g, b, ra, vert_uvs):
        self.ogre_vidx = ogre_vidx
        self.nx = nx
        self.ny = ny
        self.nz = nz
        self.r = r
        self.g = g
        self.b = b
        self.ra = ra
        self.vert_uvs = vert_uvs

    '''does not compare ogre_vidx (and position at the moment) [ no need to compare position ]'''

    def __eq__(self, o):
        if not math.isclose(self.nx, o.nx): return False
        if not math.isclose(self.ny, o.ny): return False
        if not math.isclose(self.nz, o.nz): return False
        if not math.isclose(self.r, o.r): return False
        if not math.isclose(self.g, o.g): return False
        if not math.isclose(self.b, o.b): return False
        if not math.isclose(self.ra, o.ra): return False
        if len(self.vert_uvs) != len(o.vert_uvs): return False
        if self.vert_uvs:
            for i, uv1 in enumerate(self.vert_uvs):
                uv2 = o.vert_uvs[i]
                if uv1 != uv2: return False
        return True

    def __repr__(self):
        return 'vertex(%d)' % self.ogre_vidx


def extract_vertex_color(vcolors, vcolors_alpha, face, index):
    r = 1.0
    g = 1.0
    b = 1.0
    ra = 1.0
    export = False
    if vcolors:
        k = list(face.vertices).index(index)
        r, g, b = getattr(vcolors.data[face.index], 'color%s' % (k + 1))
        if vcolors_alpha:
            ra, ga, ba = getattr(vcolors_alpha.data[face.index], 'color%s' % (k + 1))
        else:
            ra = 1.0
        export = True
    return export, (r, g, b, ra)


class Exporter:
    def __init__(self, operator, context):
        self.DEBUG = False
        self.operator = operator
        self.context = context
        # Store all temporary data in a temporary directory
        self.temp_directory = tempfile.mkdtemp()
        tokens = bpy.data.filepath.split(os.sep)
        # The name of the asset, without any extensions. I.e. "deer.blend" becomes "deer"
        self.asset_name = bpy.context.active_object.name
        # self.skeleton_name = bpy.data.scenes['Scene'].Rig

        self.skeleton_name = self.asset_name

        intersect = -1
        if 'source' in tokens:
            #Get the last "source" entry, by reversing the list ('::-1')
            intersect = len(tokens) - 1 - tokens[::-1].index('source')
        if intersect == -1:
            self.operator.report({'WARNING'}, "The Blender file isn't placed below a 'source' directory, "
                                              "as it should be. Placing model and skeleton in same directory as "
                                              "Blender file.")
            destTokens = tokens[0:-1]
        else:
            destTokens = tokens[0:intersect]
            destTokens.append('model')

        # The path to the destination directory, where the mesh and skeleton should be placed
        self.dest_path = (os.sep).join(destTokens)

        self._locate_ogre_tools()

        if 'assets' in tokens:
            _id = tokens.index('assets')
            self.assets_relative_path_tokens = tokens[_id:-1]
            self.assets_root = (os.sep).join(tokens[0:_id + 1])
        else:
            self.operator.report({'WARNING'}, "It seems the Blender file isn't placed in the Worldforge Assets "
                                              "Repository. Automatic naming of material will not work.")

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        # Clean up the temporary directory
        if self.temp_directory:
            #print(self.temp_directory)
            shutil.rmtree(self.temp_directory)

    def _locate_ogre_tools(self):

        # First check if there's a command on the path
        self.converter_path = shutil.which("OgreXMLConverter")
        self.meshmagick_path = shutil.which("meshmagick")

        if self.converter_path:
            self.operator.report({'INFO'}, "Found Ogre XML converter at " + self.converter_path)
        else:
            self.operator.report({'INFO'}, "Could not find Ogre XML converter.")

        # On Windows we can provide the tools ourselves, but on Linux they have to be provided by the system (issues with shared libraries and all)
        # We'll let the provided tools override the ones installed system wide, just to avoid issues. We could expand this with the ability for the user to specify the path.
        if os.name == 'nt':
            _id = None
            tkn = os.path.abspath(os.path.dirname(bpy.data.filepath))
            if 'assets' in tkn:
                _id = tkn.index('assets')
                self.converter_path = os.path.join(tkn[0:_id], 'resources', 'asset_manager', 'bin', 'nt',
                                                   'OgreCommandLineTools_1.7.2', 'OgreXMLConverter.exe')

    def _convert_xml_to_mesh(self, ogre_xml_path, final_asset_name):

        if not self.converter_path:
            self.operator.report({'ERROR'}, 'Could not find any OgreXMLConverter command.')
            return

        dest_mesh_path = os.path.join(self.dest_path, final_asset_name)

        directory = os.path.dirname(dest_mesh_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        result = subprocess.call([self.converter_path, ogre_xml_path, dest_mesh_path])
        if result == 0:
            self.operator.report({'INFO'}, "Wrote mesh file " + dest_mesh_path)
        else:
            self.operator.report({'ERROR'}, "Error when writing mesh file " + dest_mesh_path)

        return dest_mesh_path

    def export_to_xml(self, animation=False):
        '''Uses the OGRE exporter to create a mes.xml file.
        Returns the path to the exported xml file.'''
        ogre_xml_path = os.path.join(self.temp_directory, self.asset_name + ".mesh.xml")
        skeleton_xml_path = os.path.join(self.temp_directory, self.asset_name + ".skeleton.xml")

        logging.debug("Writing to file " + ogre_xml_path)
        dot_mesh(ogre_xml_path)


        return ogre_xml_path, skeleton_xml_path

    def adjust_ogre_xml_skeleton(self, ogre_xml_file, skeleton_name=None):
        '''adjusts the name of the skeleton name of a given ogre_xml_file'''
        with open(ogre_xml_file, 'r') as f:
            lines = f.readlines()
            f.close()

        with open(ogre_xml_file, 'w') as f:
            for line in lines:
                if (line.strip())[0:5] == '<skel':
                    tks = line.split('=')
                    fixed_skeleton_line = ('%s=\'%s\'/>\n' % (tks[0], skeleton_name))
                    f.write(fixed_skeleton_line)
                else:
                    f.write(line)
            f.close()

    def find_file_recursively(self, relative_path_tokens, file_name):
        '''Searches for a file recursively upwards, starting from a directory and walking upwards in the hierarchy until the "assets" directory is reached.'''
        path = os.path.join(self.assets_root, (os.sep).join(relative_path_tokens))

        for root, _, filenames in os.walk(path):
            for filename in fnmatch.filter(filenames, file_name):
                return os.path.join(root, filename)
        del relative_path_tokens[-1]
        return self.find_file_recursively(relative_path_tokens, file_name)

    def find_library_skeleton_path(self, armature):
        # The file name of the exported armature/skeleton
        armature_file_name = armature.name + ".skeleton"

        # we need to remove any '/' characters at the start of the path
        armature_file_path = armature.library.filepath.lstrip('/')
        # if it's a relative path we need to resolve the path
        if armature_file_path.startswith("."):
            rel_path = os.path.dirname(bpy.data.filepath) + os.sep + os.path.dirname(armature_file_path)
            armature_path = os.path.abspath(rel_path)
        else:
            armature_path = os.path.abspath(os.path.dirname(armature_file_path))

        # Get a relative path from the root of the assets library
        armature_relative_path = os.path.relpath(armature_path, self.assets_root)

        # We now know where the armature .blend file should be, but we can't know exactly where the corresponding .skeleton file should be
        # We need to figure this out by searching, first in the most probably location and then walking upwards until we reach the "assets" directory.
        # If we haven't found any skeleton file by then we'll just assume that it should be alongside the .blend file
        armature_found_path = self.find_file_recursively(armature_relative_path.split(os.sep), armature_file_name)
        if armature_found_path:
            return os.path.relpath(armature_found_path, self.assets_root)
        else:
            return armature_relative_path + "/" + armature_file_name

    def export_to_mesh(self, mesh_name, animation=False):
        '''Exports the asset to a .mesh file'''

        try:
            xml_path, skeleton_path = self.export_to_xml(animation)
        except Exception as e:
            self.operator.report({'ERROR'},
                                 "Error when exporting mesh. Make sure you have the Ogre exporter installed. Message: " + str(
                                     e))
            traceback.print_exc()
            return

        skeleton_path = None

        armature = bpy.context.active_object.find_armature()
        if armature and animation:
            # The file name of the exported armature/skeleton
            armature_file_name = mesh_name + ".skeleton"

            # check if it's a linked armature
            if armature.library:
                referenced_skeleton_path = self.find_library_skeleton_path(armature)
            # since it's a linked armature we won't export the skeleton
            else:
                # if it's not a linked armature it's exported to xml and we should convert it
                skeleton_xml_path = os.path.join(self.temp_directory, mesh_name + ".skeleton.xml")
                referenced_skeleton_path = "./" + armature_file_name
                skeleton_path = self._convert_xml_to_mesh(skeleton_xml_path, armature_file_name)

            # we need to adjust the relative path of the skeleton in the mesh file
            self.adjust_ogre_xml_skeleton(xml_path, referenced_skeleton_path)
            self.operator.report({'INFO'}, "Skeleton path set to " + referenced_skeleton_path)

        mesh_path = self._convert_xml_to_mesh(xml_path, mesh_name + ".mesh")
        # see if we have meshmagick available and if so call it
        if mesh_path and self.meshmagick_path:
            # Check if mesh optimization is turned on
            if self.context.scene.EX_wf_export_optimize:
                subprocess.call([self.meshmagick_path, 'optimise', mesh_path])
                self.operator.report({'INFO'}, "Optimised mesh file")
                if animation and skeleton_path:
                    subprocess.call([self.meshmagick_path, 'optimise', skeleton_path])
                    self.operator.report({'INFO'}, "Optimised skeleton file")


# ----------------------------------------------------------------------------
# -------------------------- COMMAND EXEC ------------------------------------
# ----------------------------------------------------------------------------
class OBJECT_OT_wfoe_animated(Operator, AddObjectHelper):
    '''export animated ogre file'''
    bl_idname = 'mesh.wf_export_ogre_animated'
    bl_label = 'Export Ogre Animated'
    bl_category = 'WorldForge'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        with Exporter(self, context) as exporter:
            exporter.export_to_mesh(bpy.context.scene.wf_mesh_name, True)
        return {'FINISHED'}


class OBJECT_OT_wfoe_static(Operator, AddObjectHelper):
    '''export static ogre file'''
    bl_idname = 'mesh.wf_export_ogre_static'
    bl_label = 'Export Ogre Static'
    bl_category = 'WorldForge'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        with Exporter(self, context) as exporter:
            exporter.export_to_mesh(bpy.context.scene.wf_mesh_name, False)
        return {'FINISHED'}


class OBJECT_OT_wf_fix_materials(Operator, AddObjectHelper):
    '''Gets meshes ready for woldforge export'''
    bl_idname = 'mesh.wf_fix_materials'
    bl_label = 'WF Mat Fixer'
    bl_category = 'WorldForge'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None

    def execute(self, context):
        OMM = OgreMaterialManager()
        OMM.wf_fix_materials(context)
        return {'FINISHED'}


class OBJECT_OT_wf_open_ogre_materials(Operator, AddObjectHelper):
    '''open ogre materials based on the texture filename '''
    bl_idname = 'scene.wf_open_ogre_materials'
    bl_label = 'WF Open Ogre Materials'
    bl_category = 'WorldForge'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None

    def execute(self, context):
        OMM = OgreMaterialManager()
        OMM.DEBUG = False
        OMM.open_ogre_materials(context)
        return {'FINISHED'}


class OBJECT_OT_clean_vertex_groups(Operator, AddObjectHelper):
    '''Cleans vertex groups on select objects base on current armatures deformable bones'''
    bl_idname = 'object.clean_vertex_groups'
    bl_label = 'Clean Vertex Groups'
    bl_category = 'WorldForge'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None

    def execute(self, context):
        RAU = RigAnimationUtilities()
        RAU.DEBUG = True
        RAU.clean_vertex_groups(context)
        return {'FINISHED'}


class OBJECT_OT_wf_rename_objects(Operator):
    """Renames multiple objects names and the data names to a supplied string"""
    bl_idname = "object.wf_rename_objects"
    bl_label = "Rename Object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.selected_objects != None

    def execute(self, context):
        print('renaming objects')
        ll = ['|', ' ', '.', ':', '\'', '\"', '\\', '@', '#', '$', '%', '^', ';']

        arr = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', ]
        obs = context.selected_editable_objects
        print(obs)
        if context.scene.wf_rename_panel != '':
            new_name = context.scene.wf_rename_panel
            for i in new_name:
                if i in ll:
                    new_name.replace(i, '_')

            new_name = new_name.lower()
            new_name = new_name.replace(' ', '_')
            print(new_name)
            if len(obs) > 1:
                for zz in range(0, len(obs)):
                    ob = obs[zz]
                    ob.name = new_name + ('_%s' % arr[zz])
                    ob.data.name = new_name + ('_%s' % arr[zz])
            else:
                ob = obs[0]
                ob.name = new_name
                ob.data.name = new_name

        return {'FINISHED'}


class OBJECT_OT_wf_pivot_to_selected(Operator):
    """Pivot to Selection"""
    bl_idname = "object.wf_pivot_to_selected"
    bl_label = "Pivot To Selected"
    bl_options = {'REGISTER', 'UNDO'}

    # @classmethod
    # def poll(cls, context):
    #     obj = context.active_object
    #     return obj is not None and obj.mode == 'EDIT'

    def execute(self, context):
        obj = context.active_object
        if obj.mode == 'EDIT':
            saved_location = bpy.context.scene.cursor_location.copy()
            bpy.ops.view3d.snap_cursor_to_selected()
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
            bpy.context.scene.cursor_location = saved_location
            bpy.ops.object.mode_set(mode='EDIT')

        if obj.mode == 'OBJECT':
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')

        return {'FINISHED'}


# ----------------------------------------------------------------------------
# ------------------------ BUTTON MAPPING ------------------------------------
# ----------------------------------------------------------------------------
def wfoe_static_manual_map():
    url_manual_prefix = 'http://wiki.blender.org/index.php/Doc:2.6/Manual/'
    url_manual_mapping = (('bpy.ops.mesh.wf_export_ogre_static', 'Modeling/Objects'),)
    return url_manual_prefix, url_manual_mapping


def wfoe_animated_manual_map():
    url_manual_prefix = 'http://wiki.blender.org/index.php/Doc:2.6/Manual/'
    url_manual_mapping = (('bpy.ops.mesh.wf_export_ogre_animated', 'Modeling/Objects'),)
    return url_manual_prefix, url_manual_mapping


def wf_fix_materials_manual_map():
    url_manual_prefix = 'http://wiki.blender.org/index.php/Doc:2.6/Manual/'
    url_manual_mapping = (('bpy.ops.mesh.wf_fix_materials', 'Modeling/Objects'),)
    return url_manual_prefix, url_manual_mapping


def wf_open_ogre_materials_manual_map():
    url_manual_prefix = 'http://wiki.blender.org/index.php/Doc:2.6/Manual/'
    url_manual_mapping = (('bpy.ops.scene.wf_open_ogre_materials', 'Modeling/Objects'),)
    return url_manual_prefix, url_manual_mapping


def clean_vertex_groups_manual_map():
    url_manual_prefix = 'http://wiki.blender.org/index.php/Doc:2.6/Manual/'
    url_manual_mapping = (('bpy.ops.object.clean_vertex_groups', 'Modeling/Objects'),)
    return url_manual_prefix, url_manual_mapping


def wf_rename_objects_manual_map():
    url_manual_prefix = 'http://wiki.blender.org/index.php/Doc:2.6/Manual/'
    url_manual_mapping = (('bpy.ops.object.wf_rename_objects', 'Modeling/Objects'),)
    return url_manual_prefix, url_manual_mapping


def wf_pivot_to_selected_manual_map():
    url_manual_prefix = 'http://wiki.blender.org/index.php/Doc:2.6/Manual/'
    url_manual_mapping = (('bpy.ops.object.wf_pivot_to_selected', 'Modeling/Objects'),)
    return url_manual_prefix, url_manual_mapping


# ----------------------------------------------------------------------------
# --------------------------- PANEL ------------------------------------------
# ----------------------------------------------------------------------------

bpy.types.Scene.Rig = bpy.props.StringProperty()


def get_armature(name):
    '''gets the name of the current armature '''
    for ob in bpy.data.objects:
        if ob.name == name:
            return ob
    return False


class PANEL_OT_wf_tools(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "WorldForge"
    bl_label = "Tools"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="Rename Objects:")
        layout.prop(scene, "wf_rename_panel")
        row = layout.row()
        row.operator('object.wf_rename_objects', text='Renamer', icon="FILE_TICK")
        col = layout.column(align=True)
        col.operator('object.wf_pivot_to_selected', text='', icon='FORCE_FORCE')
        row = col.row(align=True)
        row.operator("object.shade_smooth", text="Smooth")
        row.operator("object.shade_flat", text="Flat")


class PANEL_OT_wf_mat_panel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "WorldForge"
    bl_label = "Material Utils"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        row = layout.row()
        # layout.qlabel(text="Material Utilities")
        row = layout.row(align=True)
        row.operator('mesh.wf_fix_materials', text='Fix Materials', icon='SCULPTMODE_HLT')
        row.operator('scene.wf_open_ogre_materials', text='Ogre Mats', icon='IMASEL')
        # col = layout.column(align=True)
        row = layout.row(align=True)
        row.operator('view3d.material_to_texface', text='Mat to Tex', icon='MATERIAL_DATA')
        row.operator('view3d.texface_to_material', text='Tex to Mat', icon='FACESEL_HLT')


class PANEL_OT_wf_rigging_panel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "WorldForge"
    bl_label = "Rigging Utils"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        col = layout.row()
        col.operator('object.vertex_group_limit_total', text='Limit Weights')
        col.operator('object.clean_vertex_groups', text='Clean Weights')


class PANEL_OT_wf_ogre_export(bpy.types.Panel):
    """Worldforge Tools Panel"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "WorldForge"
    # bl_context = "objectmode"
    bl_label = "Mesh Export"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        col = layout.column(align=True)
        col.label(text="Mesh name:")
        layout.prop(scene, "wf_mesh_name")
        row = layout.row()
        row.operator("mesh.wf_export_ogre_static", icon='VIEW3D')

        row = layout.row(align=True)
        row.prop(scene, "frame_start")
        row.prop(scene, "frame_end")
        row = layout.row()
        row.prop(scene, "EX_wf_export_optimize")
        row = layout.row()
        row.operator("mesh.wf_export_ogre_animated", icon='BONE_DATA')

wf_active_object = bpy.context.active_object
@bpy.app.handlers.persistent
def wf_mesh_name_handler(dummy):
    global wf_active_object
    if wf_active_object != bpy.context.active_object:
        wf_active_object = bpy.context.active_object
        bpy.context.scene.wf_mesh_name = wf_active_object.name

# ----------------------------------------------------------------------------
# --------------------------- REGISTRATION -----------------------------------
# ----------------------------------------------------------------------------
def register():
    bpy.types.Scene.wf_mesh_name = bpy.props.StringProperty(name="", description="Rename objects with this string")
    bpy.types.Scene.wf_rename_panel = bpy.props.StringProperty(name="", description="Rename objects with this string")

    bpy.utils.register_class(OBJECT_OT_wfoe_static)
    bpy.utils.register_manual_map(wfoe_static_manual_map)

    bpy.utils.register_class(OBJECT_OT_wfoe_animated)
    bpy.utils.register_manual_map(wfoe_animated_manual_map)

    bpy.utils.register_class(OBJECT_OT_wf_fix_materials)
    bpy.utils.register_manual_map(wf_fix_materials_manual_map)

    bpy.utils.register_class(OBJECT_OT_wf_open_ogre_materials)
    bpy.utils.register_manual_map(wf_open_ogre_materials_manual_map)

    bpy.utils.register_class(OBJECT_OT_clean_vertex_groups)
    bpy.utils.register_manual_map(clean_vertex_groups_manual_map)

    bpy.utils.register_class(OBJECT_OT_wf_rename_objects)
    bpy.utils.register_manual_map(wf_rename_objects_manual_map)

    bpy.utils.register_class(OBJECT_OT_wf_pivot_to_selected)
    bpy.utils.register_manual_map(wf_pivot_to_selected_manual_map)

    bpy.utils.register_class(PANEL_OT_wf_ogre_export)
    bpy.utils.register_class(PANEL_OT_wf_mat_panel)
    bpy.utils.register_class(PANEL_OT_wf_rigging_panel)
    bpy.utils.register_class(PANEL_OT_wf_tools)
    bpy.types.Scene.EX_wf_export_optimize = bpy.props.BoolProperty(default=False, name="Optimize mesh",
                                                                   description="If enabled, MeshMagick (if available) will be used to optimize the mesh.")
    bpy.app.handlers.scene_update_post.append(wf_mesh_name_handler)


def unregister():
    del bpy.types.Scene.wf_mesh_name
    del bpy.types.Scene.wf_rename_panel

    bpy.utils.unregister_class(OBJECT_OT_wfoe_static)
    bpy.utils.unregister_manual_map(wfoe_static_manual_map)

    bpy.utils.unregister_class(OBJECT_OT_wfoe_animated)
    bpy.utils.unregister_manual_map(wfoe_animated_manual_map)

    bpy.utils.unregister_class(OBJECT_OT_wf_fix_materials)
    bpy.utils.unregister_manual_map(wf_fix_materials_manual_map)

    bpy.utils.unregister_class(OBJECT_OT_wf_open_ogre_materials)
    bpy.utils.unregister_manual_map(wf_open_ogre_materials_manual_map)

    bpy.utils.unregister_class(OBJECT_OT_clean_vertex_groups)
    bpy.utils.unregister_manual_map(clean_vertex_groups_manual_map)

    bpy.utils.unregister_class(OBJECT_OT_wf_rename_objects)
    bpy.utils.unregister_manual_map(wf_rename_objects_manual_map)

    bpy.utils.unregister_class(OBJECT_OT_wf_pivot_to_selected)
    bpy.utils.unregister_manual_map(wf_pivot_to_selected_manual_map)

    bpy.utils.unregister_class(PANEL_OT_wf_ogre_export)
    bpy.utils.unregister_class(PANEL_OT_wf_mat_panel)
    bpy.utils.unregister_class(PANEL_OT_wf_rigging_panel)
    bpy.utils.unregister_class(PANEL_OT_wf_tools)

    bpy.app.handlers.scene_update_post.remove(wf_mesh_name_handler)

if __name__ == '__main__':
    register()
