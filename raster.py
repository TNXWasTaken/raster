import turtle

class Vertex:

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class Face:

    def __init__(self, ix, iy, iz):
        self.ix = ix
        self.iy = iy
        self.iz = iz

with open("./teapot.obj", "r") as file:
    obj = file.read()
    vertices = []
    faces = []
    for line in obj.split("\n"):
        if line == "":
            continue
        data = line.split(" ")
        if line[0] == "v":
            vertices.append(Vertex(float(data[1]), float(data[2]), float(data[3])))
        elif line[0] == "f":
            faces.append(Face(int(data[1]), int(data[2]), int(data[3])))

    print(vertices)