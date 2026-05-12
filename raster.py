#import turtle
from typing import List
from PIL import Image, ImageDraw
import imageio
import numpy as np
from math import sin, cos, sqrt, atan2, radians, tan

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

    def __init__(self, pos: Pos, rotation: Vec2, fov: int, resolution: (int, int)):
        self.pos = pos
        self.width, self.height = resolution
        self.up = Pos(0,1,0)
        self.fov = fov
        self.rotation = rotation
    

    def raster(self, vertices: List[Vertex], faces: List[Face]):
        # view_space_vertices = []
        # for vertex in vertices:
        #     final_vertex = self.raster_to_view_space(vertex)
        #     view_space_vertices.append(Vertex(Pos(final_vertex[0], final_vertex[1], final_vertex[2])))
        
        # return view_space_vertices
        img = Image.new("RGB", (self.width, self.height), color=(0, 0, 0))
        screen_space_vertices = []
        f = 1/tan(radians(self.fov / 2))
        for vertex in vertices:
            vertex = vertex - self.pos
            vertex.rotate(-self.rotation.x, -self.rotation.y, Pos(0, 0, 0))
            if vertex.pos.z < 0.001:
                continue
            xclip = (f * vertex.pos.x)/vertex.pos.z
            xscreen = (xclip + 1) / 2 * self.width
            yclip = (f * vertex.pos.y)/vertex.pos.z
            yscreen = (1 - yclip) / 2 * self.height
            if 0 <= round(xscreen) < self.width and 0 <= round(yscreen) < self.height:
                img.putpixel((round(xscreen), round(yscreen)), (0, 255, 0))
            screen_space_vertices.append(Vec2(round(xscreen), round(yscreen)))
            
        print(f"x: {screen_space_vertices[0].x}, y: {screen_space_vertices[0].y}")
        img_draw = ImageDraw.Draw(img)

        faces.sort(key=lambda x: (vertices[x.ipos.x - 1].pos.z + vertices[x.ipos.y - 1].pos.z + vertices[x.ipos.z - 1].pos.z)/3, reverse=True)

        for face in faces:
            #print([(screen_space_vertices[face.ipos.x - 1].x, screen_space_vertices[face.ipos.x - 1].y), (screen_space_vertices[face.ipos.y - 1].x, screen_space_vertices[face.ipos.y - 1].y), (screen_space_vertices[face.ipos.z - 1].x, screen_space_vertices[face.ipos.z - 1].y)])
            img_draw.polygon([(screen_space_vertices[face.ipos.x - 1].x, screen_space_vertices[face.ipos.x - 1].y), (screen_space_vertices[face.ipos.y - 1].x, screen_space_vertices[face.ipos.y - 1].y), (screen_space_vertices[face.ipos.z - 1].x, screen_space_vertices[face.ipos.z - 1].y)], fill=("white"), outline='black')

        self.rotation = Vec2(0, 0)
        return img



with open("./teapot.obj", "r") as file:
    obj = file.read()
    vertices = []
    faces = []
    for line in obj.split("\n"):
        if line == "":
            continue
        data = line.split(" ")
        if data[0] == "v":
            if len(data) < 3:
                continue
            vertices.append(Vertex(Pos(float(data[1]), float(data[2]), float(data[3]))))
        elif data[0] == "f":
            if len(data) < 3:
                continue
            if "/" in line:
                    faces.append(Face(Pos(int(data[1].split("/")[0]), int(data[2].split("/")[0]), int(data[3].split("/")[0]))))
            else:
                faces.append(Face(Pos(int(data[1]), int(data[2]), int(data[3]))))
    
def rotate_obj(vertices: List[Vertex], yaw, pitch):
    centere = Pos(0,0,0)
    vertices_len = len(vertices)

    for vertex in vertices:
        centere.x += vertex.pos.x
        centere.y += vertex.pos.y
        centere.z += vertex.pos.z
    
    centere.x = centere.x / vertices_len
    centere.y = centere.y / vertices_len
    centere.z = centere.z / vertices_len

    for vertex in vertices:
        vertex.rotate(yaw, pitch, centere)

camera = Camera(Pos(0,1,-5), Vec2(0,0), 45, (1080, 1080))

writer = imageio.get_writer("./output.mp4", format="mp4", mode="I", fps=60)

camera.raster(vertices, faces).save("output.png")

# for i in range(360):
#     rotate_obj(vertices, 1, 0)
#     writer.append_data(np.asarray(camera.raster(vertices, faces)))

writer.close()