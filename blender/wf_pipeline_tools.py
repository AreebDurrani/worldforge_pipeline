'''
Tool depends on Blender to Ogre exporter http://code.google.com/p/blender2ogre
'''

bl_info = {
	'name': 'Pipeline Tools',
	'category': 'WorldForge',
	'author': 'anisimkalugin.com',
	'version': (0, 0, 1),
	'blender': (2, 71, 0),
	'description': 'Worldforge Pipeline Tools',
	'warning': '',
	'wiki_url': ''
	}

import bpy, os, shutil, subprocess, tempfile, fnmatch
from bpy.types import Operator
# from bpy.props import FloatVectorProperty
from bpy_extras.object_utils import AddObjectHelper, object_data_add
#from mathutils import Vector
class RigAnimationUtilities:
	def __init__( self ):
		self.DEBUG = False
	
	def clean_vertex_groups( self, context ):
		sel = bpy.context.selected_objects

		for ob in sel:
			vertex_groups = ob.vertex_groups
			if len(ob.modifiers) > 0:
				rig = ob.modifiers[-1].object # get the rig
				bones = rig.data.bones
				
				
				if self.DEBUG:
					print( ob.name )
					print( rig.name )
					print( bones )
				#get data
				vgrp_list = [grp.name for grp in ob.vertex_groups]
				bone_list = [bone.name for bone in rig.data.bones if bone.use_deform ]

				#compare lists 
				del_group = [itm for itm in vgrp_list if itm not in bone_list]
				mkv_groups = [itm for itm in bone_list if itm not in vgrp_list]

				#add vertex groups based on armatures deformable bones
				[ob.vertex_groups.new(name) for name in mkv_groups] 

				# remove groups that are not part of the current armatures deformable bones
				# list comprehension code may be a bit too long
				[ob.vertex_groups.remove( ob.vertex_groups[ ob.vertex_groups.find( group ) ] ) for group in del_group]
				return True

		return False

class OgreMaterialManager:
	'''Worldforge material management utilites'''
	def __init__( self ):
		self.DEBUG = False
		
	def get_base_name( self, path ):
		bad_names_l = ['//..']
		tkns = path.split(os.sep)[1:-1]
		seps = []
		for i in range( len(tkns)):
			itm =  tkns[i]
			if not itm in bad_names_l:
			   seps.append(itm)
		if seps == []:
			return 'blender file name'
			#bpy.path.display_name_from_filepath(bpy.data.filepath)
		return seps[-1]

	def open_ogre_materials(self, context):
		'''opens ogre.material based on the texture file path'''
		sel = bpy.context.selected_objects
		tmp_txt = bpy.data.texts.new('{tmp}') #hacky shit

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
							print ( '---- debug statements ----' )
							print ( image_path )
							print ( ogre_mat_file )
							print ( filepaths )
							print ( exists )
		bpy.data.texts.remove(tmp_txt)
#
	def get_ogre_mat_name( self, relative_path ):
		'''retrieves ogre.material based on the current image'''
		#ogre_mat_file = relative_path[:-5] + 'ogre.material'
		ogre_mat_file = bpy.path.abspath(relative_path)[:-5] + 'ogre.material'
		# ogre_mat_file = testPath[:-5] + 'ogre.material'
		matNames = []
		if os.path.isfile(ogre_mat_file):
			f = open(ogre_mat_file, 'r')
			for line in f:
				if line[:8] == 'material':
					matNames.append( line.split(' ')[1] )
			f.close()

		return matNames

	def write_to_text_datablock(self, b_list):
		'''writes out the list to a ogre mat textblock'''
		ogre_tdb = self.get_text_datablock()
		ogre_tdb.write('--------------\n')
		for itm in b_list:
			ogre_tdb.write('%s \n' % itm )

	def get_text_datablock( self, tdb = 'ogre_mats' ):
		'''gets/creates a text data block (tdb)'''
		txt_datablock = bpy.data.texts.find( tdb )
		if txt_datablock == -1:
			return bpy.data.texts.new( tdb )
		return bpy.data.texts[tdb]

	def wf_fix_materials( self, context):
		'''tries to fix material names based on ogre.material files'''
		sel = bpy.context.selected_objects
		for ob in sel:
			for slot in ob.material_slots:
				mat = slot.material
				mat.name
				
				if mat.active_texture == None:
					continue

				img = mat.active_texture
				image_path = mat.active_texture.image.filepath #= 'asdfsadf' manipulate the file path
				
				#image_names_list = self.get_ogre_mat_name( image_path )
				image_names_list = [itm for itm in self.get_ogre_mat_name( image_path ) if itm[-12:] != 'shadowcaster']
				if image_names_list != []:
					if len(image_names_list) > 1:
						self.write_to_text_datablock( image_names_list )
					else:
						mat.name = image_names_list[0]
						
				image_type = (bpy.path.display_name( image_path )).lower()
				asset_name = self.get_base_name( image_path )
				image_name = '_'.join( [asset_name, image_type] )

				mat.active_texture.name = image_name
				mat.active_texture.image.name = image_name
							
				if self.DEBUG == True:
					print( image_path )
					print( image_type )
					print( asset_name )
					print( image_name )
					print( image_names_list )
					
					
