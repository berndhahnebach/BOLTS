#BOLTS - Open Library of Technical Specifications
#Copyright (C) 2014 Bernd Hahnebach <bernd@bimstatik.org>
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#Lesser General Public License for more details.
#
#You should have received a copy of the GNU Lesser General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA


from FreeCAD import Vector
from Part import makeCircle, makeLine
import Part


def generic_circle(params,document):
        d = params['d']
        l = params['l']
        name = params['name']

        part = document.addObject("Part::Feature","BOLTS_part")
        part.Label = name

        part.Shape = Part.makeCylinder(0.5*d,l)

        
def generic_rectangle(params,document):
        h = params['h']
        b = params['b']
        l = params['l']
        name = params['name']

        part = document.addObject("Part::Feature","BOLTS_part")
        part.Label = name

        part.Shape = Part.makeBox(b,h,l)


def generic_pipe(params,document):
        id = params['id']
        od = params['od']
        l = params['l']
        name = params['name']

        if id > od:
                raise ValueError("Inner diameter must be smaller than outer diameter")

        if id == 0:
                raise ValueError("It's a pipe,inner diameter must be greater 0")

        part = document.addObject("Part::Feature","BOLTS_part")
        part.Label = name

        outer = Part.makeCylinder(0.5*od,l)
        inner = Part.makeCylinder(0.5*id,l)
        part.Shape = outer.cut(inner).removeSplitter()
        

def generic_hollow_rectangle(params,document):
        h = params['h']
        b = params['b']
        t = params['t']
        l = params['l']
        name = params['name']

        ## Definition in EN standard
        ri=1.0*t
        ro=1.5*t

        if t >= h/4 or t >= b/4 :
                raise ValueError("Height and Width must be greater than 4 x Webthickness")

        part = document.addObject("Part::Feature","BOLTS_part")
        part.Label = name

        # outer rectangle, going clockwise
        Vor1 = Vector((b/2),(h/2-ro),0)
        Vor2 = Vector((b/2),(-h/2+ro),0)
        Vor3 = Vector((b/2-ro),(-h/2),0)
        Vor4 = Vector((-b/2+ro),-h/2,0)
        Vor5 = Vector(-b/2,(-h/2+ro),0)
        Vor6 = Vector(-b/2,(h/2-ro),0)
        Vor7 = Vector((-b/2+ro),(h/2),0)
        Vor8 = Vector((b/2-ro),(h/2),0)
        Lor1 = makeLine(Vor1,Vor2)
        Lor2 = makeLine(Vor3,Vor4)
        Lor3 = makeLine(Vor5,Vor6)
        Lor4 = makeLine(Vor7,Vor8)

        # outer radius, going clockwise
        Voc1 = Vector((b/2-ro),(-h/2+ro),0)
        Voc2 = Vector((-b/2+ro),(-h/2+ro),0)
        Voc3 = Vector((-b/2+ro),(h/2-ro),0)
        Voc4= Vector((b/2-ro),(h/2-ro),0)
        normal = Vector(0,0,1)
        Coc1 = makeCircle(ro,Voc1,normal,270,  0)
        Coc2 = makeCircle(ro,Voc2,normal,180,270)
        Coc3 = makeCircle(ro,Voc3,normal, 90,180)
        Coc4 = makeCircle(ro,Voc4,normal,  0, 90)

        # inner rectangle, going clockwise
        Vir1 = Vector((b/2-t),(h/2-t-ri),0)
        Vir2 = Vector((b/2-t),(-h/2+t+ri),0)
        Vir3 = Vector((b/2-t-ri),(-h/2+t),0)
        Vir4 = Vector((-b/2+t+ri),(-h/2+t),0)
        Vir5 = Vector((-b/2+t),(-h/2+t+ri),0)
        Vir6 = Vector((-b/2+t),(h/2-t-ri),0)
        Vir7 = Vector((-b/2+t+ri),(h/2-t),0)
        Vir8 = Vector((b/2-t-ri),(h/2-t),0)
        Lir1 = makeLine(Vir1,Vir2)
        Lir2 = makeLine(Vir3,Vir4)
        Lir3 = makeLine(Vir5,Vir6)
        Lir4 = makeLine(Vir7,Vir8)

        # inner radius, going clockwise
        Vic1 = Vector((b/2-t-ri),(-h/2+t+ri),0)
        Vic2 = Vector((-b/2+t+ri),(-h/2+t+ri),0)
        Vic3 = Vector((-b/2+t+ri),(h/2-t-ri),0)
        Vic4= Vector((b/2-t-ri),(h/2-t-ri),0)
        normal = Vector(0,0,1)
        Cic1 = makeCircle(ri,Vic1,normal,270,  0)
        Cic2 = makeCircle(ri,Vic2,normal,180,270)
        Cic3 = makeCircle(ri,Vic3,normal, 90,180)
        Cic4 = makeCircle(ri,Vic4,normal,  0, 90)

        # putting the segments together, make wires, make faces, extrude them and cut them
        Wo = Part.Wire([Lor1,Coc1,Lor2,Coc2,Lor3,Coc3,Lor4,Coc4,])
        Wi = Part.Wire([Lir1,Cic1,Lir2,Cic2,Lir3,Cic3,Lir4,Cic4,])
        Fo = Part.Face(Wo)
        Fi = Part.Face(Wi)
        Po = Fo.extrude(Vector(0,0,l))
        Pi = Fi.extrude(Vector(0,0,l))
        beam = Po.cut(Pi) 
        part.Shape = beam


