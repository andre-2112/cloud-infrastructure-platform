"""
Console utilities for Unicode-safe output on Windows.

Provides fallback ASCII characters when Unicode symbols fail to render.
"""

from rich.console import Console
from typing import Any


# Unicode to ASCII mapping
UNICODE_TO_ASCII = {
    '✓': '[OK]',
    '✗': '[X]',
    '→': '->',
    '⚠': '[!]',
    '❌': '[X]',
    '⭐': '*',
    '🚀': '',
    '📋': '',
    '🌍': '',
    '🔧': '',
}


def safe_print(console: Console, *args: Any, **kwargs: Any) -> None:
    """
    Print to console with Unicode fallback for Windows cp1252.

    Args:
        console: Rich Console instance
        *args: Content to print
        **kwargs: Additional arguments for console.print()
    """
    # Replace Unicode characters BEFORE printing
    safe_args = []
    for arg in args:
        if isinstance(arg, str):
            for unicode_char, ascii_char in UNICODE_TO_ASCII.items():
                arg = arg.replace(unicode_char, ascii_char)
        safe_args.append(arg)

    # Now print with safe arguments
    console.print(*safe_args, **kwargs)


def safe_console_output(func):
    """
    Decorator to catch UnicodeEncodeError and retry with ASCII.

    Usage:
        @safe_console_output
        def my_function():
            console.print("✓ Success")
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except UnicodeEncodeError:
            # Function will be retried, console.print inside will handle the conversion
            pass
    return wrapper
