use std::fs::File;
use std::io::{Cursor, Read, Seek, SeekFrom};
use std::path::Path;
use image::{EncodableLayout, ImageBuffer, Rgb, RgbImage};
use imageproc::drawing::draw_polygon_mut;
use imageproc::point::Point;
use std::ops::Sub;
use std::ops::Add;
use std::iter::Sum;
use minimp4::Mp4Muxer;
use openh264::encoder::{Encoder, EncoderConfig};

struct Vec2 {
    x: f32,
    y: f32
}
impl Vec2 {
    fn new(x: f32, y: f32) -> Vec2 {
        Vec2 {x, y}
    }
}
#[derive(Copy, Clone)]
struct Vertex {
    x: f32,
    y: f32,
    z: f32
}
impl Vertex {
    fn new(x: f32, y: f32, z: f32) -> Self {
        Vertex { x, y, z }
    }

    fn rotate(&mut self, origin: Vertex, yaw: f32, pitch: f32) {
        let dvertex = Vertex::new(self.x - origin.x, self.y - origin.y, self.z - origin.z);

        let magnitude = (dvertex.x.powi(2) + dvertex.y.powi(2) + dvertex.z.powi(2)).sqrt();
        let yaw_rads = yaw.to_radians();
        let pitch_rads = pitch.to_radians();

        let current_yaw = dvertex.z.atan2(dvertex.x);
        let current_pitch = dvertex.y.atan2((dvertex.x.powi(2) + dvertex.z.powi(2)).sqrt());

        let final_yaw = yaw_rads + current_yaw;
        let final_pitch = pitch_rads + current_pitch;

        self.x = origin.x + final_pitch.cos() * final_yaw.cos() * magnitude;
        self.y = origin.y + final_pitch.sin() * magnitude;
        self.z = origin.z + final_pitch.cos() * final_yaw.sin() * magnitude;
    }
}
impl Sub for Vertex {
    type Output = Self;

    fn sub(self, other: Vertex) -> Self {
        Vertex { x: self.x - other.x, y: self.y - other.y, z: self.z - other.z }
    }
}
impl Sub<&mut Vertex> for Vertex {
    type Output = Self;

    fn sub(self, other: &mut Vertex) -> Self {
        Vertex { x: self.x - other.x, y: self.y - other.y, z: self.z - other.z }
    }
}
impl Sub<&Vertex> for Vertex {
    type Output = Vertex;
    fn sub(self, rhs: &Vertex) -> Vertex {
        Vertex {
            x: self.x - rhs.x,
            y: self.y - rhs.y,
            z: self.z - rhs.z,
        }
    }
}
impl Add for Vertex {
    type Output = Self;

    fn add(self, other: Vertex) -> Self {
        Vertex::new(self.x + other.x, self.y + other.y, self.z + other.z)
    }
}
impl Sum for Vertex {
    fn sum<I: Iterator<Item = Self>>(iter: I) -> Self {
        iter.fold(Vertex { x: 0.0, y: 0.0, z: 0.0 }, |a, b| a + b)
    }
}

struct Face {
    vertex1: i32,
    vertex2: i32,
    vertex3: i32,
}
impl Face {
    fn new(vertex1: i32, vertex2: i32, vertex3: i32) -> Self {
        Face { vertex1, vertex2, vertex3 }
    }
}

struct Camera {
    origin: Vertex,
    rotation: Vec2,
    resolution: Vec2,
    fov: f32
}
impl Camera {
    fn new(origin: Vertex, rotation: Vec2, resolution: Vec2, fov: f32) -> Self {
        Self {
            origin,
            rotation,
            resolution,
            fov
        }
    }

