import numpy as np
import logging
from PyQt6.QtGui import QVector3D

logger = logging.getLogger('inmoov_v13')

class CollisionSphere:
    def __init__(self, position: QVector3D, radius: float, link_name: str):
        self.position = position # Relative to Link Origin
        self.radius = radius
        self.link_name = link_name
        self.abs_position = QVector3D(0,0,0) 

class CollisionEngine:
    def __init__(self, robot_model):
        self.model = robot_model
        self.colliders = {} 
        self.generate_colliders()

    def generate_colliders(self):
        margin = self.model.metadata.get("safety_margin_mm", 5.0)
        
        for link_name, link in self.model.links.items():
            spheres = []
            vis = link.visual
            # Direction Logic
            direction = -1.0 if vis.flip else 1.0
            
            if vis.method == "loft" or vis.method == "cylinder":
                length = vis.length_mm
                avg_radius = vis.radius
                if vis.sections:
                    s0 = vis.sections[0]
                    # Robust radius extraction
                    if "radius" in s0: avg_radius = s0["radius"]
                    elif "radius_x" in s0: avg_radius = (s0["radius_x"] + s0["radius_y"])/2
                
                step = max(20.0, avg_radius * 1.2) 
                num_spheres = int(length / step) + 1
                
                for i in range(num_spheres):
                    # APPLY FLIP HERE
                    z = (i * step) * direction
                    
                    # Clamp magnitude
                    if abs(z) > length: z = length * direction

                    r = avg_radius + margin
                    spheres.append(CollisionSphere(QVector3D(0, 0, z), r, link_name))
            
            elif vis.method == "sphere":
                r = vis.radius + margin
                spheres.append(CollisionSphere(QVector3D(0, 0, 0), r, link_name))
            
            elif vis.method == "box":
                w, h, d = vis.size
                r = (max(w, h, d) / 2) + margin
                spheres.append(CollisionSphere(QVector3D(0, 0, 0), r, link_name))
                
            self.colliders[link_name] = spheres
        
        logger.info(f"Generated {sum(len(v) for v in self.colliders.values())} collision spheres.")

    def update_collider_positions(self, kinematics_engine):
        nodes = kinematics_engine.scene_nodes
        for link_name, spheres in self.colliders.items():
            if link_name in nodes:
                transform = nodes[link_name].transform()
                for sphere in spheres:
                    sphere.abs_position = transform.map(sphere.position)

    def check_collisions(self):
        collisions = []
        links = list(self.colliders.keys())
        for i in range(len(links)):
            name_a = links[i]
            link_a_obj = self.model.links[name_a]
            parent_a = link_a_obj.parent_name
            for j in range(i + 1, len(links)):
                name_b = links[j]
                link_b_obj = self.model.links[name_b]
                if name_b == parent_a or link_b_obj.parent_name == name_a: continue
                if self._check_link_pair(self.colliders[name_a], self.colliders[name_b]):
                    collisions.append((name_a, name_b))
        return collisions

    def _check_link_pair(self, spheres_a, spheres_b):
        for sa in spheres_a:
            for sb in spheres_b:
                dist_sq = sa.abs_position.distanceToPoint(sb.abs_position)
                min_dist = sa.radius + sb.radius
                if dist_sq < min_dist: return True
        return False