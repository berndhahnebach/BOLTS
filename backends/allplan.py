# bolttools - a framework for creation of part libraries
# Copyright (C) 2013 Johannes Reinhardt <jreinhardt@ist-dein-freund.de>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

from errors import *  # flake8 gives error: unable to detect undefined names

from os.path import join, exists, basename, splitext
from os import makedirs, remove
from datetime import datetime
from xml.etree.ElementTree import ElementTree, dump, SubElement
from shutil import copy, copytree, copyfile, rmtree

import license

from common import Backend
import xml.dom.minidom


pyguitemplate_pre = '''# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2015 - Bernd Hahnebach <bernd@bimstatik.org>            *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************


import NemAll_Python_Elements as Ele

import sys
from os.path import dirname, join
rootpath = join(dirname(__file__), "BOLTS")
sys.path.append(rootpath)
sys.path.append(join(rootpath, "bolttools"))
sys.path.append(join(rootpath, "yaml"))

import bolttools.blt as BOLTSblt


def check_allplan_version(build_ele, version):
    return True  # Support all versions


def create_element(build_ele, doc):

    # initialize tze BOLTS repo
    repo = BOLTSblt.Repository(rootpath)

    # path for Geom modules, need to be inside the def for some reason ... ?!
    sys.path.append(join(rootpath, "allplan"))

    # initialize bolt_part, this is use for first pre view in Allplan
    preview_params = {'b': 206.0, 'l': 1000.0, 'r': 18.0, 'tw': 15.0, 'h': 220.0, 'tf': 25.0}
    import GeomProfileI
    bolt_part = GeomProfileI.GeomProfileI(preview_params)

    # initialize the BOLTS params dictionary
    params = {}

    # get the input values and fill params with them
    bolts_coll_id = build_ele.CollectionName.value
'''


def add_part(base, params, doc):
    module = importlib.import_module(base.module_name)
    module.__dict__[base.name](params, doc)


