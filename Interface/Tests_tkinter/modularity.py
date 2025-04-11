# main_app.py

import tkinter as tk
from utils import greet_user, say_goodbye, shout

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Function Caller")

        self.label = tk.Label(root, text="Enter your name:")
        self.label.pack(pady=5)

        self.entry = tk.Entry(root)
        self.entry.pack(pady=5)

        # Buttons for different functions
        tk.Button(root, text="Greet", command=lambda: self.run_function(greet_user)).pack(pady=2)
        tk.Button(root, text="Goodbye", command=lambda: self.run_function(say_goodbye)).pack(pady=2)
        tk.Button(root, text="Shout", command=lambda: self.run_function(shout)).pack(pady=2)

        self.message = tk.Label(root, text="", fg="green")
        self.message.pack(pady=10)

    def run_function(self, func):
        name = self.entry.get()
        try:
            result = func(name)  # Call the passed-in function with the entry value
            self.message.config(text=f"{result} (Success)", fg="green")
        except Exception as e:
            self.message.config(text=f"Error: {e}", fg="red")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
