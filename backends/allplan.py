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

from errors import *

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
rootpath = join(dirname(__file__), "BoltsCore")
sys.path.append(rootpath)
sys.path.append(join(rootpath, "bolttools"))
sys.path.append(join(rootpath, "yaml"))

import bolttools.blt as BOLTSblt


def check_allplan_version(build_ele, version):
    return True  # Support all versions


def create_element(build_ele, doc):

    # path for Geom module, need to be inside the def for some reason ... ?!
    sys.path.append(dirname(__file__))

    # initialize tze BOLTS repo
    repo = BOLTSblt.Repository(rootpath)

    # initialize the BOLTS params dictionary
    params = {}

    # get the input values and fill params with them
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
        out_core = join(ver_root, "PythonPartsScripts", "BIMStatik", "BOLTS", "BoltsCore")
        out_module = join(ver_root, "PythonPartsScripts", "BIMStatik", "BOLTS")
        makedirs(out_gui)
        makedirs(out_core)

        # generate version file
        date = datetime.now()
        with open(join(ver_root, "VERSION"), "w") as version_file:
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

        # data, modules, gui
        if not exists(join(out_core, "data")):
            makedirs(join(out_core, "data"))

        for coll, in self.repo.itercollections():

            # Copy part data
            # Skip collection if no base file exists or licenses issues
            if not license.is_combinable_with(coll.license_name, args["target_license"]):
                print("Skip %s due to license issues" % coll.id)
                continue

            if not exists(join(self.repo.path, "allplan", coll.id, "%s.base" % coll.id)):
                print("Skip %s due to missing base file" % coll.id)
                continue

            copy(join(self.repo.path, "data", "%s.blt" % coll.id), join(out_core, "data", "%s.blt" % coll.id))

            for base, classes in self.dbs["allplan"].iterbases(["base", "classes"], filter_collection=coll):
                base_name = splitext(base.filename)[0]
                # copy py file
                copy(join(self.repo.path, "allplan", coll.id, base.filename), out_module)

                # create py gui file
                pyguiname = 'gui_' + base.filename
                with open(join(out_module, pyguiname), "w") as pyguifile:
                    pyguifile.write(pyguitemplate_pre)
                    pyguifile.write("    bolts_std_id = build_ele.Standard.value\n")
                    pyguifile.write("\n")
                    for std, cl in self.dbs["allplan"].iterstandards(["standard", "class"], filter_base=base):
                        stdid = str(std.get_id())
                        if_line = "    if bolts_std_id == '" + stdid + "':"
                        pyguifile.write(if_line + "\n")
                        for pname in cl.parameters.free:
                            pname_line = "        params['" + pname + "'] = build_ele." + pname + stdid + ".value"
                            pyguifile.write(pname_line + "\n")
                        pyguifile.write("\n")
                    pyguifile.write("\n")
                    pyguifile.write("    # get the BOLTS geometry values and write them to params too\n")
                    pyguifile.write("    cl = repo.class_standards.get_src(repo.standards[bolts_std_id])\n")
                    pyguifile.write("    params = cl.parameters.collect(params)\n")
                    pyguifile.write("    print(params)\n")
                    pyguifile.write("\n")
                    pyguifile.write("    # build geometry\n")
                    # pyguifile.write("    sys.path.append(dirname(__file__))\n")
                    pyguifile.write("    import " + base_name + "\n")
                    pyguifile.write("    bolt_part = " + base_name + "." + base_name + "(params)\n")
                    pyguifile.write("\n")
                    pyguifile.write("    # common properties\n")
                    pyguifile.write("    com_prop = Ele.CommonProperties()\n")
                    pyguifile.write("    com_prop.GetGlobalProperties()\n")
                    pyguifile.write("\n")
                    pyguifile.write("    model_ele_list = [Ele.ModelElement3D(com_prop, bolt_part.Shape)]\n")
                    pyguifile.write("    return (model_ele_list, [])\n")

                # Generate a pyp file for each class
                pyp = ElementTree(file=join(self.repo.path, "backends", "allplan", "pyptemplate.xml"))
                # fill in script tag
                script = pyp.getroot().findall("Script")[0]
                SubElement(script, "Name").text = "BIMStatik\\BOLTS\\" + pyguiname
                SubElement(script, "Title").text = "BOLTS - " + base.filename
                SubElement(script, "Version").text = "1.0"

                element = pyp.getroot()
                page = SubElement(element, "Page")
                SubElement(page, "Name").text = "page1"
                SubElement(page, "Text").text = "BOLTS - " + base.filename

                # ComboBox with all standards
                # SubElement(page,"Name").text = std.standard.get_nice()
                # SubElement(page,"Name").text = std.get_id()
                # may be there is some better way to retrieve the standars ...
                std_value_list = ""
                std_last_value = ""
                for std, cl in self.dbs["allplan"].iterstandards(["standard", "class"], filter_base=base):
                    # print(std.get_id())
                    std_value_list += str(std.get_id())
                    std_value_list += "|"
                    std_last_value = str(std.get_id())
                std_value_list = std_value_list[:-1]  # cut the last | from string
                # print(std_value_list)
                param = SubElement(page, "Parameter")
                SubElement(param, "Name").text = "Standard"
                SubElement(param, "Text").text = "Norm, Standard, Code"
                SubElement(param, "Value").text = std_last_value
                SubElement(param, "ValueList").text = std_value_list
                SubElement(param, "ValueType").text = "StringComboBox"

                for std, cl in self.dbs["allplan"].iterstandards(["standard", "class"], filter_base=base):
                    for pname in cl.parameters.free:

                        param = SubElement(page, "Parameter")
                        # SubElement(param,"Name").text = pname
                        SubElement(param, "Name").text = pname + std.get_id()
                        SubElement(param, "Text").text = "%s (%s)" % (pname, cl.parameters.description[pname])
                        SubElement(param, "Visible").text = "Standard == '" + std.get_id() + "'"

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

                xmlfile = join(out_gui, "%s.pyp" % base_name)
                pyp.write(xmlfile)
                dom = xml.dom.minidom.parse(xmlfile)
                prettyxml = dom.toprettyxml(indent="    ", encoding="utf-8")
                # print(prettyxml)
                f = open(xmlfile, "w")
                f.write(prettyxml)
                f.close


        ##############################################################################
        ##############################################################################
        ##############################################################################
        pyguiname = 'gui_BOLTS.py'
        # try one big BOLTS pyp file

        # GUI, pyp file
        pyp = ElementTree(file=join(self.repo.path, "backends", "allplan", "pyptemplate.xml"))
        # fill in script tag
        script = pyp.getroot().findall("Script")[0]
        #SubElement(script, "Name").text = "BIMStatik\\BOLTS\\" + "gui_GeomProfileI.py"  # PENDENT!!!
        SubElement(script, "Name").text = "BIMStatik\\BOLTS\\" + pyguiname
        SubElement(script, "Title").text = "BOLTS"
        SubElement(script, "Version").text = "1.0"

        element = pyp.getroot()
        page = SubElement(element, "Page")
        SubElement(page, "Name").text = "page1"
        SubElement(page, "Text").text = "BOLTS"

        # ComboBox with all collection ids
        # collect the collections
        print("\n\nTry to make one big BOLTS pyp")
        coll_value_list = "Choose"
        for coll, in self.repo.itercollections():
            if not exists(join(self.repo.path, "allplan", coll.id, "%s.base" % coll.id)):
                # print("Skip %s due to missing base file" % coll.id)
                continue
            else:
                print("Include %s" % coll.id)
            # print coll.id
            coll_value_list += "|"
            coll_value_list += str(coll.id)
        print coll_value_list
        param = SubElement(page, "Parameter")
        SubElement(param, "Name").text = "CollectionID"
        SubElement(param, "Text").text = "CollectionID PalleteText"
        SubElement(param, "Value").text = "Choose"
        SubElement(param, "ValueList").text = coll_value_list
        SubElement(param, "ValueType").text = "StringComboBox"



        for coll, in self.repo.itercollections():
            if not exists(join(self.repo.path, "allplan", coll.id, "%s.base" % coll.id)):
                # print("Skip %s due to missing base file" % coll.id)
                continue
            print(coll.id)
            class_value_list = "Choose"
            for base, classes in self.dbs["allplan"].iterbases(["base", "classes"], filter_collection=coll):
                for cl in classes:
                    print("  " + cl.id + " --> " + splitext(base.filename)[0])
                    class_value_list += "|"
                    class_value_list += cl.id
                print class_value_list
            param = SubElement(page, "Parameter")
            SubElement(param, "Name").text = "ClassID_" + coll.id
            SubElement(param, "Text").text = "Collection Classes"
            SubElement(param, "Visible").text = "CollectionID == '" + coll.id + "'"
            SubElement(param, "Value").text = "Choose"
            SubElement(param, "ValueList").text = class_value_list
            SubElement(param, "ValueType").text = "StringComboBox"


            # now we need the keys and types and Length and other keays like in all pyp for each class
            for base, classes in self.dbs["allplan"].iterbases(["base", "classes"], filter_collection=coll):
                for cl in classes:
                    for pname in cl.parameters.free:
                        # print ("  %s" % pname)
                        param = SubElement(page, "Parameter")
                        SubElement(param, "Name").text = "PName_" + pname + "_" + cl.id
                        SubElement(param, "Text").text = "%s (%s)" % (pname, cl.parameters.description[pname])
                        SubElement(param, "Visible").text = "CollectionID == '" + coll.id + "' and ClassID_" + coll.id + " == '" + cl.id + "'"

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

        # write the file and writ it again, but much more pretty
        xmlfile = join(out_gui, "BOLTS.pyp")
        pyp.write(xmlfile)
        dom = xml.dom.minidom.parse(xmlfile)
        prettyxml = dom.toprettyxml(indent="    ", encoding="utf-8")
        # print(prettyxml)
        f = open(xmlfile, "w")
        f.write(prettyxml)
        f.close


        # py modul for GUI to retrieve the BOLTS data
        with open(join(out_module, pyguiname), "w") as pyguifile:
            pyguifile.write(pyguitemplate_pre)
            pyguifile.write("    bolts_coll_id = build_ele.CollectionID.value\n")
            # pyguifile.write("    print(bolts_coll_id)\n")
            pyguifile.write("\n")
            for coll, in self.repo.itercollections():
                if not exists(join(self.repo.path, "allplan", coll.id, "%s.base" % coll.id)):
                    # print("Skip %s due to missing base file" % coll.id)
                    continue
                for base, classes in self.dbs["allplan"].iterbases(["base", "classes"], filter_collection=coll):
                    base_name = splitext(base.filename)[0]
                    for cl in classes:
                        if_coll_line = "    if bolts_coll_id == '" + coll.id + "':"
                        cl_id_line = "        bolts_cl_id = build_ele.ClassID_" + coll.id + ".value"
                        if_cl_line = "        if bolts_cl_id == '" + cl.id + "':"
                        pyguifile.write(if_coll_line + "\n")
                        pyguifile.write(cl_id_line + "\n")
                        # pyguifile.write("        print(bolts_cl_id)\n")
                        pyguifile.write(if_cl_line + "\n")
                        for pname in cl.parameters.free:
                            pname_line = "            params['" + pname + "'] = build_ele.PName_" + pname + "_" + cl.id + ".value"
                            pyguifile.write(pname_line + "\n")
                        pyguifile.write("            cl = repo.classes['" + cl.id + "']\n")
                        pyguifile.write("            params = cl.parameters.collect(params)\n")
                        pyguifile.write("            print(params)\n")
                        pyguifile.write("            import " +  base_name + "\n")
                        pyguifile.write("            bolt_part = " + base_name + "." + base_name + "(params)\n")
                        pyguifile.write("\n")
            pyguifile.write("\n")
            pyguifile.write("    # common properties\n")
            pyguifile.write("    com_prop = Ele.CommonProperties()\n")
            pyguifile.write("    com_prop.GetGlobalProperties()\n")
            pyguifile.write("\n")
            pyguifile.write("    model_ele_list = [Ele.ModelElement3D(com_prop, bolt_part.Shape)]\n")
            pyguifile.write("    return (model_ele_list, [])\n")