def generic_ibeam_pf(params,document):
        h = params['h']
        b = params['b']
        tf = params['tf']
        tw = params['tw']
        r = params ['r']
        l = params['l']
        name = params['name']

        part = document.addObject("Part::Feature","BOLTS_part")
        part.Label = name

        # lower flange, starting at the left web fillet, going against clockwise
        Vlf1 = Vector((-tw/2-r),(-h/2+tf),0)
        Vlf2 = Vector(-b/2,(-h/2+tf),0)
        Vlf3 = Vector(-b/2,-h/2,0)
        Vlf4 = Vector(b/2,-h/2,0)
        Vlf5 = Vector(b/2,(-h/2+tf),0)
        Vlf6 = Vector((tw/2+r),(-h/2+tf),0)
        Llf1 = makeLine(Vlf1,Vlf2)
        Llf2 = makeLine(Vlf2,Vlf3)
        Llf3 = makeLine(Vlf3,Vlf4)
        Llf4 = makeLine(Vlf4,Vlf5)
        Llf5 = makeLine(Vlf5,Vlf6)

        # upper flange, starting at the rigth web fillet, going clockwise
        Vuf1 = Vector(tw/2+r,(h/2-tf),0)
        Vuf2 = Vector(b/2,(h/2-tf),0)
        Vuf3 = Vector(b/2,h/2,0)
        Vuf4 = Vector(-b/2,h/2,0)
        Vuf5 = Vector(-b/2,(h/2-tf),0)
        Vuf6 = Vector((-tw/2-r),(h/2-tf),0)
        Luf1 = makeLine(Vuf1,Vuf2)
        Luf2 = makeLine(Vuf2,Vuf3)
        Luf3 = makeLine(Vuf3,Vuf4)
        Luf4 = makeLine(Vuf4,Vuf5)
        Luf5 = makeLine(Vuf5,Vuf6)

        # web, starting rigth bottom, going against clockwise
        Vw1 = Vector(tw/2,(-h/2+tf+r),0)
        Vw2 = Vector(tw/2,(h/2-tf-r),0)
        Vw3 = Vector(-tw/2,(h/2-tf-r),0)
        Vw4 = Vector(-tw/2,(-h/2+tf+r),0)
        Lw1 = makeLine(Vw1,Vw2)
        Lw2 = makeLine(Vw3,Vw4)

        # center of the fillets, starting right bottom, going against clockwise
        Vfc1 = Vector((tw/2+r),(-h/2+tf+r),0)
        Vfc2 = Vector((tw/2+r),(h/2-tf-r),0)
        Vfc3 = Vector((-tw/2-r),(h/2-tf-r),0)
        Vfc4 = Vector((-tw/2-r),(-h/2+tf+r),0)
        normal = Vector(0,0,1)
        Cfc1 = makeCircle(r,Vfc1,normal,180,270)
        Cfc2 = makeCircle(r,Vfc2,normal, 90,180)
        Cfc3 = makeCircle(r,Vfc3,normal,  0, 90)
        Cfc4 = makeCircle(r,Vfc4,normal,270,  0)

        # putting the segments together make a wire, a face and extrude it
        W = Part.Wire([Llf1,Llf2,Llf3,Llf4,Llf5,Cfc1,Lw1,Cfc2,Luf1,Luf2,Luf3,Luf4,Luf5,Cfc3,Lw2,Cfc4])
        F = Part.Face(W)
        beam = F.extrude(Vector(0,0,l))
        part.Shape = beam


def generic_cbeam_pf(params,document):
        h = params['h']
        b = params['b']
        tf = params['tf']
        tw = params['tw']
        r = params ['r']
        l = params['l']
        name = params['name']

        part = document.addObject("Part::Feature","BOLTS_part")
        part.Label = name

        # lower flange, starting at the ene of web, going against clockwise
        Vlf1 = Vector(0,(-h/2),0)
        Vlf2 = Vector(b,-h/2,0)
        Vlf3 = Vector(b,-h/2+tf,0)
        Vlf4 = Vector((tw+r),(-h/2+tf),0)
        Llf1 = makeLine(Vlf1,Vlf2)
        Llf2 = makeLine(Vlf2,Vlf3)
        Llf3 = makeLine(Vlf3,Vlf4)

        # upper flange, starting at the rigth web fillet, going clockwise
        Vuf1 = Vector(tw+r,(h/2-tf),0)
        Vuf2 = Vector(b,(h/2-tf),0)
        Vuf3 = Vector(b,h/2,0)
        Vuf4 = Vector(0,h/2,0)
        Luf1 = makeLine(Vuf1,Vuf2)
        Luf2 = makeLine(Vuf2,Vuf3)
        Luf3 = makeLine(Vuf3,Vuf4)

        # web, starting rigth bottom, going against clockwise
        Vw1 = Vector(tw,(-h/2+tf+r),0)
        Vw2 = Vector(tw,(h/2-tf-r),0)
        Lw1 = makeLine(Vw1,Vw2)
        Lw2 = makeLine(Vuf4 ,Vlf1)

        # center of the fillets, starting right bottom, going up
        Vfc1 = Vector((tw+r),(-h/2+tf+r),0)
        Vfc2 = Vector((tw+r),(h/2-tf-r),0)
        normal = Vector(0,0,1)
        Cfc1 = makeCircle(r,Vfc1,normal,180,270)
        Cfc2 = makeCircle(r,Vfc2,normal, 90,180)

        # putting the segments together make a wire, a face and extrude it
        W = Part.Wire([Llf1,Llf2,Llf3,Cfc1,Lw1,Cfc2,Luf1,Luf2,Luf3,Lw2])
        F = Part.Face(W)
        beam = F.extrude(Vector(0,0,l))
        part.Shape = beam


