# -*- coding: utf-8 -*-

import OpenGL.GL as gl
import OpenGL.GLU as glu
#import OpenGL.GLUT as glut

from PyQt5 import QtWidgets as qWidget


#from TInterface import Calculator
#from AdvancedTools import TPeriodTable
from AdvancedTools import TAtomicModel
from AdvancedTools import TCalculators
#from AdvancedTools import Helpers
import math
#import matplotlib.cm as cm
import numpy as np

class GuiOpenGL(object):
    def __init__(self, widget):
        """constructor"""
        self.openGLWidget = widget
        self.MainModel = TAtomicModel()
        self.ViewOrtho = True
        self.ViewBox = False
        self.ViewBonds = True
        self.ViewSurface = False
        self.ViewContour = False
        self.ViewContourFill = False
        self.ViewVoronoi = False
        self.active = False
        self.QuadObjS = []
        self.object = None
        self.NLists = 8
        self.Scale = 1
        self.xsOld = 0
        self.ysOld = 0
        self.xScene = 0
        self.yScene = 0
        self.x = 0
        self.y = 0
        self.z = -20
        self.rotX = 0
        self.rotY = 0
        self.rotZ = 0
        self.CanSearch = False
        self.selected_atom = -1
        self.ProbeXYZ = False

    def isActive(self):
        return self.active

    def isAtomSelected(self):
        return self.selected_atom >=0

    def copy_state(self, GUI):
        self.rotX = GUI.rotX
        self.rotY = GUI.rotY
        self.rotZ = GUI.rotZ
        self.ViewOrtho = GUI.ViewOrtho
        self.ViewBox = GUI.ViewBox
        self.ViewBonds = GUI.ViewBonds
        self.ViewSurface = GUI.ViewSurface
        self.ViewContour = GUI.ViewContour
        self.ViewVoronoi = GUI.ViewVoronoi
        self.ViewContourFill = GUI.ViewContourFill
        self.x = GUI.x
        self.y = GUI.y
        self.z = GUI.z
        self.Scale = GUI.Scale
        self.selected_atom = GUI.selected_atom
        self.MainModel = GUI.MainModel
        self.color_of_atoms = GUI.color_of_atoms
        self.color_of_bonds = GUI.color_of_bonds
        self.color_of_box = GUI.color_of_box

        self.add_atoms()
        self.add_bonds()
        self.add_box()
        if self.ViewVoronoi:
            self.color_of_voronoi = GUI.color_of_voronoi
            self.add_voronoi(self.color_of_voronoi)
        if self.ViewContour:
            self.add_contour(GUI.data_contour)
        if self.ViewContourFill:
            self.add_colored_plane(GUI.data_contour_fill)
        if self.ViewSurface:
            self.add_surface(GUI.data_surface)

        self.openGLWidget.update()
        
    def screen2space(self, x, y, width, height):
        radius = min(width, height)*float(self.Scale)
        return (2.*x-width)/radius, -(2.*y-height)/radius

    def set_atomic_structure(self, structure, atomscolors, ViewBox, boxcolor, ViewBonds, bondscolor, bondWidth):
        self.clean()
        self.MainModel = structure
        self.ViewBox = ViewBox
        self.ViewBonds = ViewBonds
        self.bondWidth = bondWidth
        self.ViewSurface = False
        self.ViewContour = False
        self.ViewContourFill = False
        self.active = False
        self.color_of_atoms = atomscolors
        self.add_atoms()
        self.color_of_bonds = bondscolor
        self.color_of_box = boxcolor
        self.MainModel.FindBonds()
        self.add_bonds()
        self.add_box()
        self.openGLWidget.update()


    def save_to_file(self, fname):
        self.openGLWidget.grab().save(fname)

    def set_color_of_atoms(self, colors):
        self.color_of_atoms = colors
        self.add_atoms()

    def set_color_of_bonds(self,color):
        self.color_of_bonds = color
        self.add_bonds()

    def set_color_of_voronoi(self,voronoicolor):
        self.add_voronoi(voronoicolor)

    def set_color_of_box(self,color):
        self.color_of_box = color
        self.add_box()

    def set_box_visible(self, state):
        self.ViewBox = state
        self.openGLWidget.update()

    def set_bonds_visible(self, state):
        self.ViewBonds = state
        self.openGLWidget.update()
    
    def scale(self, wheel):
        if self.active == True:
            self.Scale += 0.05*(wheel/120)
            self.openGLWidget.update()
            return True
    
    def rotat(self, x, y, width, height):
        if self.active == True:
            xs, ys = self.screen2space(x, y, width, height)
            self.rotY += 10*(xs-self.xsOld)
            self.rotX -= 10*(ys-self.ysOld)
            return True
    
    def move(self, x, y, width, height):
        if self.active == True:
            xs, ys = self.screen2space(x, y, width, height)
            self.x +=xs-self.xsOld
            self.y +=ys-self.ysOld
            self.xsOld = xs
            self.ysOld = ys
            return True
   
    def setXY(self, x, y, width, height):
        if self.active == True:
            self.xsOld, self.ysOld = self.screen2space(x, y, width, height)
            self.xScene, self.yScene = x, y
            self.openGLWidget.update()
            return True

    def move_atom(self, x, y, width, height):
        if self.active == True:
            if self.ProbeXYZ == False:
                self.ProbeXYZ = True
                self.xScene, self.yScene = x, y
                self.openGLWidget.update()
                self.add_atoms()
                self.ViewVoronoi = False
                self.ViewSurface = False
                self.ViewContourFill = False
                self.ViewContour = False
            return True

    # рисует связь между атомами в виде цилиндра
    def add_bond(self, Atom1Pos, Atom2Pos, Radius=0.1):
        Rel = [Atom2Pos[0]-Atom1Pos[0], Atom2Pos[1]-Atom1Pos[1], Atom2Pos[2]-Atom1Pos[2]]
        BindingLen = math.sqrt(math.pow(Rel[0],2) + math.pow(Rel[1],2) + math.pow(Rel[2],2)) # высота цилиндра
        assert(BindingLen != 0)
        Fall = 180.0/math.pi*math.acos(Rel[2] / BindingLen)
        Yaw = 180.0/math.pi*math.atan2(Rel[1], Rel[0])
       
        gl.glPushMatrix()
        gl.glTranslated(Atom1Pos[0], Atom1Pos[1], Atom1Pos[2]) # преобразование координат № 3
        gl.glRotated(Yaw, 0, 0, 1) # преобразование координат № 2
        gl.glRotated(Fall, 0, 1, 0) # преобразование координат № 1
        glu.gluCylinder(glu.gluNewQuadric(),
            Radius, # /*baseRadius:*/
            Radius, # /*topRadius:*/
            BindingLen, # /*height:*/
            15, # /*slices:*/
            1) #/*stacks:*/
        gl.glPopMatrix()

    def clean(self):
        if self.active == True:
            gl.glDeleteLists(self.object, self.NLists)
        self.object = gl.glGenLists(self.NLists)

    def add_selected_atom(self):
        gl.glNewList(self.object+7, gl.GL_COMPILE)
        for at in self.MainModel.atoms:
            if at.isSelected() == True:
                gl.glPushMatrix()
                gl.glTranslatef(at.x, at.y, at.z)
                self.QuadObjS.append(glu.gluNewQuadric())
                gl.glColor3f(1, 0, 0)
                glu.gluSphere(self.QuadObjS[-1], 0.35, 70, 70)
                gl.glPopMatrix()
        gl.glEndList()
        
    def add_atoms(self):
        gl.glNewList(self.object, gl.GL_COMPILE)
        for at in self.MainModel.atoms:            
            gl.glPushMatrix()
            gl.glTranslatef(at.x, at.y, at.z)
            self.QuadObjS.append(glu.gluNewQuadric())

            if at.isSelected() == False:
                color = self.color_of_atoms[at.charge]
                gl.glColor3f(color[0], color[1], color[2])
                glu.gluSphere(self.QuadObjS[-1], 0.3, 70, 70)
            else:
                gl.glColor3f(1, 0, 0)
                glu.gluSphere(self.QuadObjS[-1], 0.35, 70, 70)
            gl.glPopMatrix()
        gl.glEndList()
        self.active = True

    def add_bonds(self):
        gl.glNewList(self.object + 2, gl.GL_COMPILE)
        gl.glColor3f(self.color_of_bonds[0], self.color_of_bonds[1], self.color_of_bonds[2])
        for bond in self.MainModel.bonds:
            x1 = self.MainModel.atoms[bond[0]].x
            y1 = self.MainModel.atoms[bond[0]].y
            z1 = self.MainModel.atoms[bond[0]].z

            x2 = self.MainModel.atoms[bond[1]].x
            y2 = self.MainModel.atoms[bond[1]].y
            z2 = self.MainModel.atoms[bond[1]].z

            self.add_bond([x1, y1, z1], [x2, y2, z2], self.bondWidth)
        gl.glEndList()

    def add_box(self):
        gl.glNewList(self.object + 3, gl.GL_COMPILE)
        gl.glColor3f(self.color_of_box[0], self.color_of_box[1], self.color_of_box[2])

        minX = self.MainModel.minX()
        minY = self.MainModel.minY()
        minZ = self.MainModel.minZ()

        origin = np.array([minX, minY, minZ])
        v1 = self.MainModel.LatVect1
        v2 = self.MainModel.LatVect2
        v3 = self.MainModel.LatVect3

        p1 = origin
        p2 = origin + v1
        p3 = origin + v2
        p4 = p2 + v2
        p5 = origin + v3
        p6 = p2 + v3
        p7 = p3 + v3
        p8 = p4 + v3

        width = 0.03
        self.add_bond(p1, p2, width)
        self.add_bond(p1, p3, width)
        self.add_bond(p1, p5, width)
        self.add_bond(p2, p4, width)
        self.add_bond(p2, p6, width)
        self.add_bond(p3, p4, width)
        self.add_bond(p3, p7, width)
        self.add_bond(p4, p8, width)
        self.add_bond(p5, p6, width)
        self.add_bond(p5, p7, width)
        self.add_bond(p6, p8, width)
        self.add_bond(p7, p8, width)
        gl.glEndList()

    def add_surface(self, data):
        self.data_surface = data
        gl.glNewList(self.object + 4, gl.GL_COMPILE)
        for surf in data:
            verts = surf[0]
            faces = surf[1]
            color = surf[2]
            gl.glColor4f(color[0], color[1], color[2], color[3])
            for face in faces:
                gl.glBegin(gl.GL_TRIANGLES)
                for point in face:
                    gl.glVertex3f(verts[point][0], verts[point][1], verts[point][2])
                gl.glEnd()
        gl.glEndList()
        self.ViewSurface = True
        self.openGLWidget.update()

    def add_contour(self, params):
        self.data_contour = params
        gl.glDeleteLists(self.object + 5, 1)
        gl.glNewList(self.object + 5, gl.GL_COMPILE)

        for param in params:
            values = param[0]
            conts = param[1]
            colors = param[2]
            it = 0
            for cont in conts:
                color = colors[it]
                it += 1
                gl.glColor3f(color[0], color[1], color[2])

                for contour in cont:
                    for i in range(0,len(contour)-1):
                        p1 = contour[i]
                        p2 = contour[i+1]
                        width = 0.03
                        self.add_bond(p1, p2, width)
        gl.glEndList()
        self.ViewContour = True
        self.openGLWidget.update()

    def add_colored_plane(self, data):
        self.data_contour_fill = data
        gl.glDeleteLists(self.object + 6, 1)
        gl.glNewList(self.object + 6, gl.GL_COMPILE)
        for plane in data:
            points = plane[0]
            colors = plane[1]
            Nx = len(points)
            Ny = len(points[0])
            gl.glBegin(gl.GL_TRIANGLES)
            for i in range(0, Nx-1):
                for j in range(0, Ny-1):
                    gl.glColor3f(colors[i][j][0], colors[i][j][1], colors[i][j][2])
                    gl.glVertex3f(points[i][j][0], points[i][j][1], points[i][j][2])
                    gl.glColor3f(colors[i+1][j][0], colors[i+1][j][1], colors[i+1][j][2])
                    gl.glVertex3f(points[i+1][j][0], points[i+1][j][1], points[i+1][j][2])
                    gl.glColor3f(colors[i][j+1][0], colors[i][j+1][1], colors[i][j+1][2])
                    gl.glVertex3f(points[i][j+1][0], points[i][j+1][1], points[i][j+1][2])
                    gl.glColor3f(colors[i][j+1][0], colors[i][j+1][1], colors[i][j+1][2])
                    gl.glVertex3f(points[i][j+1][0], points[i][j+1][1], points[i][j+1][2])
                    gl.glColor3f(colors[i + 1][j][0], colors[i + 1][j][1], colors[i + 1][j][2])
                    gl.glVertex3f(points[i + 1][j][0], points[i + 1][j][1], points[i + 1][j][2])
                    gl.glColor3f(colors[i + 1][j+1][0], colors[i + 1][j+1][1], colors[i + 1][j+1][2])
                    gl.glVertex3f(points[i + 1][j+1][0], points[i + 1][j+1][1], points[i + 1][j+1][2])
            gl.glEnd()
        gl.glEndList()
        self.ViewContourFill = True
        self.openGLWidget.update()

    def add_voronoi(self, color, maxDist):
        self.color_of_voronoi = color
        volume = np.inf
        if self.selected_atom >=0:
            ListOfPoligons, volume = TCalculators.VoronoiAnalisis(self.MainModel, self.selected_atom, maxDist)

            gl.glNewList(self.object+1, gl.GL_COMPILE)
            gl.glColor4f(color[0], color[1], color[2], 0.7)
            for poligon in ListOfPoligons:
                gl.glBegin(gl.GL_POLYGON)
                for point in poligon:
                    gl.glVertex3f(point[0], point[1], point[2])
                gl.glEnd()
            gl.glEndList()
            self.ViewVoronoi = True
            self.openGLWidget.update()
        return self.selected_atom, volume

    def paintGL(self):
        qWidget.QOpenGLWidget.makeCurrent(self.openGLWidget)
        ambient = [1.0, 1.0, 1.0, 0.04]
        lightpos = [1.0, 10.0, 100.0]
        gl.glLightModelfv(gl.GL_LIGHT_MODEL_AMBIENT, ambient) # Определяем текущую модель освещения
        gl.glEnable (gl.GL_LIGHTING)
        gl.glEnable (gl.GL_LIGHT0)
        gl.glEnable (gl.GL_DEPTH_TEST)
        gl.glEnable (gl.GL_COLOR_MATERIAL)
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, lightpos)     # Определяем положение источника света
        try:
            gl.glClearColor(1.0, 1.0, 1.0, 1.0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            gl.glMatrixMode(gl.GL_PROJECTION)
            gl.glLoadIdentity()
            x, y, width, height = gl.glGetDoublev(gl.GL_VIEWPORT)
            
            if self.ViewOrtho == False:
                glu.gluPerspective(
                    45,  # field of view in degrees
                    width / float(height or 1),  # aspect ratio
                    .25,  # near clipping plane
                    200)  # far clipping plane            
            else:
                radius = .5 * min(width, height)
                w, h = width/radius, height/radius
            
                gl.glOrtho(-2*w,    # GLdouble left
                    2*w,    # GLdouble right
                    -2*h,    # GLdouble bottom
                    2*h, # GLdouble top
                    -0.25, # GLdouble near
                    200.0)  # GLdouble far
            
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glLoadIdentity()

            if self.active:
                gl.glTranslated(self.x, self.y, self.z)

                gl.glRotate(self.rotX, 1, 0, 0)
                gl.glRotate(self.rotY, 0, 1, 0)
                gl.glRotate(self.rotZ, 0, 0, 1)

                gl.glScale(self.Scale, self.Scale, self.Scale)

                if self.ProbeXYZ:
                    self.add_selected_atom()
                    gl.glCallList(self.object + 7)  # selected atom

                    point = self.get_point_in_3D(self.xScene, self.yScene)
                    if abs(self.MainModel.atoms[self.selected_atom].x - point[0]) < 0.2:
                        self.MainModel.atoms[self.selected_atom].x = point[0]
                    if abs(self.MainModel.atoms[self.selected_atom].y + point[1]) < 0.2:
                        self.MainModel.atoms[self.selected_atom].y = - point[1]
                    if abs(self.MainModel.atoms[self.selected_atom].z - point[2]) < 0.2:
                        self.MainModel.atoms[self.selected_atom].z = point[2]
                    self.add_atoms()
                    gl.glCallList(self.object)  # atoms
                    self.add_bonds()
                    if self.ViewBonds:
                        gl.glCallList(self.object + 2)  # Bonds
                else:
                    gl.glCallList(self.object)  # atoms

                    if self.CanSearch:
                        self.get_atom_on_screen()

                    if self.ViewBonds:
                        gl.glCallList(self.object + 2)  # Bonds

                    if self.ViewVoronoi:
                        gl.glCallList(self.object + 1)  # Voronoi

                    if self.ViewBox:
                        gl.glCallList(self.object + 3)  # lattice_parameters_abc_angles

                    if self.ViewSurface:
                        gl.glCallList(self.object + 4)  # Surface

                    if self.ViewContour:
                        gl.glCallList(self.object + 5)  # Contour

                    if self.ViewContourFill:
                        gl.glCallList(self.object + 6)  # ContourFill

        except Exception as exc:
            print(exc)
            pass

    def get_atom_on_screen(self):
        point = self.get_point_in_3D(self.xScene, self.yScene)
        oldSelected = self.selected_atom
        minr = 10000
        ind = -1
        for at in range(0, len(self.MainModel.atoms)):
            r = math.sqrt( (point[0]-self.MainModel.atoms[at].x)**2 + (-point[1]-self.MainModel.atoms[at].y)**2 + (point[2]-self.MainModel.atoms[at].z)**2 )
            if r < minr:
                minr = r
                ind = at

        if minr < 2:
            if self.selected_atom >=0:
                self.ViewVoronoi = False
            if self.selected_atom != ind:
                #print("Point 1")
                if self.selected_atom >= 0:
                    self.MainModel.atoms[self.selected_atom].setSelected(False)
                self.selected_atom = ind
                self.MainModel.atoms[self.selected_atom].setSelected(True)
            else:
                #print("Point 2")
                if self.selected_atom >= 0:
                    self.MainModel.atoms[self.selected_atom].setSelected(False)
                self.selected_atom = -1
            self.add_atoms()
        self.CanSearch = False
        if oldSelected != self.selected_atom:
            self.openGLWidget.update()

    def get_point_in_3D(self, x, y):
        model = gl.glGetDoublev(gl.GL_MODELVIEW_MATRIX)
        proj = gl.glGetDoublev(gl.GL_PROJECTION_MATRIX)
        view = gl.glGetIntegerv(gl.GL_VIEWPORT)
        winY = float(view[3]) - float(y)
        z = gl.glReadPixels(x, int(winY), 1, 1, gl.GL_DEPTH_COMPONENT, gl.GL_FLOAT)
        point = glu.gluUnProject(x, y, z, model, proj, view)
        self.ProbeXYZ = False
        return point

    def initializeGL(self):
        qWidget.QOpenGLWidget.makeCurrent(self.openGLWidget)
        print("\033[4;30;102m INITIALIZE GL \033[0m")
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glEnable(gl.GL_DEPTH_TEST)
        self.object = gl.glGenLists(self.NLists)
        gl.glNewList(self.object, gl.GL_COMPILE)
        gl.glEndList()
        #gl.glEnable(gl.GL_CULL_FACE) # отсечение граней

       
    def delObj(self):
        gl.glDeleteLists(self.object, self.NLists)
        self.object = gl.glGenLists(self.NLists)
        print(self.object)

        
    def DelObject(self):
        i = 0
        for quadObj in self.QuadObjS:
            print(i)
            i+=1
            glu.gluDeleteQuadric(quadObj)
