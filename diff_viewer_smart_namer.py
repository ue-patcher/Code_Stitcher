import sys
import re
import argparse
import libcst as cst

BLAND_NAMES = {
    "process", "run", "update", "execute", "handle", "do_stuff",
    "start", "stop", "get", "set", "load", "save", "parse", "check", "do_it", "draw"
}

def camel_to_snake(name: str) -> str:
    name = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name).lower()

def extract_node_name(node) -> str:
    if isinstance(node, cst.Name):
        return node.value
    elif isinstance(node, cst.Attribute):
        base = extract_node_name(node.value)
        if base:
            return f"{base}.{node.attr.value}"
    return None

class GlobalClassCollector(cst.CSTVisitor):
    """Pre-pass 1: Collects ALL classes and their base classes across ALL files."""
    def __init__(self):
        self.class_bases = {}

    def visit_ClassDef(self, node: cst.ClassDef):
        bases = []
        for base in node.bases:
            base_str = extract_node_name(base.value)
            if base_str:
                bases.append(base_str)
        self.class_bases[node.name.value] = bases

class ContextAnalyzer(cst.CSTVisitor):
    """Pre-pass 2: Identifies bland methods utilizing the Global Sprite Knowledge."""
    def __init__(self, global_sprite_classes, global_rename_map):
        self.current_class = None
        self.global_sprite_classes = global_sprite_classes
        self.global_rename_map = global_rename_map

    def visit_ClassDef(self, node: cst.ClassDef):
        self.current_class = node.name.value
        if self.current_class not in self.global_rename_map:
            self.global_rename_map[self.current_class] = {}

    def leave_ClassDef(self, node: cst.ClassDef):
        self.current_class = None

    def visit_FunctionDef(self, node: cst.FunctionDef):
        if not self.current_class: return

        old_name = node.name.value

        
        is_sprite = self.current_class in self.global_sprite_classes
        if is_sprite and old_name in {"update", "draw", "kill"}:
            return

        if old_name.lower() in BLAND_NAMES or old_name.startswith("do_"):
            new_name = self._generate_smart_name(old_name, node)
            if new_name != old_name:
                self.global_rename_map[self.current_class][old_name] = new_name

    def _generate_smart_name(self, old_name: str, node: cst.FunctionDef) -> str:
        params = node.params.params
        if len(params) > 1:
            first_arg = params[1].name.value
            if first_arg not in ("args", "kwargs", "data", "val", "x", "info", "event", "surf"):
                return f"{old_name}_{first_arg}"

        clean_class = re.sub(r'(Manager|Handler|Processor|Service|Factory|Layer)$', '', self.current_class)
        snake_class = camel_to_snake(clean_class)
        if snake_class and snake_class != old_name:
            return f"{old_name}_{snake_class}"

        return f"{old_name}_action"

class TypeTracker(cst.CSTVisitor):
    """File-pass 1: Traces variables using global class knowledge."""
    def __init__(self, known_classes):
        self.known_classes = known_classes
        self.var_types = {}

    def _infer_type(self, node):
        if isinstance(node, cst.Call) and isinstance(node.func, cst.Name):
            if node.func.value in self.known_classes:
                return node.func.value
        elif isinstance(node, (cst.List, cst.Tuple)):
            for el in node.elements:
                t = self._infer_type(el.value)
                if t: return t
        return None

    def visit_Assign(self, node: cst.Assign):
        t = self._infer_type(node.value)
        if t:
            for target in node.targets:
                name = extract_node_name(target.target)
                if name: self.var_types[name] = t

    def visit_AnnAssign(self, node: cst.AnnAssign):
        name = extract_node_name(node.target)
        if not name: return
        if isinstance(node.annotation.annotation, cst.Name) and node.annotation.annotation.value in self.known_classes:
            self.var_types[name] = node.annotation.annotation.value

    def visit_Call(self, node: cst.Call):
        if isinstance(node.func, cst.Attribute) and node.func.attr.value == "append" and node.args:
            t = self._infer_type(node.args[0].value)
            if t:
                list_name = extract_node_name(node.func.value)
                if list_name: self.var_types[list_name] = t

    def visit_For(self, node: cst.For):
        iter_name = extract_node_name(node.iter)
        target_name = extract_node_name(node.target)
        if iter_name and target_name and iter_name in self.var_types:
            self.var_types[target_name] = self.var_types[iter_name]