class Exporter:
	def __init__( self, operator, context):
		self.DEBUG = False
		self.operator = operator
		self.context = context
		#Store all temporary data in a temporary directory
		self.temp_directory = tempfile.mkdtemp()
		tokens = bpy.data.filepath.split(os.sep)
		#The name of the asset, without any extensions. I.e. "deer.blend" becomes "deer"
		self.asset_name = (tokens[-1].split('.')[0])
		#self.skeleton_name = bpy.data.scenes['Scene'].Rig
		
		self.skeleton_name = self.asset_name
		
		intersect = -1 
		if 'source' in tokens:
			intersect = tokens.index('source')
		destTokens = tokens[0:intersect]
		destTokens.append('model')
		#The path to the destination directory, where the mesh and skeleton should be placed
		self.dest_path = (os.sep).join(destTokens)
		
		self._locate_ogre_tools()
		
		if 'assets' in tokens:
			_id = tokens.index('assets')
			self.assets_relative_path_tokens = tokens[_id :-1]
			self.assets_root = (os.sep).join(tokens[0:_id + 1])
		
		
	def __enter__(self):
		return self
	
	def __exit__(self, type, value, traceback):
		#Clean up the temporary directory
		if self.temp_directory:
			print(self.temp_directory)
			#shutil.rmtree(self.temp_directory)
			
	def _locate_ogre_tools(self):
		
		#First check if there's a command on the path
		self.converter_path = shutil.which("OgreXMLConverter")
		self.meshmagick_path = shutil.which("meshmagick")

		#On Windows we can provide the tools ourselves, but on Linux they have to be provided by the system (issues with shared libraries and all)
		#We'll let the provided tools override the ones installed system wide, just to avoid issues. We could expand this with the ability for the user to specify the path.
		if os.name == 'nt':
			_id = None
			tkn = os.path.abspath( os.path.dirname(bpy.data.filepath) )
			if 'assets' in tkn:
				_id = tkn.index('assets')
				self.converter_path = os.path.join(tkn[0:_id], 'resources','asset_manager','bin','nt','OgreCommandLineTools_1.7.2','OgreXMLConverter.exe' )
			
	
	
	def _convert_xml_to_mesh(self, ogre_xml_path, final_asset_name):
	
		if not self.converter_path:
			self.operator.report({'ERROR'}, 'Could not find any OgreXMLConverter command.')
			return
			
		dest_mesh_path = os.path.join(self.dest_path, final_asset_name)
		
		subprocess.call([self.converter_path, ogre_xml_path, dest_mesh_path])
		self.operator.report({'INFO'}, "Wrote mesh file " + dest_mesh_path)
		return dest_mesh_path
				
	def export_to_xml(self, animation = False):
		'''Uses the OGRE exporter to create a mes.xml file.
		Returns the path to the exported xml file.'''
		ogre_xml_path = os.path.join(self.temp_directory, self.asset_name + ".mesh.xml")
		skeleton_xml_path = os.path.join(self.temp_directory, self.asset_name + ".skeleton.xml")
		
		bpy.ops.ogre.export(
			EX_COPY_SHADER_PROGRAMS     =False, 
			EX_SWAP_AXIS                ='xz-y', 
			EX_SEP_MATS                 =False, 
			EX_ONLY_DEFORMABLE_BONES    =False, 
			EX_ONLY_ANIMATED_BONES      =False, 
			EX_SCENE                    =False, 
			EX_SELONLY                  =True, 
			EX_FORCE_CAMERA             =False, 
			EX_FORCE_LAMPS              =False, 
			EX_MESH                     =True, 
			EX_MESH_OVERWRITE           =True, 
			EX_ARM_ANIM                 =animation, 
			EX_SHAPE_ANIM               =animation, 
			EX_INDEPENDENT_ANIM         =animation, 
			EX_TRIM_BONE_WEIGHTS        =0.01, 
			EX_ARRAY                    =True, 
			EX_MATERIALS                =False, 
			EX_FORCE_IMAGE_FORMAT       ='NONE', 
			EX_DDS_MIPS                 =1, 
			EX_lodLevels                =0, 
			EX_lodDistance              =300, 
			EX_lodPercent               =40, 
			EX_nuextremityPoints        =0, 
			EX_generateEdgeLists        =False, 
			EX_generateTangents         =True, 
			EX_tangentSemantic          ='uvw', 
			EX_tangentUseParity         =4, 
			EX_tangentSplitMirrored     =False, 
			EX_tangentSplitRotated      =False, 
			EX_reorganiseBuffers        =False, 
			EX_optimiseAnimations       =False, 
			filepath=ogre_xml_path)		
		
		return ogre_xml_path, skeleton_xml_path	
	
	def adjust_ogre_xml_skeleton(self, ogre_xml_file, skeleton_name = None ):
		'''adjusts the name of the skeleton name of a given ogre_xml_file'''
		with open(ogre_xml_file, 'r') as f:
			lines = f.readlines()
			f.close()

		with open(ogre_xml_file, 'w') as f:
			for line in lines:
				if (line.strip())[0:5] == '<skel':
					tks = line.split('=')
					fixed_skeleton_line =  ('%s=\'./%s\'/>\n' % (tks[0], skeleton_name))
					f.write(fixed_skeleton_line)
				else:
					f.write(line)
			f.close()
			
			
	def find_file_recursively(self, relative_path_tokens, file_name):
		'''Searches for a file recursively upwards, starting from a directory and walking upwards in the hierarchy until the "assets" directory is reached.'''
		print(self.assets_root)
		print(relative_path_tokens)
		path = os.path.join(self.assets_root, (os.sep).join(relative_path_tokens))
		
		for root, _, filenames in os.walk(path):
			for filename in fnmatch.filter(filenames, file_name):
				return os.path.join(root, filename)
		del relative_path_tokens[-1]
		return self.find_file_recursively(relative_path_tokens, file_name)

		
		
	def export_to_mesh(self, animation = False):
		'''Exports the asset to a .mesh file'''

		try:		
			xml_path, skeleton_xml_path = self.export_to_xml(animation)
		except Exception as e:
			self.operator.report({'ERROR'}, "Error when exporting mesh. Make sure you have the Ogre exporter installed. Message: " + str(e))
			return

		skeleton_path = None
		
		if animation:
			#Check that there are any armatures
			if len(bpy.data.armatures) > 0:
				if len(bpy.data.armatures) == 1:
					armature = bpy.data.armatures[0]
				else:
					#if there are multiple. check if anyone is selected
					selected_armature_name = self.context.scene.Rig
					if selected_armature_name:
						for an_armature in bpy.data.armatures:
							if an_armature.name == selected_armature_name:
								armature = an_armature
								break
					if not armature:
						#none selected; just select the first one
						armature = bpy.data.armatures[0]

			#The file name of the exported armature/skeleton
			armature_file_name = armature.name + ".skeleton"

			#check if it's a linked armature
			if armature.library:
				#we need to remove any '/' characters at the start of the path
				armature_file_path = armature.library.filepath.lstrip('/')
				#if it's a relative path we need to resolve the path
				if armature_file_path.startswith("."):
					rel_path = os.path.dirname(bpy.data.filepath) + os.sep + os.path.dirname(armature_file_path)
					armature_path = os.path.abspath(rel_path)
				else:
					armature_path = os.path.abspath(os.path.dirname(armature_file_path))
					
				#Get a relative path from the root of the assets library
				armature_relative_path = os.path.relpath(armature_path, self.assets_root)
				
				#We now know where the armature .blend file should be, but we can't know exactly where the corresponding .skeleton file should be
				#We need to figure this out by searching, first in the most probably location and then walking upwards until we reach the "assets" directory.
				#If we haven't found any skeleton file by then we'll just assume that it should be alongside the .blend file
				armature_found_path = self.find_file_recursively(armature_relative_path.split(os.sep), armature_file_name)
				if armature_found_path:
					referenced_skeleton_path = os.path.relpath(armature_found_path, self.assets_root)
				else:
					referenced_skeleton_path = armature_relative_path + "/" + armature_file_name
									
				#since it's a linked armature we won't export the skeleton
			else:
				#if it's not a linked armature we should export it
				if skeleton_xml_path:
					referenced_skeleton_path = armature_file_name
					skeleton_path = self._convert_xml_to_mesh(skeleton_xml_path, armature_file_name)


			#we need to adjust the relative path of the skeleton in the mesh file
			self.adjust_ogre_xml_skeleton(xml_path, referenced_skeleton_path)
			self.operator.report({'INFO'}, "Skeleton path set to " + referenced_skeleton_path)
			
		
		mesh_path = self._convert_xml_to_mesh(xml_path, self.asset_name + ".mesh")
		#see if we have meshmagick available and if so call it
		if mesh_path and self.meshmagick_path:
			#Check if mesh optimization is turned on
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
			exporter.export_to_mesh(True)
		return {'FINISHED'}

