"""
Sovereign AGI — Phase 19 (L5 Autonomy)
services/repair/application/ast_patcher.py
Surgical AST Patching. Modifies only the required function/class to prevent full-file destruction.
"""

import ast
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class UnifiedASTPatcher:
    """
    Parses a python file into an AST, allows extraction of specific nodes,
    and supports targeted replacement to avoid hallucinating unrelated parts of a file.
    """
    def __init__(self, source_code: str):
        self.source_code = source_code
        try:
            self.tree = ast.parse(source_code)
        except SyntaxError as e:
            logger.error(f"Cannot parse source code: {e}")
            raise ValueError(f"Invalid Python source code: {e}")

    def extract_node(self, target_name: str) -> Optional[str]:
        """
        Extracts the source code of a specific class or function method.
        Target name can be 'MyClass' or 'MyClass.my_method' or just 'my_function'.
        """
        parts = target_name.split('.')
        node = self._find_node(self.tree, parts)
        if node:
            return ast.unparse(node)
        return None

    def replace_node(self, target_name: str, new_node_source: str) -> str:
        """
        Replaces the target class, function or method with new source code.
        Returns the entire updated source code.
        """
        try:
            new_ast_module = ast.parse(new_node_source)
        except SyntaxError as e:
            raise ValueError(f"Patch code contains SyntaxError: {e}")
        
        # Usually we expect 1 top-level node in the patch
        if not new_ast_module.body:
            raise ValueError("Patch source is empty.")
        new_node = new_ast_module.body[0]

        parts = target_name.split('.')
        parent, target = self._find_node_and_parent(self.tree, parts)
        
        if not target:
            raise ValueError(f"Node '{target_name}' not found in the source tree.")

        if parent:
            # Replace node in parent's body
            for idx, child in enumerate(parent.body):
                if child is target:
                    parent.body[idx] = new_node
                    break
        else:
            # Root level node replacement
            for idx, child in enumerate(self.tree.body):
                if child is target:
                    self.tree.body[idx] = new_node
                    break
                    
        return ast.unparse(self.tree)

    def _find_node(self, tree: ast.AST, parts: list[str]) -> Optional[ast.AST]:
        parent, target = self._find_node_and_parent(tree, parts)
        return target

    def _find_node_and_parent(self, tree: ast.AST, parts: list[str]) -> Tuple[Optional[ast.AST], Optional[ast.AST]]:
        if not parts:
            return None, None
            
        current_part = parts[0]
        
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name == current_part:
                    if len(parts) == 1:
                        # Found the target
                        return tree, node
                    else:
                        # Continue searching inside the class body
                        return self._find_node_and_parent(node, parts[1:])
        return None, None
