import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk


class Application:
    def __init__(self, window, window_title, image_path):
        self.window = window
        self.window.title(window_title)
        self.image_path = image_path

        # Canvas size
        self.canvas_width = 500
        self.canvas_height = 700
        self.margin = 40  # margin around image

        self.canvas = tk.Canvas(window, width=self.canvas_width, height=self.canvas_height, bg='azure3', relief='raised')

        # Headline
        self.headline_label = tk.Label(text="IMAGE PROCESSING", bg='azure3')
        self.canvas.create_window(80, 20, window=self.headline_label)

        # Load initial image
        self.img = Image.open(self.image_path)
        self.resized_img = self.resize_image_to_fit(self.img)
        self.pic = ImageTk.PhotoImage(self.resized_img)
        self.down_window_label = tk.Label(image=self.pic)
        self.down_window_label.image = self.pic  # keep reference

        # Center image in canvas
        center_x = self.canvas_width // 2
        center_y = self.canvas_height // 2
        self.image_window = self.canvas.create_window(center_x, center_y, window=self.down_window_label)

        # Buttons
        self.load_button = tk.Button(text="LOAD IMAGE", command=self.load_image)
        self.close_button = tk.Button(text="CLOSE", command=self.window.destroy)

        self.canvas.create_window(150, 650, window=self.load_button)
        self.canvas.create_window(350, 650, window=self.close_button)

        self.canvas.pack()
        self.window.mainloop()

    def load_image(self):
        file_path = filedialog.askopenfilename()
        if not file_path:
            return

        self.new_img = Image.open(file_path)
        self.resized_img = self.resize_image_to_fit(self.new_img)
        self.pic = ImageTk.PhotoImage(self.resized_img)

        # Destroy previous label if it exists
        if hasattr(self, 'down_window_label'):
            self.down_window_label.destroy()

        self.down_window_label = tk.Label(image=self.pic)
        self.down_window_label.image = self.pic  # keep reference

        # Replace the old image window with a new centered one
        center_x = self.canvas_width // 2
        center_y = self.canvas_height // 2
        self.canvas.create_window(center_x, center_y, window=self.down_window_label)

    def resize_image_to_fit(self, image):
        max_width = self.canvas_width - self.margin
        max_height = self.canvas_height - self.margin

        img_width, img_height = image.size
        ratio = min(max_width / img_width, max_height / img_height)

        new_size = (int(img_width * ratio), int(img_height * ratio))
        return image.resize(new_size, Image.Resampling.LANCZOS)


# Launch the app
Application(tk.Tk(), "IMAGE_PROCESSING_APPLICATION", "image.jpg")
