import json
import os
import logging
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger('inmoov_v13')

class VisualData:
    def __init__(self, data: dict):
        self.method = data.get("method", "sphere")
        self.color_key = data.get("color", "default")
        self.length_mm = float(data.get("length_mm", 0.0))
        self.radius = float(data.get("radius", 10.0))
        self.size = tuple(data.get("size", [10, 10, 10]))
        self.sections = data.get("sections", [])
        # NEW: Directional control. False = +Z (Up), True = -Z (Down)
        self.flip = data.get("flip", False) 

    def to_dict(self):
        return {
            "method": self.method,
            "color": self.color_key,
            "length_mm": self.length_mm,
            "radius": self.radius,
            "size": list(self.size),
            "sections": self.sections,
            "flip": self.flip
        }

class Joint:
    def __init__(self, data: dict):
        self.name = data.get("name", "fixed_joint")
        self.id = data.get("id", None)
        self.type = data.get("type", "fixed")
        self.axis = tuple(data.get("axis", [0, 0, 1]))
        self.limits = tuple(data.get("limits", [0, 180]))
        self.origin = tuple(data.get("origin", [0, 0, 0]))
        self.current_angle = 90.0

    def to_dict(self):
        return {
            "name": self.name,
            "id": self.id,
            "type": self.type,
            "axis": list(self.axis),
            "limits": list(self.limits),
            "origin": list(self.origin)
        }

class Link:
    def __init__(self, name: str, data: dict):
        self.name = name
        self.parent_name = data.get("parent", None)
        self.children_names = data.get("children", [])
        self.mass_g = float(data.get("mass_g", 0.0))
        self.center_of_mass = tuple(data.get("center_of_mass", [0, 0, 0]))
        
        joint_data = data.get("joint", None)
        self.joint = Joint(joint_data) if joint_data else None
        
        self.visual = VisualData(data.get("visual", {}))
        self.parent: Optional['Link'] = None
        self.children: List['Link'] = []

    def to_dict(self):
        d = {
            "mass_g": self.mass_g,
            "visual": self.visual.to_dict(),
            "children": [c.name for c in self.children]
        }
        if self.parent:
            d["parent"] = self.parent.name
        if self.joint:
            d["joint"] = self.joint.to_dict()
        return d

class RobotModel:
    def __init__(self):
        self.links: Dict[str, Link] = {}
        self.root: Optional[Link] = None
        self.name = "Unknown"
        self.metadata = {}

    def load_from_file(self, file_path: str) -> bool:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            self.metadata = data.get("metadata", {})
            self.name = self.metadata.get("name", "Unknown")
            
            self.links.clear()
            for lname, ldata in data.get("links", {}).items():
                self.links[lname] = Link(lname, ldata)

            # Rebuild Graph
            for link in self.links.values():
                if link.parent_name and link.parent_name in self.links:
                    link.parent = self.links[link.parent_name]
                for child_name in link.children_names:
                    if child_name in self.links:
                        link.children.append(self.links[child_name])
            
            root_name = data.get("root_link")
            if root_name in self.links:
                self.root = self.links[root_name]
                return True
            return False
        except Exception as e:
            logger.error(f"Load failed: {e}")
            return False

    def save_to_file(self, file_path: str) -> bool:
        try:
            data = {
                "metadata": self.metadata,
                "root_link": self.root.name if self.root else "",
                "links": {}
            }
            for name, link in self.links.items():
                data["links"][name] = link.to_dict()
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
            logger.info(f"Robot saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Save failed: {e}")
            return False

    def add_link(self, name, parent_name, type="revolute"):
        if name in self.links: return False
        
        new_data = {
            "parent": parent_name,
            "joint": {"name": f"{name}_joint", "type": type, "id": ""},
            "visual": {"method": "sphere", "radius": 20, "color": "default"}
        }
        
        new_link = Link(name, new_data)
        self.links[name] = new_link
        
        if parent_name in self.links:
            parent = self.links[parent_name]
            new_link.parent = parent
            parent.children.append(new_link)
            parent.children_names.append(name)
            
        return True