#import turtle
from typing import List
#from PIL import Image, ImageDraw
import sys
from math import sin, cos, sqrt, atan2, radians, tan

print(sys.version)

def normalize(v):
    if v.x == 0 and v.y == 0 and v.z == 0:
        return v
    length = sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2)
    return Pos(v.x / length, v.y / length, v.z / length)

def cross(a, b):
    return Pos(a.y*b.z - a.z*b.y,
    a.z*b.x - a.x*b.z,
    a.x*b.y - a.y*b.x)

def dot(a, b):
    return a.x*b.x + a.y*b.y + a.z*b.z

def multiplyMatrixVector(matrix, vec4):
    out = []
    for i in range(4):
        out.append(matrix[i*4]*vec4[0] + matrix[(i*4)+1]*vec4[1] + matrix[(i*4)+2]*vec4[2] + matrix[(i*4)+3]*vec4[4])
    
    return out

class Position:

    def __init__(self, x, y ,z):
        self.x = x
        self.y = y
        self.z = z
    
    def __sub__(self, other):
        return Pos(self.x - other.x, self.y - other.y, self.z - other.z)
    
class Vec2:

    def __init__(self, x, y):
        self.x = x
        self.y = y

Pos = Position

class Vertex:

    def __init__(self, pos):
        self.pos = pos
    
    def __sub__(self, other):
        if type(other) == Pos:
            return Vertex(self.pos - other)
    
    def rotate(self, yaw, pitch, origin):
        # Translate to origin
        dx = self.pos.x - origin.x
        dy = self.pos.y - origin.y
        dz = self.pos.z - origin.z

        magnitude = sqrt(dx**2 + dy**2 + dz**2)
        yaw_rad = radians(yaw)
        pitch_rad = radians(pitch)

        # atan2 gives the correct current angle in each plane
        current_yaw = atan2(dz, dx)
        current_pitch = atan2(dy, sqrt(dx**2 + dz**2))

        final_yaw = current_yaw + yaw_rad
        final_pitch = current_pitch + pitch_rad

        # Translate back after rotating
        self.pos.x = origin.x + cos(final_pitch) * cos(final_yaw) * magnitude
        self.pos.y = origin.y + sin(final_pitch) * magnitude
        self.pos.z = origin.z + cos(final_pitch) * sin(final_yaw) * magnitude

class Face:

    def __init__(self, ipos):
        self.ipos = ipos

class Camera:

    def __init__(self, pos: Pos, target: Pos, rotation: Vec2, fov: int):
        self.pos = pos
        self.target = target
        self.up = Pos(0,1,0)
        self.fov = fov
        self.rotation = rotation
        self.__generate_view_matrix__()
    
    def __generate_view_matrix__(self):
        forward = normalize(self.target - self.pos)
        right = normalize(cross(forward, self.up))
        self.up = cross(right, forward)
        up = self.up
        self.view_matrix = [[right.x, right.y, right.z, -dot(right, self.pos)],
                            [up.x, up.y, up.z, -dot(up, self.pos)],
                            [-forward.x, -forward.y, -forward.z , dot(forward, self.pos)],
                            [0, 0, 0, 1]]
    
    def raster_to_view_space(self, vertex):
        return multiplyMatrixVector(self.view_matrix, [vertex.x, vertex.y, vertex.z, 1])
    
    def raster(self, vertices: List[Vertex]):
        # view_space_vertices = []
        # for vertex in vertices:
        #     final_vertex = self.raster_to_view_space(vertex)
        #     view_space_vertices.append(Vertex(Pos(final_vertex[0], final_vertex[1], final_vertex[2])))
        
        # return view_space_vertices
        width = 512
        height = 512
        img = Image.new("RGB", (width, height), color=(0, 0, 0))
        f = 1/tan(self.fov/2)
        for vertex in vertices:
            vertex = vertex - self.pos
            vertex.rotate(-self.rotation.x, -self.rotation.y, Pos(0, 0, 0))
            xclip = (f * vertex.pos.x)/vertex.pos.z
            xscreen = (xclip + 1) / 2 * width
            yclip = (f * vertex.pos.y)/vertex.pos.z
            yscreen = (yclip + 1) / 2 * height
            img.putpixel((round(xscreen), round(yscreen)), (0,255,0,0))
            

        self.rotation = Vec2(0, 0)
        img.save("output.png")



with open("./teapot.obj", "r") as file:
    obj = file.read()
    vertices = []
    faces = []
    for line in obj.split("\n"):
        if line == "":
            continue
        data = line.split(" ")
        if line[0] == "v":
            vertices.append(Vertex(Pos(float(data[1]), float(data[2]), float(data[3]))))
        elif line[0] == "f":
            faces.append(Face(Pos(int(data[1]), int(data[2]), int(data[3]))))
    
camera = Camera(Pos(0,0,0), Pos(0,0,0), Vec2(0,0), 90)

camera.raster(vertices)

