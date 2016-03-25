# ***************************************************************************
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

"""
Script for generation of bolts
"""

import NemAll_Python_Geometry as AllplanGeo
import NemAll_Python_Elements as AllplanElements
import NemAll_Python_Utility as AllplanUtil
import GeometryValidate as GeometryValidate

def check_allplan_version(build_ele, version):
    """
    Check the current Allplan version

    Args:
        build_ele: the building element.
        version:   the current Allplan version

    Returns:
        True/False if version is supported by this script
    """

    # Delete unused arguments
    del build_ele
    del version

    # Support all versions
    return True


def create_element(build_ele, doc):
    """
    Creation of element

    Args:
        build_ele: the building element.
        doc:       input document
    """

    model_ele_list = []
    handle_list = []
    reinf_ele_list = None

    #get the input values and check if they are valid
    params = {}
    params["key"] = build_ele.key.value
    params["l"] = build_ele.length.value

    repo = Repository(".")
    cl = repo.class_standards.get_src(repo.standards[build_ele.std])

    params = cl.parameters.collect(params)

    #build geometry
    bolt_head = make_hexagon_solid(params['e'], params['k'])

    origin_bolt_shank = AllplanGeo.AxisPlacement3D(AllplanGeo.Point3D(0, 0, -params["l"]),
                                                AllplanGeo.Vector3D(0, 1, 0),
                                                AllplanGeo.Vector3D(0, 0, 1))
    bolt_shank = AllplanGeo.BRep3D.CreateCylinder(origin_bolt_shank, 0.5 * params["d1"],  params['l'])

    err, screw = AllplanGeo.MakeUnion(bolt_head, bolt_shank)
    if not (GeometryValidate.polyhedron(err) or screw.IsValid()):
        print('Error generating geometry')

    #common properties
    com_prop = AllplanElements.CommonProperties()
    com_prop.GetGlobalProperties()
    com_prop.Pen = 1
    com_prop.Color = color

    model_ele_list.append(AllplanElements.ModelElement3D(com_prop, screw))

    return (self.model_ele_list, self.handle_list, self.reinf_ele_list)
