import os
from typing import List


def build_file_tree(paths: List[str]):
    """Build a nested dictionary representing directories and files."""
    tree = {}
    for rel_path in paths:
        parts = rel_path.split(os.sep)
        node = tree
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node.setdefault('__files__', []).append(parts[-1])
    return tree


def _generate_html(node, base_path, action_url, field_name, action_value):
    html = '<ul class="file-tree">'
    for name in sorted(k for k in node.keys() if k != '__files__'):
        html += f'<li class="dir"><span>{name}</span>'
        html += _generate_html(node[name], os.path.join(base_path, name), action_url, field_name, action_value)
        html += '</li>'
    for fname in sorted(node.get('__files__', [])):
        rel = os.path.join(base_path, fname)
        html += (
            '<li class="file">'
            f'<form method="post" action="{action_url}" class="file-select-form">'
            f'<input type="hidden" name="action" value="{action_value}">' 
            f'<input type="hidden" name="{field_name}" value="{rel}">' 
            f'<button type="submit" class="file-link">{fname}</button>'
            '</form>'
            '</li>'
        )
    html += '</ul>'
    return html


def build_file_browser_html(paths: List[str], base_dir: str, action_url: str, field_name: str, action_value: str) -> str:
    """Generate nested HTML for a simple file browser."""
    rel_paths = [os.path.relpath(p, base_dir) for p in paths]
    tree = build_file_tree(rel_paths)
    return _generate_html(tree, '', action_url, field_name, action_value)
