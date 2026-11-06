import ast
import inspect
from typing import Any, Callable, Dict

ALLOWED_BUILTINS = {
    "abs": abs, "round": round, "min": min, "max": max, "sum": sum,
    "len": len, "str": str, "int": int, "float": float, "bool": bool,
    "range": range, "list": list, "dict": dict, "tuple": tuple, "set": set,
    "enumerate": enumerate, "zip": zip, "sorted": sorted,
}


class SecurityViolationError(Exception):
    pass


class ASTSecurityInspector(ast.NodeVisitor):
    FORBIDDEN_NODES = (
        ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal, ast.Delete,
        ast.With, ast.AsyncWith, ast.While, ast.ClassDef, ast.AsyncFunctionDef,
        ast.Await, ast.Yield, ast.YieldFrom, ast.Try,
    )
    FORBIDDEN_ATTRS = {"format", "format_map", "mro"}
    FORBIDDEN_CALLS = {"eval", "exec", "compile", "open", "input", "getattr", "setattr", "delattr", "globals", "locals", "vars", "dir", "type", "help", "__import__"}

    def generic_visit(self, node):
        if isinstance(node, self.FORBIDDEN_NODES):
            raise SecurityViolationError(f"AST node '{type(node).__name__}' is disallowed.")
        super().generic_visit(node)

    def visit_Attribute(self, node):
        if node.attr.startswith("_") or node.attr in self.FORBIDDEN_ATTRS:
            raise SecurityViolationError(f"Access to attribute '{node.attr}' is prohibited.")
        self.generic_visit(node)

    def visit_Name(self, node):
        if node.id.startswith("_") or node.id in self.FORBIDDEN_CALLS:
            raise SecurityViolationError(f"Use of identifier '{node.id}' is prohibited.")
        self.generic_visit(node)


def build_sandboxed_callable(func_name: str, code_body: str) -> Callable[..., Any]:
    tree = ast.parse(code_body)
    ASTSecurityInspector().visit(tree)

    compiled = compile(tree, filename="<dynamic_tool>", mode="exec")
    scope: Dict[str, Any] = {"__builtins__": dict(ALLOWED_BUILTINS)}
    exec(compiled, scope)

    fn = scope.get(func_name)
    if fn is None or not callable(fn):
        raise ValueError(f"Function '{func_name}' was not defined in the submitted code.")
    return fn


def invoke_sandboxed_tool(fn: Callable[..., Any], default_args: tuple = (4, 8)) -> Any:
    sig = inspect.signature(fn)
    params = [
        p for p in sig.parameters.values()
        if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        and p.default is inspect.Parameter.empty
    ]
    call_args = [default_args[i] if i < len(default_args) else 2 for i in range(len(params))]
    return fn(*call_args)
