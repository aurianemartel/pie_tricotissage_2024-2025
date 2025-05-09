# utils.py

def greet_user(name):
    if not name:
        raise ValueError("Name cannot be empty.")
    return f"Hello, {name}!"

def say_goodbye(name):
    if not name:
        raise ValueError("Name cannot be empty.")
    return f"Goodbye, {name}!"

def shout(name):
    if not name:
        raise ValueError("Name cannot be empty.")
    return name.upper() + "!!!"
