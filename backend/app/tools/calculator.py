import ast


_OPERATORS = {
    ast.Add: lambda left, right: left + right,
    ast.Sub: lambda left, right: left - right,
    ast.Mult: lambda left, right: left * right,
    ast.Div: lambda left, right: left / right,
}


def _format_number(value: float) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _eval_node(node: ast.AST):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        if abs(value := float(node.value)) > 1_000_000_000_000:
            raise ValueError("number is too large")
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        inner = _eval_node(node.operand)
        return inner if isinstance(node.op, ast.UAdd) else -inner
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if isinstance(node.op, ast.Div) and right == 0:
            raise ValueError("division by zero")
        return _OPERATORS[type(node.op)](left, right)
    raise ValueError("unsupported expression")


def safe_calc(expression: str) -> str:
    """Evaluate arithmetic with AST nodes only. Names and calls are rejected."""
    try:
        parsed = ast.parse(expression.strip(), mode="eval")
        return _format_number(_eval_node(parsed))
    except Exception as exc:
        return f"Error: {exc}"
