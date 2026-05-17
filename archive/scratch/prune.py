import ast
import os
import glob
import re

def prune_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    
    # 1. Strip all @mcp.tool(name="geox_xxx") lines
    # This regex is highly constrained to a single line containing EXACTLY the decorator without matching across multiple lines.
    source = re.sub(r'^[ \t]*@mcp\.tool\(name="geox_[a-zA-Z0-9_]+"\)[ \t]*\r?\n', '', source, flags=re.MULTILINE)
    
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"Error parsing {filepath}: {e}")
        return
        
    lines_to_delete = set()
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            doc = ast.get_docstring(node)
            if doc and ("[DEPRECATED]" in doc or "Legacy alias" in doc):
                start_line = node.lineno
                if node.decorator_list:
                    start_line = min(d.lineno for d in node.decorator_list)
                
                for i in range(start_line, node.end_lineno + 1):
                    lines_to_delete.add(i)

    if not lines_to_delete:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(source)
        print(f"Pruned syntax decorators only in {filepath}")
        return

    lines = source.splitlines(True)
    new_lines = []
    
    for i, line in enumerate(lines, start=1):
        if i not in lines_to_delete:
            new_lines.append(line)
            
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("".join(new_lines))
    print(f"Pruned functions in {filepath}")
        
if __name__ == '__main__':
    for filepath in glob.glob('contracts/tools/*.py'):
        prune_file(filepath)
    print("Done")
