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


# at the moment there is no differencd between HexScrew and HexBolt
# normaly the Thread (Gewinde) length is different
# the real length is in the params, see Internet and FreeCAD
# in FreeCAD the shank is made of twe cylinder to visualize the thread length


import NemAll_Python_Geometry as Geo
import GeometryValidate as Validate


class GeomHexScrew():
    def __init__(self, params):
        print('Init of Allplan class: ' + self.__class__.__name__)

        # set params
        w = params['s']  # head width
        t = params['k']  # head thickness
        l = params['l']  # length excluding head, shank length
        d = params['d1']  # screw diameter

        # build geometry
        self.Shape = make_screw_solid(w, t, l, d)


def make_screw_solid(w, t, l, d):
    head_width = w
    head_thickness = t
    bolt_shank_lenght = l
    screw_diameter = d

    #----------------- bolt_head
    bolt_head = make_hexagon_solid(head_width, head_thickness)

    #----------------- bolt_shank
    # origin_bolt_shank = Geo.AxisPlacement3D(Geo.Point3D(0, 0, -bolt_shank_lenght),
    origin_bolt_shank = Geo.AxisPlacement3D(Geo.Point3D(0, 0, 0), Geo.Vector3D(0, 1, 0), Geo.Vector3D(0, 0, 1))
    bolt_shank = Geo.BRep3D.CreateCylinder(origin_bolt_shank, 0.5 * screw_diameter,  bolt_shank_lenght)

    #------------------ union of bolt_head and bolt_shank
    err, screw = Geo.MakeUnion(bolt_head, bolt_shank)
    if Validate.polyhedron(err) and screw.IsValid():
        print('Screw without Error')

    return screw


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
