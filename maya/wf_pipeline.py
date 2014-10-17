import maya.cmds as cmds
import maya.mel as mm
import os, sys
from xml.dom.minidom import parse
from xml.dom import minidom
import time

def create_dirs( path ):
	if not os.path.exists(path):
		os.makedirs(path)		

def get_directory_intersection( intersection_string, directory = None ):
	if directory ==  None:
		directory = cmds.file(q=True, sceneName=True)
		print directory

	tkn = os.path.abspath( directory ).split(os.sep)
	intersect = False
	if intersection_string in tkn:
		intersect = tkn.index( intersection_string )
	return intersect

def get_ogre_converter():
	_path = cmds.file(q=True, sceneName=True)
	root_path = None
	try:
		idx =  _path.index('assets')
		root_path = _path[0:idx]
	except:
		print 'String \"assets\" does not exist in the path %s' % _path
		return False

	if root_path:
		return os.path.abspath( os.path.join(root_path, 'resources','asset_manager',\
									'bin','nt','OgreCommandLineTools_1.7.2',\
									'OgreXMLConverter.exe') )

def get_export_dir():
	scene_path = os.path.abspath(cmds.file(q=True, sceneName=True))
	intersection = get_directory_intersection('source', scene_path)

	if intersection:
		path_arr = scene_path.split(os.sep)[0:intersection] + ['model']
		return (os.sep).join(path_arr)
	return False

def get_objects():
	meshes = cmds.ls( selection=True )

	if len(meshes) == 0:
		meshes =cmds.ls( geometry=True, visible=True)
		# if len(meshes) != 0:
		# 	return False
	return meshes

def get_root_project():
	_path = cmds.file(q=True, sceneName=True)
	try:
		idx =  _path.index('assets')
		return _path[:idx+6]
		
	except:
		print 'String \"assets\" does not exist in the path %s' % _path

def fix_texure_path(root_path, img_path):
	tail_path = False
	try:
		idx =  img_path.index('assets')
		tail_path =  img_path[idx+6:]
	except:
		pass
	if tail_path:
		return  root_path + tail_path
		#test = os.path.join(root_path, tail_path)
		#print test
	return tail_path	

def get_scene_texture_connections():
	conns =[]
	
	for mat in cmds.ls(mat=True):
		if cmds.nodeType(mat) == 'lambert':
			dif_conn = cmds.listConnections('%s.color' % mat)
			nrm_conn = cmds.listConnections('%s.normalCamera' % mat)
			if dif_conn:
				conns.append(dif_conn[0])
			if nrm_conn:
				for itm in cmds.listConnections(nrm_conn):
					if cmds.nodeType(itm) == 'file':
						conns.append(itm)
						break
				
		if cmds.nodeType(mat) == 'blinn' or cmds.nodeType(mat) == 'phong':
			dif_conn = cmds.listConnections('%s.color' % mat)
			nrm_conn = cmds.listConnections('%s.normalCamera' % mat)
			spc_conn = cmds.listConnections('%s.specularColor' % mat)
			if dif_conn:
				conns.append(dif_conn[0])
				
			if nrm_conn:
				#conns.append(nrm_conn[0])
				for itm in cmds.listConnections(nrm_conn):
					if cmds.nodeType(itm) == 'file':
						conns.append(itm)
						break
						
			if spc_conn:
				conns.append(spc_conn[0])
	return conns	

def convert_mesh_to_xml(ogre_mesh_files, force=False):
	oxmlc = get_ogre_converter()

	# converte mesh to xml files
	for om in ogre_mesh_files:
		if os.path.exists(om):
			mesh = om
			xml = om + '.xml'
			if force:
				os.system('%s -t -q %s' % (oxmlc, mesh) )
			else:			
				if os.path.exists(xml):
					#converts the mesh if its new 
					if os.path.getmtime(mesh) > os.path.getmtime(xml):
						os.system('%s -t -q %s' % (oxmlc, mesh) )	
				else:
					os.system('%s -t -q %s' % (oxmlc, mesh) )	

def convert_xml_to_mesh(ogre_mesh_files):
	oxmlc = get_ogre_converter()

	# converte mesh to xml files
	for om in ogre_mesh_files:
		if os.path.exists(om):
			os.remove(om)
			xml = om + '.xml'
			if os.path.exists(xml):
				os.system('%s -q %s' % (oxmlc, xml) )
			
def fix_xml_material_names(ogre_mesh_files):

	convert_mesh_to_xml(ogre_mesh_files)

	for om in ogre_mesh_files:
		if os.path.exists(om + '.xml'):
			xmldoc = minidom.parse(om +'.xml')
			submeshes = xmldoc.getElementsByTagName("submesh")
			for node in submeshes:
				old_mat = node.attributes["material"].value
				new_mat = old_mat.replace('_','/')
				node.attributes["material"].value = new_mat
			
			#write back to the xml file
			updated_xml = xmldoc.toxml()
			# print updated_xml
			f = open(om+'.xml','w')
			f.write(updated_xml )
			f.close()

	convert_xml_to_mesh(ogre_mesh_files)


def rename_mats(*args):
	mats = cmds.ls(mat=True)
	for mat in mats:
		_file = cmds.listConnections('%s.color' % mat)
		if _file :
			tex_path =  cmds.getAttr(_file[0] + '.fileTextureName')
			try:
				idx =  tex_path.index('assets')
				new_name = '_' + tex_path[idx+7:-6]
				cmds.rename(mat, new_name)

			except:
				print 'Material: \n  %s' % mat
				print 'String \"assets\" does not exist in the path\n  %s' % tex_path

