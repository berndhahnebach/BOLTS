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


class GeomProfileHollowCircle():
    def __init__(self, params):
        print('Init of Allplan class: ' + self.__class__.__name__)

        # set params
        print(params)
        od = params['D']  # outer diameter
        t = params['t']  # thickness
        length = params['l']  # profile length

        # build geometry
        self.Shape = make_hollow_circle_solid(od, t, length)


def make_hollow_circle_solid(od, t, length):
    origin = Geo.AxisPlacement3D(Geo.Point3D(0, 0, 0), Geo.Vector3D(0, 1, 0), Geo.Vector3D(0, 0, 1))
    outer = Geo.BRep3D.CreateCylinder(origin, 0.5 * od, length)
    inner = Geo.BRep3D.CreateCylinder(origin, 0.5 * (od - t), length)

    #------------------ Subtraction
    err, solid = Geo.MakeSubtraction(outer, inner)
    #if Validate.solid(err) and solid.IsValid():
    #    print('solid without Error')
    # siehe nut errorpruefung dort steht polyhedron ... 

    return solid
