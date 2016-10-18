# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Bernd Hahnebach <bernd@bimstatik.org>            *
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


import NemAll_Python_Geometry as Geo
import GeometryValidate as Validate


class GeomNut():
    def __init__(self, params):
        print('Init of Allplan class: ' + self.__class__.__name__)

        # set params
        w = params['s']  # width
        t = params['m_max']  # thickness
        d = params['d1']  # hole diameter

        # build geometry
        self.Shape = make_nut_solid(w, t, d)


def make_nut_solid(w, t, d):
    screw_diameter = d
    nut_width = w
    nut_thickness = t

    #----------------- nut_without_hole
    nut_without_hole = make_hexagon_solid(nut_width, nut_thickness)

    #----------------- hole
    origin = Geo.AxisPlacement3D(Geo.Point3D(0, 0, -nut_thickness), Geo.Vector3D(0, 1, 0), Geo.Vector3D(0, 0, 1))
    nut_hole = Geo.BRep3D.CreateCylinder(origin, 0.5 * screw_diameter,  3 * nut_thickness)

    #------------------ Subtraction
    err, nut = Geo.MakeSubtraction(nut_without_hole, nut_hole)
    if Validate.polyhedron(err) and nut.IsValid():
        print('Nut without Error')

    return nut


def make_hexagon_solid(a, t):
    import math
    d = a / math.sqrt(3)
    # a .. width
    # d .. inner hexagon diameter

    origin = Geo.AxisPlacement3D(Geo.Point3D(0, 0, 0), Geo.Vector3D(0, 1, 0), Geo.Vector3D(0, 0, 1))

    solid1 = Geo.BRep3D.CreateCuboid(origin, a, d, t)
    translation = Geo.Matrix3D()
    translation.Translate(Geo.Vector3D(0.5 * d, -0.5 * a, 0))
    solid1 = Geo.Transform(solid1, translation)

    rotation = Geo.Matrix3D()
    rotation_axis = Geo.Line3D(Geo.Point3D(0,0,0),Geo.Point3D(0,0,1))
    rotation_angle = Geo.Angle(math.pi / 3.0)
    rotation.Rotation(rotation_axis, rotation_angle)
    solid2 = Geo.Transform(solid1, rotation)

    rotation = Geo.Matrix3D()
    rotation_axis = Geo.Line3D(Geo.Point3D(0,0,0),Geo.Point3D(0,0,1))
    rotation_angle = Geo.Angle(math.pi * 2 / 3.0)
    rotation.Rotation(rotation_axis, rotation_angle)
    solid3 = Geo.Transform(solid1, rotation)

    # union of solids
    hexagon_solid = Geo.MakeUnion(solid1, solid2)[1]
    hexagon_solid = Geo.MakeUnion(hexagon_solid, solid3)[1]

    return hexagon_solid