def generic_tbeam_pf(params,document):
        h = params['h']
        b = params['b']
        tf = params['tf']
        tw = params['tw']
        r = params ['r']
        l = params['l']
        name = params['name']

        part = document.addObject("Part::Feature","BOLTS_part")
        part.Label = name

        # upper flange, starting at the rigth web fillet, going clockwise
        Vuf1 = Vector(tw/2+r,(h/2-tf),0)
        Vuf2 = Vector(b/2,(h/2-tf),0)
        Vuf3 = Vector(b/2,h/2,0)
        Vuf4 = Vector(-b/2,h/2,0)
        Vuf5 = Vector(-b/2,(h/2-tf),0)
        Vuf6 = Vector((-tw/2-r),(h/2-tf),0)
        Luf1 = makeLine(Vuf1,Vuf2)
        Luf2 = makeLine(Vuf2,Vuf3)
        Luf3 = makeLine(Vuf3,Vuf4)
        Luf4 = makeLine(Vuf4,Vuf5)
        Luf5 = makeLine(Vuf5,Vuf6)

        # web, starting rigth bottom, going against clockwise
        Vw1 = Vector(tw/2,-h/2,0)
        Vw2 = Vector(tw/2,(h/2-tf-r),0)
        Vw3 = Vector(-tw/2,(h/2-tf-r),0)
        Vw4 = Vector(-tw/2,-h/2,0)
        Lw1 = makeLine(Vw1,Vw2)
        Lw2 = makeLine(Vw3,Vw4)
        Lw3 = makeLine(Vw4,Vw1)

        # center of the fillets, starting right bottom, going against clockwise
        Vfc2 = Vector((tw/2+r),(h/2-tf-r),0)
        Vfc3 = Vector((-tw/2-r),(h/2-tf-r),0)
        normal = Vector(0,0,1)
        Cfc2 = makeCircle(r,Vfc2,normal, 90,180)
        Cfc3 = makeCircle(r,Vfc3,normal,  0, 90)

        # putting the segments together make a wire, a face and extrude it
        W = Part.Wire([Lw1,Cfc2,Luf1,Luf2,Luf3,Luf4,Luf5,Cfc3,Lw2,Lw3])
        F = Part.Face(W)
        beam = F.extrude(Vector(0,0,l))
        part.Shape = beam


def generic_lbeam_pf(params,document):
        h = params['h']
        b = params['b']
        tf = params['tf']
        tw = params['tw']
        r = params ['r']
        l = params['l']
        name = params['name']

        part = document.addObject("Part::Feature","BOLTS_part")
        part.Label = name

        # lower flange, starting at the ene of web, going against clockwise
        Vlf1 = Vector(0,(-h/2),0)
        Vlf2 = Vector(b,-h/2,0)
        Vlf3 = Vector(b,-h/2+tf,0)
        Vlf4 = Vector((tw+r),(-h/2+tf),0)
        Llf1 = makeLine(Vlf1,Vlf2)
        Llf2 = makeLine(Vlf2,Vlf3)
        Llf3 = makeLine(Vlf3,Vlf4)

        # web, starting rigth bottom, going against clockwise
        Vw1 = Vector(tw,(-h/2+tf+r),0)
        Vw2 = Vector(tw,h/2,0)
        Vw3 = Vector(0,h/2,0)
        Lw1 = makeLine(Vw1,Vw2)
        Lw2 = makeLine(Vw2,Vw3)
        Lw3 = makeLine(Vw3 ,Vlf1)

        # center of the fillets, starting right bottom, going up
        Vfc1 = Vector((tw+r),(-h/2+tf+r),0)
        normal = Vector(0,0,1)
        Cfc1 = makeCircle(r,Vfc1,normal,180,270)

        # putting the segments together make a wire, a face and extrude it
        W = Part.Wire([Llf1,Llf2,Llf3,Cfc1,Lw1,Lw2,Lw3])
        F = Part.Face(W)
        beam = F.extrude(Vector(0,0,l))
        part.Shape = beam        