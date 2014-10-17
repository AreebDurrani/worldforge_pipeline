import platform
import os
import sys
import time
import fileinput
import subprocess
import shutil
from shutil import copy2, copystat

# module vars
__author__ = "Anisim Kalugin"
__credits__ = "Internet"
__license__ = "GPL V3.0 - http://www.gnu.org/licenses/"
__maintainer__ = "Anisim Kalugin"
__email__ = "a.kalugin[at]gmail.com"
__github__ = "https://github.com/worldforge/worldforge_pipeline"
__status__ = "Production"
  
# platform check
PLATFORM = platform.uname()[0]
HOST = platform.uname()[1]
MACHINE = platform.machine()
PLATFORMS = ['Windows']
if PLATFORM not in PLATFORMS:
	raise UserWarning('This install only works on Windows!')
  
# globals vars
MODULE_NAME = 'wf_tools'
VERSION = '0.0.1'
MODULE_PATH = '.'
ABSOLUTE_PATH = os.getcwd()
# PYTHON_SOURCE_PATH = MODULE_PATH+'/src'
# EXCLUDE_DIRS = \
# 	[
# 		'.git',
# 		'.svn',
# 	]
# EXCLUDE_FILES = ['pyc','pkl','~']
# MAYA_USERSETUP_MEL_FILE = 'python("import dmptools.setup.init");// automatically added by the dmptools installation'
  
# check if we run the install from the correct location
LD = os.listdir(ABSOLUTE_PATH)

if 'install.py' in LD and 'wf_pipeline.py' in LD and 'icons' in LD and 'shelf' in LD:
	print 'In the right directory'
else:
	raise UserWarning('You run the install from the wrong location!')
del(LD)
  
# platform globals
if PLATFORM == 'Windows':
	HOMEPATH = os.getenv('USERPROFILE')
	TEMPPATH = os.getenv('TEMP')

	# maya windows globals
	MAYA_GLOBAL = HOMEPATH+'/documents/maya/'
	IS_MAYA_EXISTS = os.path.exists(MAYA_GLOBAL)
	MAYA_PLUGINS 	= os.environ['MAYA_PLUG_IN_PATH']
	if not IS_MAYA_EXISTS:
		try:
			from win32com.shell import shell, shellcon
			PERSONAL_PATH = shell.SHGetFolderPath(0, shellcon.CSIDL_PERSONAL, None, 0) 
			MAYA_GLOBAL = PERSONAL_PATH + '/maya/'
		except:
			raise UserWarning('Unable to find Maya')
	MAYA_PATH = MAYA_GLOBAL+'scripts/'

def install_maya():
	""" maya install main function """
	print '=============================='
	print '           M A Y A            '
	print '=============================='
	print 'installing maya ' + MODULE_NAME + ' in ' + MAYA_PATH + '...'


	p_abs = os.path.abspath
	p_join = os.path.join
	p_exist = os.path.exists

	
	dst_prefs_icons	 = p_abs( p_join(MAYA_PLUGINS, '..', 'prefs', 'icons' ) )
	dst_prefs_script = p_abs( p_join(MAYA_PLUGINS, '..', 'prefs', 'scripts' ) )
	dst_scripts		 = p_abs( p_join(MAYA_PLUGINS, '..', 'scripts' ) )
	dst_prefs_shelf	 = p_abs( p_join(MAYA_PLUGINS, '..', 'prefs', 'shelves' ) )


	#script tools
	src_tool = p_join(ABSOLUTE_PATH,'wf_pipeline.py')
	dst_tool = p_join(dst_prefs_script, 'wf_pipeline.py' )
	if p_exist(dst_tool):
		os.remove(dst_tool)
	copy2(src_tool, dst_tool)
	
	#wf shelf 
	shelf_path = p_join(ABSOLUTE_PATH, 'shelf')
	for _f in os.listdir( shelf_path ):
		src_shelf = p_join(shelf_path, _f)
		dst_shelf =  p_join(dst_prefs_shelf, _f)
		if p_exist(dst_shelf):
			os.remove(dst_shelf)
		copy2(src_shelf, dst_shelf)

	#icons
	icon_path = p_join(ABSOLUTE_PATH, 'icons')
	for _f in os.listdir( icon_path ):
		src_icon = p_join(icon_path, _f)
		dst_icon =  p_join(dst_prefs_icons, _f)
		if p_exist(dst_icon):
			os.remove(dst_icon)
		copy2(src_icon, dst_icon)
	# print MAYA_PLUGINS

	#Append to the ogreExporter.mel
	ogre_mel = p_join(dst_scripts,'ogreExporter.mel')
	if p_exist(ogre_mel):
		f = open(ogre_mel, 'r+')
		data = f.readlines()
		f.close()

		if len(data[3985]) == 1:
			data[3985] = r'menuItem -label "WF Exporter" -c "python(\"import wf_pipeline;wf_pipeline.UI()\")";'
			f = open(ogre_mel, 'w')
			f.writelines(data)
			f.close()

if os.path.exists(MAYA_PATH):
	install_maya()
