import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from PIL import ImageTk
from PIL import Image
from io import BytesIO



root = tk.Tk()
root.geometry("400x400")
frm = ttk.Frame(root, padding=10)
frm.pack()

ttk.Button(frm, text="Choisir image").pack(side='bottom')

ttk.Label(frm, text="Hello World!").pack(side='right')
ttk.Button(frm, text="Quit", command=root.destroy).pack(side='left')

curseur = tk.Scale(root, orient = "horizontal", from_=0, to=400, length=300)
curseur.pack()



root.mainloop()