class IntelligentRenamer(cst.CSTTransformer):
    """File-pass 2: Transforms code based on global rename map and local types."""
    def __init__(self, global_rename_map: dict, var_types: dict):
        self.global_rename_map = global_rename_map
        self.var_types = var_types
        self.current_class = None

    def visit_ClassDef(self, node: cst.ClassDef):
        self.current_class = node.name.value
        return True

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef):
        self.current_class = None
        return updated_node

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef):
        if self.current_class and original_node.name.value in self.global_rename_map.get(self.current_class, {}):
            new_name = self.global_rename_map[self.current_class][original_node.name.value]
            return updated_node.with_changes(name=cst.Name(new_name))
        return updated_node

    def leave_Attribute(self, original_node: cst.Attribute, updated_node: cst.Attribute):
        caller_str = extract_node_name(original_node.value)
        old_attr = original_node.attr.value

        
        if caller_str == "self" and self.current_class:
            if old_attr in self.global_rename_map.get(self.current_class, {}):
                new_attr = self.global_rename_map[self.current_class][old_attr]
                return updated_node.with_changes(attr=cst.Name(new_attr))

        
        elif caller_str in self.var_types:
            inferred_class = self.var_types[caller_str]
            if old_attr in self.global_rename_map.get(inferred_class, {}):
                new_attr = self.global_rename_map[inferred_class][old_attr]
                return updated_node.with_changes(attr=cst.Name(new_attr))

        return updated_node

def resolve_global_sprites(class_bases) -> set:
    """Recursively resolves which classes inherit from Sprite/Group across the whole monolith."""
    sprite_classes = set()

    def check_is_sprite(cls_name, visited):
        if cls_name in sprite_classes:
            return True
        if cls_name in visited:
            return False 
        visited.add(cls_name)

        bases = class_bases.get(cls_name, [])
        for b in bases:
            if "Sprite" in b or "Group" in b:
                return True
            
            clean_b = b.split(".")[-1]
            if check_is_sprite(clean_b, visited):
                return True
        return False

    for cls in class_bases:
        if check_is_sprite(cls, set()):
            sprite_classes.add(cls)

    return sprite_classes

def process_monolith(filepaths: list):
    trees = {}

    
    print(f"Parsing {len(filepaths)} file(s) into the monolith...")
    for path in filepaths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                trees[path] = cst.parse_module(f.read())
        except Exception as e:
            print(f"Skipping {path} (Error reading/parsing: {e})")

    
    collector = GlobalClassCollector()
    for tree in trees.values():
        tree.visit(collector)

    global_sprite_classes = resolve_global_sprites(collector.class_bases)
    if global_sprite_classes:
        print(f"[*] Found {len(global_sprite_classes)} PyGame Sprite/Group classes globally. Protecting lifecycle hooks.")

    
    global_rename_map = {}
    analyzer = ContextAnalyzer(global_sprite_classes, global_rename_map)
    for tree in trees.values():
        tree.visit(analyzer)

    
    global_rename_map = {k: v for k, v in global_rename_map.items() if v}
    if not global_rename_map:
        print("No bland functions detected across the monolith. Everything is perfect.")
        return

    known_classes = set(global_rename_map.keys())

    
    print("\n--- Transforming Monolith ---")
    for path, tree in trees.items():
        
        tracker = TypeTracker(known_classes)
        tree.visit(tracker)

        
        renamer = IntelligentRenamer(global_rename_map, tracker.var_types)
        modified_tree = tree.visit(renamer)

        
        if modified_tree.deep_equals(tree):
            continue

        with open(path, "w", encoding="utf-8") as f:
            f.write(modified_tree.code)

        print(f"[+] Refactored: {path}")
        for cls, changes in global_rename_map.items():
            for old, new in changes.items():
                
                if cls in [c.name.value for c in tree.children if isinstance(c, cst.ClassDef)] or any(v == cls for v in tracker.var_types.values()):
                    print(f"    - {cls}.{old}() -> {cls}.{new}()")

    print("\nMonolith processing complete!")

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Monolithic Intelligent Method Renamer")
    parser.add_argument("files", nargs='+', help="One or more .py files to process together")
    args = parser.parse_args()

    process_monolith(args.files)
