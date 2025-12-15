import numpy as np
from PyQt6.QtGui import QMatrix4x4, QVector3D, QVector4D
import logging
import math
from .geometry import GeometryGenerator
from .collision import CollisionEngine
from .config_manager import config_manager 

try:
    import pyqtgraph.opengl as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False

logger = logging.getLogger('inmoov_v13')

class KinematicsEngine:
    def __init__(self, robot_model):
        self.model = robot_model
        
        self.scene_nodes = {}
        self.ghost_nodes = {}
        self.collider_nodes = {}
        self.current_state = {} 
        self.target_state = {}
        
        self.collision_engine = CollisionEngine(self.model)

        self._load_colors()
        config_manager.visual_changed.connect(self.refresh_theme)

    def _load_colors(self):
        theme_key = config_manager.get("skeleton_color") or "Bone"
        opacity = config_manager.get("visual_ghost_opacity") or 0.3
        
        palettes = {
            "Bone":   (0.8, 0.8, 0.7, 1.0),
            "Carbon": (0.2, 0.2, 0.2, 1.0),
            "Gold":   (0.8, 0.6, 0.2, 1.0),
            "Steel":  (0.6, 0.6, 0.7, 1.0)
        }
        main_c = palettes.get(theme_key, palettes["Bone"])
        
        self.colors = {
            "bone": main_c,
            "muscle": (0.9, 0.4, 0.4, 1.0),
            "skin": (0.9, 0.8, 0.7, 1.0),
            "motor": (0.1, 0.1, 0.1, 1.0),
            "default": (0.5, 0.5, 0.5, 1.0),
            "ghost": (0.0, 1.0, 1.0, opacity),
            "collider": (1.0, 0.0, 0.0, 0.2)
        }

    def refresh_theme(self):
        """Safely applies colors to 3D items."""
        self._load_colors()
        
        def safe_color(item, color):
            # Only apply color if the item supports it
            if hasattr(item, 'setColor'):
                try: item.setColor(color)
                except: pass

        for name, item in self.scene_nodes.items():
            if hasattr(item, 'link_data'):
                key = item.link_data.visual.color_key
                c = self.colors.get(key, self.colors["default"])
                safe_color(item, c)
                
        for item in self.ghost_nodes.values():
            safe_color(item, self.colors["ghost"])

    def initialize_view(self, view_widget):
        if not self.model.root: return
        self.scene_nodes.clear(); self.ghost_nodes.clear(); self.collider_nodes.clear()
        
        self._build_tree(self.model.root, view_widget, self.scene_nodes, False)
        self._build_tree(self.model.root, view_widget, self.ghost_nodes, True)
        self._build_colliders(view_widget)
        self.update_fk()

    def _build_tree(self, link, view, node_dict, is_ghost):
        color = self.colors["ghost"] if is_ghost else self.colors.get(link.visual.color_key, self.colors["default"])
        mesh_item = GeometryGenerator.generate_mesh_item(link.visual, color)
        
        # Invisible Transform Node for empty links
        if mesh_item is None and HAS_GL:
            mesh_item = gl.GLAxisItem()
            mesh_item.setSize(0,0,0) 
            mesh_item.setVisible(False)

        if mesh_item:
            view.addItem(mesh_item)
            node_dict[link.name] = mesh_item
            
            if is_ghost:
                mesh_item.setVisible(False)
            else:
                if isinstance(mesh_item, gl.GLMeshItem):
                    mesh_item.setVisible(True)
                mesh_item.link_data = link

        for child in link.children:
            self._build_tree(child, view, node_dict, is_ghost)

    def _build_colliders(self, view):
        from .robot_loader import VisualData
        for link_name, spheres in self.collision_engine.colliders.items():
            for i, sphere in enumerate(spheres):
                vdata = VisualData({"method": "sphere", "radius": sphere.radius})
                mesh = GeometryGenerator.generate_mesh_item(vdata, self.colors["collider"])
                if mesh:
                    view.addItem(mesh)
                    mesh.setVisible(False)
                    self.collider_nodes[f"{link_name}_{i}"] = mesh

    def set_visibility(self, show_ghost, show_colliders):
        for n in self.ghost_nodes.values(): 
            if hasattr(n, 'setVisible'): n.setVisible(show_ghost)
        for n in self.collider_nodes.values(): 
            n.setVisible(show_colliders)

    def update_state_from_sensors(self, sensor_data):
        self.current_state.update({str(k): float(v) for k, v in sensor_data.items()})
        self.update_fk()

    def set_target_pose(self, pose_data):
        clean = {str(k): float(v) for k, v in pose_data.items()}
        self.target_state.update(clean)
        self.current_state.update(clean) 
        self.update_fk()

    def rebuild_scene(self, view_widget):
        for n in list(self.scene_nodes.values()) + list(self.ghost_nodes.values()) + list(self.collider_nodes.values()):
            try: view_widget.removeItem(n)
            except: pass
        self.initialize_view(view_widget)

    def update_fk(self):
        if not self.model.root: return
        self._traverse_fk(self.model.root, QMatrix4x4(), self.scene_nodes, self.current_state)
        if self.ghost_nodes:
            self._traverse_fk(self.model.root, QMatrix4x4(), self.ghost_nodes, self.target_state)
        self._update_collider_transforms()

    def _traverse_fk(self, link, parent_matrix, node_map, state_dict):
        global_mat = QMatrix4x4(parent_matrix)
        if link.joint:
            ox, oy, oz = link.joint.origin
            global_mat.translate(ox, oy, oz)
            
            angle = 90.0
            jid = str(link.joint.id)
            if link.joint.id:
                if jid in state_dict:
                    angle = state_dict[jid]
            
            rot = angle - 90.0
            ax, ay, az = link.joint.axis
            global_mat.rotate(rot, ax, ay, az)

        if node_map is self.scene_nodes: link.abs_transform = global_mat
        if link.name in node_map: node_map[link.name].setTransform(global_mat)
        
        for child in link.children:
            self._traverse_fk(child, global_mat, node_map, state_dict)

    def _update_collider_transforms(self):
        for link_name, spheres in self.collision_engine.colliders.items():
            if link_name not in self.model.links: continue
            base = self.model.links[link_name].abs_transform
            for i, s in enumerate(spheres):
                k = f"{link_name}_{i}"
                if k in self.collider_nodes:
                    m = QMatrix4x4(base)
                    m.translate(s.position)
                    self.collider_nodes[k].setTransform(m)
                    
    def solve_ik(self, target_pos_list, end_link_name, iterations=30, tolerance=10.0):
        if end_link_name not in self.model.links: return

        # Ensure floats
        tx, ty, tz = float(target_pos_list[0]), float(target_pos_list[1]), float(target_pos_list[2])
        target_vec = QVector3D(tx, ty, tz)
        end_link = self.model.links[end_link_name]

        # 1. Build Chain
        chain = []
        curr = end_link
        while curr.parent:
            if curr.joint and curr.joint.id and curr.joint.type == "revolute":
                chain.append(curr)
            curr = curr.parent

        # 2. Iterate
        for _ in range(iterations):
            self._traverse_fk(self.model.root, QMatrix4x4(), self.ghost_nodes, self.target_state)
            
            # Check Error
            if end_link_name not in self.ghost_nodes: break
            eff_node = self.ghost_nodes[end_link_name]
            eff_pos = eff_node.transform().map(QVector3D(0.0, 0.0, 0.0))
            
            if eff_pos.distanceToPoint(target_vec) < tolerance:
                break 

            # 3. CCD Loop
            for link in chain:
                if link.name not in self.ghost_nodes: continue
                
                link_node = self.ghost_nodes[link.name]
                link_transform = link_node.transform()
                link_pos = link_transform.map(QVector3D(0.0, 0.0, 0.0))
                
                to_effector = (eff_pos - link_pos).normalized()
                to_target = (target_vec - link_pos).normalized()
                
                dot = QVector3D.dotProduct(to_effector, to_target)
                if dot > 0.9999: continue

                angle_diff = math.degrees(math.acos(max(-1.0, min(1.0, dot))))
                cross = QVector3D.crossProduct(to_effector, to_target)
                
                rot_matrix = QMatrix4x4(link_transform)
                rot_matrix.setColumn(3, QVector4D(0,0,0,1)) 
                
                local_axis = QVector3D(float(link.joint.axis[0]), float(link.joint.axis[1]), float(link.joint.axis[2]))
                world_axis = rot_matrix.map(local_axis).normalized()
                
                direction = 1 if QVector3D.dotProduct(cross, world_axis) > 0 else -1
                
                delta = angle_diff * direction * 0.2 
                
                jid = str(link.joint.id)
                curr_angle = self.target_state.get(jid, 90.0)
                new_angle = curr_angle + delta
                
                if link.joint.limits:
                    new_angle = max(link.joint.limits[0], min(link.joint.limits[1], new_angle))
                
                self.target_state[jid] = new_angle
                
                self._traverse_fk(self.model.root, QMatrix4x4(), self.ghost_nodes, self.target_state)
                eff_pos = eff_node.transform().map(QVector3D(0.0, 0.0, 0.0))

        self.current_state.update(self.target_state)
        self.update_fk()
        logger.info("IK Solution Applied")