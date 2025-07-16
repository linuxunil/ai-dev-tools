"""
Simple Python functions for basic pattern testing
"""


def add_numbers(a, b):
    """Add two numbers together"""
    return a + b


def subtract_numbers(a, b):
    """Subtract second number from first"""
    return a - b


def multiply_numbers(a, b):
    """Multiply two numbers"""
    return a * b


def divide_numbers(a, b):
    """Divide first number by second"""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def calculate_average(numbers):
    """Calculate average of a list of numbers"""
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)


def find_maximum(numbers):
    """Find maximum value in a list"""
    if not numbers:
        return None
    return max(numbers)


def find_minimum(numbers):
    """Find minimum value in a list"""
    if not numbers:
        return None
    return min(numbers)