class AllplanBackend(Backend):
    def __init__(self, repo, databases):
        Backend.__init__(self, repo, "allplan", databases, ["allplan"])

    def write_output(self, out_path, **kwargs):
        args = self.validate_arguments(kwargs, ["target_license", "version"])

        self.clear_output_dir(out_path)

        ver_root = join(out_path, args["version"])
        makedirs(ver_root)
        out_gui = join(ver_root, "Library", "BIMStatik", "BOLTS")
        out_core = join(ver_root, "PythonPartsScripts", "BIMStatik", "BOLTS", "BOLTS")
        out_module = join(ver_root, "PythonPartsScripts", "BIMStatik", "BOLTS")
        path_in_pyp_for_py = "BIMStatik\\BOLTS\\"
        makedirs(out_gui)
        makedirs(out_core)

        # generate version file
        date = datetime.now()
        with open(join(out_core, "VERSION"), "w") as version_file:
            version_file.write("%s\n%d-%d-%d\n%s\n" %
                (args["version"], date.year, date.month, date.day, args["target_license"]))

        # copy files
        # bolttools
        if not license.is_combinable_with("LGPL 2.1+", args["target_license"]):
            raise IncompatibleLicenseError(
                "bolttools is LGPL 2.1+, which is not compatible with %s" % args["target_license"])
        copytree(join(self.repo.path, "bolttools"), join(out_core, "bolttools"))
        # remove the test suite and documentation, to save space
        rmtree(join(out_core, "bolttools", "test_blt"))

        # yaml
        copytree(join(self.repo.path, "backends", "allplan", "yaml"), join(out_core, "yaml"))

        # data, GeomModules
        if not exists(join(out_core, "data")):
            makedirs(join(out_core, "data"))
        if not exists(join(out_core, "allplan")):
            makedirs(join(out_core, "allplan"))

        for coll, in self.repo.itercollections():

            # Copy part data
            # Skip collection if no base file exists or licenses issues
            if not license.is_combinable_with(coll.license_name, args["target_license"]):
                print("Skip %s due to license issues" % coll.id)
                continue

            if not exists(join(self.repo.path, "allplan", coll.id, "%s.base" % coll.id)):
                # print("Skip %s due to missing base file" % coll.id)
                continue

            copy(join(self.repo.path, "data", "%s.blt" % coll.id), join(out_core, "data", "%s.blt" % coll.id))

            for base, classes in self.dbs["allplan"].iterbases(["base", "classes"], filter_collection=coll):
                base_name = splitext(base.filename)[0]
                # copy py file
                copy(join(self.repo.path, "allplan", coll.id, base.filename), join(out_core, "allplan", base.filename))

        # print self.repo.class_names
        # print vars(self.repo.class_names)
        # gui and py module files
        name_gui_file = 'BOLTS.pyp'
        name_module_file = 'BOLTS.py'
        choose_txt = "Auswahl"
        colletion_txt = "Bauteile"
        class_txt = "Bauteilklassen"

        # GUI, Allplan pyp file to create a GUI for a Allplan PythonPart
        pyp = ElementTree(file=join(self.repo.path, "backends", "allplan", "pyptemplate.xml"))
        # fill in script tag
        script = pyp.getroot().findall("Script")[0]
        SubElement(script, "Name").text = path_in_pyp_for_py + name_module_file
        SubElement(script, "Title").text = "BOLTS"
        SubElement(script, "Version").text = "1.0"
        element = pyp.getroot()
        page = SubElement(element, "Page")
        SubElement(page, "Name").text = "page1"
        SubElement(page, "Text").text = "BOLTS"

        # ComboBox with all collection ids
        # collect the collections
        coll_value_list = choose_txt
        for coll, in self.repo.itercollections():
            if not exists(join(self.repo.path, "allplan", coll.id, "%s.base" % coll.id)):
                # print("Skip %s due to missing base file" % coll.id)
                continue
            coll_value_list += "|"
            # coll_value_list += str(coll.id)
            coll_value_list += coll.name
        param = SubElement(page, "Parameter")
        SubElement(param, "Name").text = "CollectionName"
        SubElement(param, "Text").text = colletion_txt
        SubElement(param, "Value").text = choose_txt
        SubElement(param, "ValueList").text = coll_value_list
        SubElement(param, "ValueType").text = "StringComboBox"

        # Combobox with all Classes of this collection which have a base file
        for coll, in self.repo.itercollections():
            if not exists(join(self.repo.path, "allplan", coll.id, "%s.base" % coll.id)):
                # print("Skip %s due to missing base file" % coll.id)
                continue
            # print(vars(coll))
            print(coll.id)

            ################ test begin ################
            # try to exchange the cl.id with the name of the class but it is not as easy at it seams
            # due to the class name is an own class an not an attribut of the class
            class_value_list = choose_txt
            for name, multiname in self.dbs["allplan"].iternames(['name', 'multiname'], filter_collection=coll):
                # print(name)
                # print(vars(name))
                # print(vars(name.name))
                #print("  " + name.name.safe + " --> " + name.name.nice)
                pass
                class_value_list += "|"
                class_value_list += name.name.nice
            print(class_value_list)
            # hexscrew1 are missing due to missing name
            ################ test end ################


            class_value_list = choose_txt
            # collect the classes
            for base, classes in self.dbs["allplan"].iterbases(["base", "classes"], filter_collection=coll):
                for cl in classes:
                    # print(vars(cl))
                    # print("  " + cl.id + " --> " + splitext(base.filename)[0])
                    class_value_list += "|"
                    class_value_list += cl.id
            print(class_value_list)
            param = SubElement(page, "Parameter")
            SubElement(param, "Name").text = "ClassID_" + coll.id
            SubElement(param, "Text").text = class_txt
            SubElement(param, "Visible").text = "CollectionName == '" + coll.name + "'"
            SubElement(param, "Value").text = choose_txt
            SubElement(param, "ValueList").text = class_value_list
            SubElement(param, "ValueType").text = "StringComboBox"

            # gui element for each the keys and type and length and other keays
            for base, classes in self.dbs["allplan"].iterbases(["base", "classes"], filter_collection=coll):
                for cl in classes:
                    for pname in cl.parameters.free:
                        # print("  %s" % pname)
                        param = SubElement(page, "Parameter")
                        SubElement(param, "Name").text = "PName_" + pname + "_" + cl.id
                        SubElement(param, "Text").text = "%s (%s)" % (pname, cl.parameters.description[pname])
                        SubElement(param, "Visible").text = "CollectionName == '" + coll.name + "' and ClassID_" + coll.id + " == '" + cl.id + "'"
                        if cl.parameters.types[pname] == "Length (mm)":
                            SubElement(param, "Value").text = str(cl.parameters.defaults[pname])
                            SubElement(param, "ValueType").text = "Length"
                        elif cl.parameters.types[pname] == "Number":
                            SubElement(param, "Value").text = str(cl.parameters.defaults[pname])
                            SubElement(param, "ValueType").text = "Double"
                        elif cl.parameters.types[pname] == "Bool":
                            SubElement(param, "Value").text = str(cl.parameters.defaults[pname])
                            SubElement(param, "ValueType").text = "CheckBox"
                        elif cl.parameters.types[pname] == "Table Index":
                            SubElement(param, "Value").text = str(cl.parameters.defaults[pname])
                            SubElement(param, "ValueList").text = "|".join(cl.parameters.choices[pname])
                            SubElement(param, "ValueType").text = "StringComboBox"
                        elif cl.parameters.types[pname] == "String":
                            SubElement(param, "Value").text = str(cl.parameters.defaults[pname])
                            SubElement(param, "ValueType").text = "String"
                            pass
                        elif cl.parameters.types[pname] == "Angle (deg)":
                            SubElement(param, "Value").text = str(cl.parameters.defaults[pname])
                    SubElement(param, "ValueType").text = "Angle"
        # write the file and write it again, but much more pretty
        xmlfile = join(out_gui, name_gui_file)
        pyp.write(xmlfile)
        dom = xml.dom.minidom.parse(xmlfile)
        prettyxml = dom.toprettyxml(indent="    ", encoding="utf-8")
        # print(prettyxml)
        f = open(xmlfile, "w")
        f.write(prettyxml)
        f.close

        # pyguimodule Python modul for GUI to retrieve the BOLTS data and call the GeomModules
        with open(join(out_module, name_module_file), "w") as pyguimodule:
            pyguimodule.write(pyguitemplate_pre)
            pyguimodule.write("\n")
            for coll, in self.repo.itercollections():
                if not exists(join(self.repo.path, "allplan", coll.id, "%s.base" % coll.id)):
                    # print("Skip %s due to missing base file" % coll.id)
                    continue
                for base, classes in self.dbs["allplan"].iterbases(["base", "classes"], filter_collection=coll):
                    base_name = splitext(base.filename)[0]
                    for cl in classes:
                        # pyguimodule.write("    if bolts_coll_id == '" + coll.id + "':\n")
                        pyguimodule.write("    if bolts_coll_id == '" + coll.name + "':\n")
                        pyguimodule.write("        if build_ele.ClassID_" + coll.id + ".value == '" + cl.id + "':\n")
                        for pname in cl.parameters.free:
                            pname_line = "            params['" + pname + "'] = build_ele.PName_" + pname + "_" + cl.id + ".value"
                            pyguimodule.write(pname_line + "\n")
                        pyguimodule.write("            cl = repo.classes['" + cl.id + "']\n")
                        pyguimodule.write("            params = cl.parameters.collect(params)\n")
                        # pyguimodule.write("            print(params)\n")
                        pyguimodule.write("            import " + base_name + "\n")
                        pyguimodule.write("            bolt_part = " + base_name + "." + base_name + "(params)\n")
                        pyguimodule.write("\n")
            pyguimodule.write("    # print params used to create the Shape\n")
            pyguimodule.write("    print(params)\n")
            pyguimodule.write("\n")
            pyguimodule.write("    # common properties\n")
            pyguimodule.write("    com_prop = Ele.CommonProperties()\n")
            pyguimodule.write("    com_prop.GetGlobalProperties()\n")
            pyguimodule.write("\n")
            pyguimodule.write("    model_ele_list = [Ele.ModelElement3D(com_prop, bolt_part.Shape)]\n")
            pyguimodule.write("    return (model_ele_list, [])\n")