def repath_scene_textures(*args):			
	root_dir = get_root_project()
	connections = get_scene_texture_connections()
	
	for con in connections:
		tex_path =  cmds.getAttr('%s.fileTextureName' % con)
		new_path = fix_texure_path( root_dir, tex_path )
		if new_path:
			cmds.setAttr('%s.fileTextureName' % con,tex_path, type="string" )
		else:
			print 'Image not in the scope of the Worldforge project:\n	using existing path: ---> %s' % tex_path

def export_static_ogre(*args):
	export_dir = get_export_dir()
	objects = get_objects()
	ogre_mesh_files = []
	if (cmds.file(q=True, sceneName=True)==''):
		print 'Not a valid scene. Try saving it.'
		return False

	if not export_dir:
		print ("Empty Scene? unable to export.")

	else:
		print ('Export Directory:\n  %s\nOgre files\n' % export_dir)
		for ob in objects:
			name = ob
			if cmds.nodeType(ob) == 'transform':
				name = cmds.listRelatives(ob)[0]
			cmds.select(ob, r=True)
			_path = os.path.abspath( export_dir + ('/%s.mesh' % name) )
			ogre_path = _path.replace(os.sep, '/')
			# print ('select %s' % ob)
			print ('     %s' % ogre_path)

			ogre_mesh_files.append(ogre_path)
					  # 'ogreExport -sel -obj -lu mm -scale 1 -mesh \"aaa.mesh\" -shared -v -n -c -t -tangents TANGENT -tangentsplitmirrored;''
			command = 'ogreExport -sel -obj -lu mm -scale 0.1 -mesh \"%s\" -shared -n -c -t -tangents TANGENT -tangentsplitmirrored;' % ogre_path
			mm.eval(command)
		
		cmds.select(objects)
		fix_xml_material_names(ogre_mesh_files)

def fix_string(string):
	
	import re
	txt = re.sub("[^aA-zZ]"," ",string)
	for i in reversed(xrange(5)):
		txt = txt.replace(' '*(i+1), '_')

	if txt[len(txt)-1:len(txt)] == '_':
		txt = txt[:len(txt)-1] 

	return txt.lower()

def rename_objects(*args):
	objs = meshes = cmds.ls( selection=True )
	txt = fix_string( cmds.textField('txt_input',q=True,text=True) )
	alphabet = ['a','b','c','d','e','f','g','h','i','j','k','l',]
	if len(objs) == 1:
		ob = objs[0]
		shape = cmds.listRelatives(ob)[0]

		t_name = txt + '_t'
		m_name = txt

		cmds.rename(shape, m_name)
		cmds.rename(ob , t_name)
		return True


	if len(objs) > 1:
		count = 0
		for ob in objs:

			shape = cmds.listRelatives(ob)[0]

			t_name = txt + '_t_' + alphabet[count]
			m_name = txt + '_' + alphabet[count]

			cmds.rename(shape, m_name)
			cmds.rename(ob , t_name)
			count+=1
		return True
	else:
		print'Nothing to do'
		return False
       
def UI():
	# does window exists
	# pass
	global base_name
	if cmds.window('wf_exporter', exists=True):
		cmds.deleteUI('wf_exporter')
	
	# create window	
	window = cmds.window('wf_exporter', title='Worldforge Exporter', w=200, h=500, mnb= False, mxb=False, sizeable=False)
	
	main_layout = cmds.columnLayout(w=100, h=300)

	#image path
	img_path = cmds.internalVar(upd=True)+ 'icons/wf_header.jpg'
	cmds.image(w=215, h=52, image = img_path)


	#cmds.window('wf_exporter45', title='Worldforge Exporter', w=200, h=200, mnb= False, mxb=False, sizeable=True)
	cmds.frameLayout(label="Utilities", collapsable=True, collapse=False) 
	cmds.rowLayout(numberOfColumns=2, columnWidth2=(102, 105), adjustableColumn1=True, columnAttach=[(1, 'both', 0), (2, 'both', 0), (3, 'both', 0)] )	
	cmds.button(label="Rename Materials", command=rename_mats)
	cmds.button(label='Re-Path Textures', command=repath_scene_textures)
	cmds.setParent( '..' )
	cmds.separator(h=5)
	cmds.columnLayout( columnAttach=('both', 5), rowSpacing=10, columnWidth=200 )
	# base_name = cmds.textField('txt_input',w=199)
	cmds.textField('txt_input', w=199)
	# cmds.textField( base_name, edit=True, enterCommand=('cmds.setFocus(\"' + base_name + '\")') )

	cmds.button( label='Re-Name Selected',w=199, command=rename_objects)
	cmds.setParent( '..' )

	
	cmds.frameLayout(label="Exporter", collapsable=True, collapse=False) 
	#cmds.rowLayout(numberOfColumns=2, columnWidth2=(80, 75), adjustableColumn=2, columnAlign=(1, 'right'), columnAttach=[(1, 'both', 0), (2, 'both', 0), (3, 'both', 0)] )
	#cmds.columnLayout(w=200, h=300)
	cmds.separator(h=5)
	cmds.columnLayout( columnAttach=('both', 5), rowSpacing=10, adjustableColumn=True  )

	cmds.button(label="Export Static", width=199, h=50, command=export_static_ogre)
	cmds.button(label="Export Animated", width=199, h=50, enable=False)
	
	cmds.setParent( '..' )
	cmds.showWindow()

