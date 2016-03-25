#bolttools - a framework for creation of part libraries
#Copyright (C) 2013 Johannes Reinhardt <jreinhardt@ist-dein-freund.de>
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#Lesser General Public License for more details.
#
#You should have received a copy of the GNU Lesser General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

from errors import *

from os.path import join, exists, basename, splitext
from os import makedirs, remove
from datetime import datetime
from xml.etree.ElementTree import ElementTree, dump, SubElement
from shutil import copy, copytree, copyfile, rmtree

import license

from common import Backend

def add_part(base,params,doc):
	module = importlib.import_module(base.module_name)
	module.__dict__[base.name](params,doc)

class AllplanBackend(Backend):
	def __init__(self,repo,databases):
		Backend.__init__(self,repo,"allplan",databases,["allplan"])

	def write_output(self,out_path,**kwargs):
		args = self.validate_arguments(kwargs,["target_license","version"])

		self.clear_output_dir(out_path)

		ver_root = join(out_path,args["version"])
		makedirs(ver_root)

		#generate version file
		date = datetime.now()
		with open(join(ver_root,"VERSION"),"w") as version_file:
			version_file.write("%s\n%d-%d-%d\n%s\n" %
				(args["version"], date.year, date.month, date.day, args["target_license"]))

		#copy files
		#bolttools
		if not license.is_combinable_with("LGPL 2.1+",args["target_license"]):
			raise IncompatibleLicenseError(
				"bolttools is LGPL 2.1+, which is not compatible with %s" % args["target_license"])
		copytree(join(self.repo.path,"bolttools"),join(ver_root,"bolttools"))
		#remove the test suite and documentation, to save space
		rmtree(join(ver_root,"bolttools","test_blt"))

		if not exists(join(ver_root,"data")):
			makedirs(join(ver_root,"data"))

		for coll, in self.repo.itercollections():

			#Copy part data
			#Skip collection if no base file exists or licenses issues
			if not license.is_combinable_with(coll.license_name,args["target_license"]):
				print "Skip %s due to license issues" % coll.id
				continue

			if not exists(join(self.repo.path,"allplan",coll.id,"%s.base" % coll.id)):
				print "Skip %s due to missing base file" % coll.id
				continue

			copy(join(self.repo.path,"data","%s.blt" % coll.id),
				join(ver_root,"data","%s.blt" % coll.id))

			for base,classes in self.dbs["allplan"].iterbases(["base","classes"],filter_collection=coll):
				#copy py file
				copy(join(self.repo.path,"allplan",coll.id,base.filename),ver_root)

				for std,cl in self.dbs["allplan"].iterstandards(["standard","class"],filter_base=base):
					#Generate a pyd file for each base
					pyd = ElementTree(file=join(self.repo.path,"backends","allplan","pydtemplate.xml"))
					#fill in script tag
					script = pyd.getroot().findall("Script")[0]
					SubElement(script,"Name").text = base.filename
					SubElement(script,"Title").text = base.filename
					SubElement(script,"Version").text = "1.0"

					element = pyd.getroot()
					page = SubElement(element,"Page")
					SubElement(page,"Name").text = std.standard.get_nice()
					SubElement(page,"Text").text = std.description

					#Hidden parameter to pass the standard id
					param = SubElement(page,"Parameter")
					SubElement(param,"Name").text = "std"
					SubElement(param,"Text").text = "A hidden parameter with the bolts std id"
					SubElement(param,"Value").text = std.standard.get_safe()
					SubElement(param,"Visible").text = "False"

					for pname in cl.parameters.free:
						param = SubElement(page,"Parameter")
						SubElement(param,"Name").text = pname
						SubElement(param,"Text").text = "%s (%s)" % (pname,cl.parameters.description[pname])

						if cl.parameters.types[pname] == "Length (mm)":
							SubElement(param,"Value").text = str(cl.parameters.defaults[pname])
							SubElement(param,"ValueType").text = "Length"
						elif cl.parameters.types[pname] == "Number":
							SubElement(param,"Value").text = str(cl.parameters.defaults[pname])
							SubElement(param,"ValueType").text = "Double"
						elif cl.parameters.types[pname] == "Bool":
							SubElement(param,"Value").text = str(cl.parameters.defaults[pname])
							SubElement(param,"ValueType").text = "CheckBox"
						elif cl.parameters.types[pname] == "Table Index":
							SubElement(param,"Value").text = str(cl.parameters.defaults[pname])
							SubElement(param,"ValueList").text = "|".join(cl.parameters.choices[pname])
							SubElement(param,"ValueType").text = "StringComboBox"
						elif cl.parameters.types[pname] == "String":
							SubElement(param,"Value").text = str(cl.parameters.defaults[pname])
							SubElement(param,"ValueType").text = "String"
							pass
						elif cl.parameters.types[pname] == "Angle (deg)":
							SubElement(param,"Value").text = str(cl.parameters.defaults[pname])
							SubElement(param,"ValueType").text = "Angle"

					pyd.write(join(ver_root,"%s.pyd" % std.standard.get_safe()))