class OBJECT_OT_wfoe_static(Operator, AddObjectHelper):
	'''export static ogre file'''
	bl_idname = 'mesh.wf_export_ogre_static'
	bl_label = 'Export Ogre Static'
	bl_category = 'WorldForge'
	bl_options = {'REGISTER', 'UNDO'}


	def execute(self, context):
		with Exporter(self, context) as exporter:
			exporter.export_to_mesh(False)
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

class OBJECT_OT_wf_rename_objects( Operator):
    """Renames multiple objects names and the data names to a supplied string"""
    bl_idname = "object.wf_rename_objects"
    bl_label = "Rename Object"
    bl_options = {'REGISTER', 'UNDO'} 

    

    @classmethod
    def poll(cls, context):
        return context.selected_objects != None

    def execute(self, context):
        print ('renaming objects')
        ll = ['|',' ','.',':','\'','\"','\\', '@','#','$','%','^',';']

        arr = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o',]
        obs = context.selected_editable_objects
        print(obs)
        if context.scene.wf_rename_panel != '':
            new_name = context.scene.wf_rename_panel
            for i in new_name:
                if i in ll:
                    new_name.replace (i,'_')

            new_name = new_name.lower()
            new_name = new_name.replace (' ', '_')
            print (new_name)
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

class OBJECT_OT_wf_pivot_to_selected( Operator ):
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
        if obj.mode =='EDIT':
            saved_location = bpy.context.scene.cursor_location.copy()
            bpy.ops.view3d.snap_cursor_to_selected()
            bpy.ops.object.mode_set(mode = 'OBJECT')
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR')  
            bpy.context.scene.cursor_location = saved_location
            bpy.ops.object.mode_set(mode = 'EDIT')

        if obj.mode == 'OBJECT':
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')

        return {'FINISHED'}
