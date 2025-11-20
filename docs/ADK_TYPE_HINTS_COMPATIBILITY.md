# ADK Type Hints Compatibility

## Issue

ADK's automatic function calling parser does not support Python 3.10+ union type syntax (`int | None`). It only recognizes the `typing.Union` and `typing.Optional` syntax.

## Root Cause

The ADK function parameter parser (`google.adk.tools._function_parameter_parse_util.py`) explicitly checks for `Union` types from the `typing` module:

```python
if origin is Union:  # Line 247
    # Handle Optional types...
```

However, the modern Python syntax `int | None` creates a `types.UnionType` object (introduced in Python 3.10), which is NOT the same as `typing.Union`. The parser doesn't recognize this type and raises:

```
ValueError: Failed to parse the parameter head: int | None = None of function read_file
```

## Solution

**Always use `typing.Optional[T]` instead of `T | None` in function signatures that will be used as ADK tools.**

### Before (Broken)
```python
def read_file(
    path: str,
    working_dir: str,
    head: int | None = None,  # ❌ Not recognized by ADK
    tail: int | None = None,  # ❌ Not recognized by ADK
) -> str:
    ...
```

### After (Fixed)
```python
from typing import Optional

def read_file(
    path: str,
    working_dir: str,
    head: Optional[int] = None,  # ✅ Recognized by ADK
    tail: Optional[int] = None,  # ✅ Recognized by ADK
) -> str:
    ...
```

## ADK-Compatible Type Hints

### ✅ Supported
- `Optional[int]`, `Optional[str]`, `Optional[list[str]]`
- `Union[str, int]` (from typing module)
- `list[str]`, `dict[str, int]`
- `Literal["option1", "option2"]`
- Basic types: `str`, `int`, `float`, `bool`

### ❌ Not Supported
- `int | None` (Python 3.10+ union syntax)
- `str | int` (Python 3.10+ union syntax)
- Complex nested unions with new syntax

## Default Values

Default values ARE supported by ADK (contrary to some documentation):
- `Optional[int] = None` ✅ Works
- `str = "default"` ✅ Works
- `list[str] = []` ✅ Works (with proper handling)

The parser handles defaults on lines 201, 214, 224, 244 of `_function_parameter_parse_util.py`.

## Best Practices

1. **Use `typing.Optional[T]`** for optional parameters instead of `T | None`
2. **Import from typing**: `from typing import Optional, Union, Literal`
3. **Use lowercase generic types**: `list[str]`, `dict[str, int]` (Python 3.9+)
4. **Test agent creation** after modifying tool signatures to catch parsing errors early

## References

- ADK Documentation: Function calling works best with simpler type signatures
- Python typing module: https://docs.python.org/3/library/typing.html
- PEP 604 (Union syntax): https://peps.python.org/pep-0604/ (Not yet supported by ADK)




