from math import sin, cos, sqrt, atan2, radians

class Vec3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
    
    def __sub__(self, other):
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def rotate(self, yaw, pitch, origin):
        # Translate to origin
        dx = self.x - origin.x
        dy = self.y - origin.y
        dz = self.z - origin.z

        magnitude = sqrt(dx**2 + dy**2 + dz**2)
        yaw_rad = radians(yaw)
        pitch_rad = radians(pitch)

        # atan2 gives the correct current angle in each plane
        current_yaw = atan2(dz, dx)
        current_pitch = atan2(dy, sqrt(dx**2 + dz**2))

        final_yaw = current_yaw + yaw_rad
        final_pitch = current_pitch + pitch_rad

        # Translate back after rotating
        self.x = origin.x + cos(final_pitch) * cos(final_yaw) * magnitude
        self.y = origin.y + sin(final_pitch) * magnitude
        self.z = origin.z + cos(final_pitch) * sin(final_yaw) * magnitude

pos = Vec3(2, 2, 2)
pos.rotate(45, 0, Vec3(0, 0, 0))
print(pos.x, pos.y, pos.z)