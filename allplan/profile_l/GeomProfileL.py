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


class GeomProfileL():
    def __init__(self, params):
        print('Init of Allplan class: ' + self.__class__.__name__)

        # set params
        print(params)
        a = params['a']
        t = params['t']
        r1 = params['r1']
        r2 = params['r2']
        length = params['l']

        # build geometry
        self.Shape = make_profile_l_solid(a, t, r1, r2, length)


def make_profile_l_solid(a, t, r1, r2, length):
    # rectangular without fillet

    # starting at the lower flanch, going against clockwise
    pol = Geo.Polygon3D()
    pol += Geo.Point3D( 0, 0, 0)
    pol += Geo.Point3D( a, 0, 0)
    pol += Geo.Point3D( a, t, 0)
    pol += Geo.Point3D( t, t, 0)
    pol += Geo.Point3D( t, a, 0)
    pol += Geo.Point3D( 0, a, 0)
    pol += Geo.Point3D( 0, 0, 0)

    area = Geo.PolygonalArea3D()
    area += pol
    extrusion = Geo.ExtrudedAreaSolid3D()
    extrusion.SetDirection(Geo.Vector3D(0, 0, length))
    #extrusion.SetRefPoint(Geo.Point3D(0, 0, 0))
    extrusion.SetExtrudedArea(area)

    err , polyhedron = Geo.CreatePolyhedron(extrusion)
    if err == Geo.eGeometryErrorCode.eOK:
        print('Solid without Error')

    return polyhedron
