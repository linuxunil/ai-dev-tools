"""
Problematic code with known safety and quality issues
"""

import os
import pickle
import subprocess


# Security issue: Command injection vulnerability
def execute_user_command(user_input):
    """Execute user command - UNSAFE!"""
    os.system(user_input)  # Command injection risk


def run_shell_command(cmd):
    """Run shell command - UNSAFE!"""
    subprocess.call(cmd, shell=True)  # Shell injection risk


# Security issue: Pickle deserialization
def load_user_data(data_file):
    """Load user data - UNSAFE!"""
    with open(data_file, "rb") as f:
        return pickle.load(f)  # Arbitrary code execution risk


# Quality issue: No error handling
def divide_unsafe(a, b):
    """Divide without error handling"""
    return a / b  # Division by zero risk


# Quality issue: Resource leak
def read_file_unsafe(filename):
    """Read file without proper cleanup"""
    f = open(filename)  # File handle leak
    return f.read()


# Quality issue: SQL injection (simulated)
def get_user_data(user_id):
    """Get user data - SQL injection risk"""
    query = f"SELECT * FROM users WHERE id = {user_id}"  # SQL injection
    return query


# Quality issue: Hardcoded secrets
API_KEY = "sk-1234567890abcdef"  # Hardcoded secret
DATABASE_PASSWORD = "admin123"  # Hardcoded password


# Quality issue: Infinite loop potential
def process_items(items):
    """Process items with potential infinite loop"""
    i = 0
    while i < len(items):
        if items[i] == "skip":
            continue  # i never incremented - infinite loop
        print(items[i])
        i += 1


# Quality issue: Memory leak potential
global_cache = {}


def cache_data(key, value):
    """Cache data without cleanup"""
    global_cache[key] = value  # Never cleaned up