# ----------------------------------------------------------------------------
# ------------------------ BUTTON MAPPING ------------------------------------
# ----------------------------------------------------------------------------
def wfoe_static_manual_map():
	url_manual_prefix = 'http://wiki.blender.org/index.php/Doc:2.6/Manual/'
	url_manual_mapping = (('bpy.ops.mesh.wf_export_ogre_static', 'Modeling/Objects'), )
	return url_manual_prefix, url_manual_mapping

def wfoe_animated_manual_map():
	url_manual_prefix = 'http://wiki.blender.org/index.php/Doc:2.6/Manual/'
	url_manual_mapping = (('bpy.ops.mesh.wf_export_ogre_animated', 'Modeling/Objects'), )
	return url_manual_prefix, url_manual_mapping

def wf_fix_materials_manual_map():
	url_manual_prefix = 'http://wiki.blender.org/index.php/Doc:2.6/Manual/'
	url_manual_mapping = (('bpy.ops.mesh.wf_fix_materials', 'Modeling/Objects'), )
	return url_manual_prefix, url_manual_mapping

def wf_open_ogre_materials_manual_map():
	url_manual_prefix = 'http://wiki.blender.org/index.php/Doc:2.6/Manual/'
	url_manual_mapping = (('bpy.ops.scene.wf_open_ogre_materials', 'Modeling/Objects'), )
	return url_manual_prefix, url_manual_mapping

def clean_vertex_groups_manual_map():
	url_manual_prefix = 'http://wiki.blender.org/index.php/Doc:2.6/Manual/'
	url_manual_mapping = (('bpy.ops.object.clean_vertex_groups', 'Modeling/Objects'), )
	return url_manual_prefix, url_manual_mapping

def wf_rename_objects_manual_map():
	url_manual_prefix = 'http://wiki.blender.org/index.php/Doc:2.6/Manual/'
	url_manual_mapping = (('bpy.ops.object.wf_rename_objects', 'Modeling/Objects'), )
	return url_manual_prefix, url_manual_mapping

def wf_pivot_to_selected_manual_map():
	url_manual_prefix = 'http://wiki.blender.org/index.php/Doc:2.6/Manual/'
	url_manual_mapping = (('bpy.ops.object.wf_pivot_to_selected', 'Modeling/Objects'), )
	return url_manual_prefix, url_manual_mapping

# ----------------------------------------------------------------------------
# --------------------------- REGISRATION ------------------------------------
# ----------------------------------------------------------------------------
def register():
	bpy.types.Scene.wf_rename_panel = bpy.props.StringProperty(name="", description = "Rename objects with this string") 

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

def unregister():
	del bpy.types.Scene.rename_panel

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
	bpy.utils.unregister_manual_map(wf_pivot_to_selected-manual_map)

if __name__ == '__main__':
	register()








