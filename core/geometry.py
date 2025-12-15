import numpy as np
import math
import logging

try:
    import pyqtgraph.opengl as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False

logger = logging.getLogger('inmoov_v13')

class GeometryGenerator:
    @staticmethod
    def generate_mesh_item(visual_data, color_tuple):
        if not HAS_GL: return None
        md = None
        
        if visual_data.method == "loft":
            md = GeometryGenerator.generate_loft(visual_data)
        elif visual_data.method == "sphere":
            md = GeometryGenerator.generate_sphere(visual_data.radius)
        elif visual_data.method == "cylinder":
            md = GeometryGenerator.generate_cylinder_as_loft(visual_data)
        elif visual_data.method == "box":
            s = visual_data.size if hasattr(visual_data, 'size') else (10,10,10)
            md = GeometryGenerator.generate_box(s[0], s[1], s[2])
        
        if md:
            return gl.GLMeshItem(meshdata=md, smooth=True, color=color_tuple, shader='shaded', glOptions='opaque')
        return None

    @staticmethod
    def generate_loft(visual_data, segments=32):
        length = visual_data.length_mm
        sections = visual_data.sections
        direction = -1.0 if visual_data.flip else 1.0 # UP = 1, DOWN = -1
        
        if not sections: return None

        rings = []
        for section in sections:
            # Apply direction multiplier
            z_pos = section.get("percent", 0.0) * length * direction
            shape_type = section.get("shape", "circle")
            
            ring_verts = []
            for i in range(segments):
                theta = 2 * math.pi * i / segments
                x, y = 0.0, 0.0
                
                if shape_type == "circle":
                    r = section.get("radius", 10)
                    x = r * math.cos(theta); y = r * math.sin(theta)
                elif shape_type == "oval":
                    rx = section.get("radius_x", 10); ry = section.get("radius_y", 10)
                    x = rx * math.cos(theta); y = ry * math.sin(theta)
                elif shape_type == "box":
                    w = section.get("width", 10) / 2; d = section.get("depth", 10) / 2
                    cs = math.cos(theta); sn = math.sin(theta)
                    x = w * np.sign(cs) * (abs(cs) ** 0.3)
                    y = d * np.sign(sn) * (abs(sn) ** 0.3)

                ring_verts.append([x, y, z_pos]) 
            rings.append(np.array(ring_verts))

        return GeometryGenerator._stitch_rings(rings, segments)

    @staticmethod
    def generate_cylinder_as_loft(visual_data, segments=32):
        r = visual_data.radius
        l = visual_data.length_mm
        direction = -1.0 if visual_data.flip else 1.0
        
        ring_bottom = []
        ring_top = []
        for i in range(segments):
            theta = 2 * math.pi * i / segments
            x = r * math.cos(theta)
            y = r * math.sin(theta)
            ring_bottom.append([x, y, 0])
            ring_top.append([x, y, l * direction])
            
        rings = [np.array(ring_bottom), np.array(ring_top)]
        return GeometryGenerator._stitch_rings(rings, segments)

    @staticmethod
    def _stitch_rings(rings, segments):
        all_verts = np.concatenate(rings)
        faces = []
        num_rings = len(rings)
        for r in range(num_rings - 1):
            base = r * segments
            next = (r + 1) * segments
            for i in range(segments):
                i_n = (i + 1) % segments
                v1 = base + i; v2 = base + i_n; v3 = next + i; v4 = next + i_n
                faces.append([v1, v2, v3]); faces.append([v2, v4, v3])
        return gl.MeshData(vertexes=all_verts, faces=np.array(faces))

    @staticmethod
    def generate_sphere(radius, rows=16, cols=32):
        return gl.MeshData.sphere(rows=rows, cols=cols, radius=radius)

    @staticmethod
    def generate_box(w, h, d):
        verts = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
        ], dtype=float)
        verts -= 0.5
        verts[:, 0] *= w; verts[:, 1] *= h; verts[:, 2] *= d
        faces = np.array([
            [0, 1, 2], [0, 2, 3], [4, 5, 6], [4, 6, 7],
            [0, 4, 7], [0, 7, 3], [1, 5, 6], [1, 6, 2],
            [0, 1, 5], [0, 5, 4], [3, 2, 6], [3, 6, 7]
        ], dtype=int)
        return gl.MeshData(vertexes=verts, faces=faces)