    fn rasterize(&mut self, vertices: &Vec<Vertex>, faces: &mut Vec<Face>) -> ImageBuffer<Rgb<u8>, Vec<u8>> {
        let mut img = RgbImage::new(self.resolution.x as u32, self.resolution.y as u32);
        let face_color = Rgb([0, 255, 0]);

        let mut screen_space_pos = Vec::new();

        let f = 1.0/((self.fov/2.0).to_radians().tan());
        let camera_space_vertices: Vec<Vertex> = vertices.iter().map(|vertex| { 
            let mut v = *vertex - self.origin;
            v.rotate(Vertex::new(0.0, 0.0, 0.0), -self.rotation.x, -self.rotation.y);
            if !(false) {
                let xclip = (f * v.x)/v.z;
                let xscreen = (xclip + 1.0) / 2.0 * self.resolution.x;
                let yclip = (f * v.y)/v.z;
                let yscreen = (1.0 - yclip) / 2.0 * self.resolution.y;
                screen_space_pos.push(Point{ x: xscreen.round() as i32, y: yscreen.round() as i32 });
            }
            v
        }).collect();
        
        faces.sort_by_key(|f| ((camera_space_vertices[(f.vertex1-1) as usize].z + camera_space_vertices[(f.vertex2-1) as usize].z + camera_space_vertices[(f.vertex3-1) as usize].z)/3.0).round() as i32);
        faces.reverse();

        for face in faces {
            //println!("x: {} {}, y: {} {}, z: {} {}", screen_space_pos[(face.vertex1-1) as usize].x, screen_space_pos[(face.vertex1-1) as usize].y, screen_space_pos[(face.vertex2-1) as usize].x, screen_space_pos[(face.vertex2-1) as usize].y, screen_space_pos[(face.vertex3-1) as usize].x, screen_space_pos[(face.vertex3-1) as usize].y);
            let vertices: &[Point<i32>] = &[
                screen_space_pos[(face.vertex1-1) as usize],
                screen_space_pos[(face.vertex2-1) as usize],
                screen_space_pos[(face.vertex3-1) as usize],
            ];
            draw_polygon_mut(&mut img, vertices, face_color);
        }
        self.rotation.x = 0.0;
        self.rotation.y = 0.0;
        img

    }
}

fn rotate_object(vertices: &mut Vec<Vertex>, yaw: f32, pitch: f32) {
    let vertices_len = vertices.len() as f32;
    let mut centre: Vertex = Vertex::new(0.0,0.0,0.0);
    for vertex in &mut *vertices {
        centre = centre + *vertex;
    }

    centre.x = centre.x / vertices_len;
    centre.y = centre.y / vertices_len;
    centre.z = centre.z / vertices_len;

    for vertex in &mut *vertices {
        vertex.rotate(centre, yaw, pitch);
    }
}

fn main() {
    let mut obj = String::new();
    File::open(Path::new(r"/workspaces/raster/teapot.obj")).unwrap().read_to_string(&mut obj).expect("TODO: panic message");
    let mut vertices = Vec::new();
    let mut faces = Vec::new();

    for line in obj.lines() {
        if line == "" {
            continue;
        }
        let data = line.split(" ").collect::<Vec<&str>>();
        if data.len() < 3 {
            continue;
        }

        if data[0] == "v" {
            vertices.push(Vertex::new(data[1].parse().unwrap(), data[2].parse().unwrap(), data[3].parse().unwrap()));
        } else if data[0] == "f" {
            faces.push(Face::new(data[1].parse().unwrap(), data[2].parse().unwrap(), data[3].parse().unwrap()));
        }
    }
    let config = EncoderConfig::new(1080, 1080);
    let mut encoder = Encoder::with_config(config).unwrap();

    let mut buf = Vec::new();

    let mut camera = Camera::new(Vertex::new(0.0, 1.0, -5.0), Vec2::new(0.0,0.0), Vec2::new(1080.0, 1080.0), 45.0);

    for _i in 0..360 {
        let frame = camera.rasterize(&vertices, &mut faces).as_bytes().to_vec();
        // Convert RGB into YUV.
        let mut yuv = openh264::formats::RBGYUVConverter::new(1080, 1080);
        yuv.convert(&frame[..]);

        // Encode YUV into H.264.
        let bitstream = encoder.encode(&yuv).unwrap();
        bitstream.write_vec(&mut buf);
        rotate_object(&mut vertices, 1.0, 0.0);
    }
    let mut video_buffer = Cursor::new(Vec::new());
    let mut mp4muxer = Mp4Muxer::new(&mut video_buffer);
    mp4muxer.init_video(1080, 1080, false, "3D");
    mp4muxer.write_video(&buf);
    mp4muxer.close();

    // Some shenanigans to get the raw bytes for the video.
    video_buffer.seek(SeekFrom::Start(0)).unwrap();

    //camera.rasterize(vertices, faces).save("/workspaces/raster/rust/output.png").unwrap();
}
