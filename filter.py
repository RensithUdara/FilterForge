import cv2
import numpy as np
from tkinter import *
from tkinter import filedialog, ttk, simpledialog, messagebox
from PIL import Image, ImageTk
from functools import partial
import threading

class ImageFilterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Filter App")
        self.root.geometry("900x800")
        self.root.configure(bg="#2C2F33")
        
        # Image variables
        self.original_image = None
        self.filtered_image = None
        self.undo_stack = []
        self.max_undo_steps = 15
        
        # Filter parameters
        self.blur_radius = 15
        self.canny_low = 100
        self.canny_high = 200
        self.sketch_sigma = 21
        
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the UI components"""
        # Menu bar
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Image", command=self.load_image, accelerator="Ctrl+O")
        file_menu.add_command(label="Save Image", command=self.save_image, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        edit_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Reset", command=self.reset_image)

        # Bind shortcuts
        self.root.bind("<Control-o>", lambda e: self.load_image())
        self.root.bind("<Control-s>", lambda e: self.save_image())
        self.root.bind("<Control-z>", lambda e: self.undo())

        # Main frames
        self.top_frame = Frame(self.root, bg="#23272A")
        self.top_frame.pack(pady=10, fill=X)

        self.filter_frame = Frame(self.top_frame, bg="#23272A")
        self.filter_frame.pack(side=LEFT, padx=10)

        self.control_frame = Frame(self.top_frame, bg="#23272A")
        self.control_frame.pack(side=RIGHT, padx=10)

        # Filter buttons
        filters = [
            ("Grayscale", "#808080", self.apply_grayscale),
            ("Blur", "#3498DB", self.apply_blur),
            ("Edges", "#E74C3C", self.apply_edges),
            ("Sharpen", "#27AE60", self.apply_sharpen),
            ("Pencil Sketch", "#D4AC0D", self.apply_pencil_sketch),
            ("Sepia", "#8B4513", self.apply_sepia),
            ("Invert", "#FF00FF", self.apply_invert),
            ("Emboss", "#4682B4", self.apply_emboss)
        ]

        for i, (text, color, func) in enumerate(filters):
            btn = Button(self.filter_frame, text=text, bg=color, fg="white", width=12, 
                        height=2, relief=RAISED, font=("Arial", 11, "bold"), 
                        command=partial(self.apply_filter, func))
            btn.grid(row=i//4, column=i%4, padx=5, pady=5)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="white", fg="black"))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.config(bg=c, fg="white"))

        # Control buttons
        actions = [
            ("Load", self.load_image),
            ("Save", self.save_image),
            ("Undo", self.undo),
            ("Resize", self.resize_image),
            ("Reset", self.reset_image)
        ]

        for i, (text, cmd) in enumerate(actions):
            Button(self.control_frame, text=text, bg="#1F1F1F", fg="white", width=10, 
                  height=2, font=("Arial", 11, "bold"), command=cmd).grid(row=i, column=0, pady=5)

        # Parameter adjustment frame
        self.param_frame = Frame(self.root, bg="#2C2F33")
        self.param_frame.pack(pady=10)

        # Sliders
        self.brightness_slider = Scale(self.param_frame, from_=-100, to_=100, orient=HORIZONTAL, 
                                     label="Brightness", command=self.on_brightness_change, 
                                     bg="#2C2F33", fg="white", font=("Helvetica", 10), length=200)
        self.brightness_slider.pack(pady=5)

        self.contrast_slider = Scale(self.param_frame, from_=0, to_=3, resolution=0.1, orient=HORIZONTAL, 
                                   label="Contrast", command=self.on_contrast_change, 
                                   bg="#2C2F33", fg="white", font=("Helvetica", 10), length=200)
        self.contrast_slider.pack(pady=5)

        self.blur_slider = Scale(self.param_frame, from_=3, to_=51, orient=HORIZONTAL, 
                                label="Blur Radius (odd)", command=self.update_blur_radius, 
                                bg="#2C2F33", fg="white", font=("Helvetica", 10), length=200)
        self.blur_slider.set(self.blur_radius)
        self.blur_slider.pack(pady=5)

        # Image display
        self.image_label = Label(self.root, bg="#2C2F33", width=600, height=450, relief="solid", bd=2)
        self.image_label.pack(pady=20)

        # Status bar
        self.status_label = Label(self.root, text="Ready", bg="#2C2F33", fg="white", font=("Arial", 10))
        self.status_label.pack(pady=5, fill=X)

    def convert_image(self, img):
        """Convert OpenCV image to Tkinter-compatible format"""
        try:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            messagebox.showerror("Error", f"Image conversion failed: {str(e)}")
            return None

    def update_image(self, img):
        """Update the displayed image"""
        tk_img = self.convert_image(img)
        if tk_img:
            self.image_label.config(image=tk_img)
            self.image_label.image = tk_img

    def load_image(self):
        """Load an image from file"""
        file_path = filedialog.askopenfilename(title="Select an Image", 
                                             filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])
        if file_path:
            threading.Thread(target=self._load_image_thread, args=(file_path,), daemon=True).start()

    def _load_image_thread(self, file_path):
        """Load image in a separate thread"""
        img = cv2.imread(file_path)
        if img is not None:
            # Maintain aspect ratio while fitting within 600x450
            h, w = img.shape[:2]
            scale = min(600/w, 450/h)
            new_w, new_h = int(w * scale), int(h * scale)
            self.original_image = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            self.filtered_image = self.original_image.copy()
            self.undo_stack.clear()
            self.update_image(self.original_image)
            self.status_label.config(text=f"Loaded: {file_path.split('/')[-1]} | {new_w}x{new_h} px")
        else:
            messagebox.showerror("Error", "Failed to read the image file")

    def apply_filter(self, filter_func):
        """Apply a filter and manage undo stack"""
        if self.original_image is None:
            messagebox.showwarning("Warning", "Please load an image first!")
            return
        self.undo_stack.append(self.filtered_image.copy())
        if len(self.undo_stack) > self.max_undo_steps:
            self.undo_stack.pop(0)
        filter_func()
        self.update_image(self.filtered_image)
        self.status_label.config(text=f"Applied: {filter_func.__name__[6:]}")  # Extract filter name

    # Filter Functions
    def apply_grayscale(self):
        self.filtered_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
        self.filtered_image = cv2.cvtColor(self.filtered_image, cv2.COLOR_GRAY2RGB)

    def apply_blur(self):
        radius = self.blur_radius if self.blur_radius % 2 == 1 else self.blur_radius + 1
        self.filtered_image = cv2.GaussianBlur(self.original_image, (radius, radius), 0)

    def apply_edges(self):
        self.filtered_image = cv2.Canny(self.original_image, self.canny_low, self.canny_high)
        self.filtered_image = cv2.cvtColor(self.filtered_image, cv2.COLOR_GRAY2RGB)

    def apply_sharpen(self):
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
        self.filtered_image = cv2.filter2D(self.original_image, -1, kernel)

    def apply_pencil_sketch(self):
        gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
        inv_gray = 255 - gray
        blurred = cv2.GaussianBlur(inv_gray, (self.sketch_sigma, self.sketch_sigma), 0)
        self.filtered_image = cv2.cvtColor(cv2.divide(gray, 255 - blurred, scale=256), cv2.COLOR_GRAY2RGB)

    def apply_sepia(self):
        kernel = np.array([[0.272, 0.534, 0.131],
                          [0.349, 0.686, 0.168],
                          [0.393, 0.769, 0.189]])
        self.filtered_image = cv2.transform(self.original_image, kernel)
        self.filtered_image = np.clip(self.filtered_image, 0, 255).astype(np.uint8)

    def apply_invert(self):
        self.filtered_image = cv2.bitwise_not(self.original_image)

    def apply_emboss(self):
        kernel = np.array([[ -2, -1,  0],
                          [ -1,  1,  1],
                          [  0,  1,  2]])
        gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
        embossed = cv2.filter2D(gray, -1, kernel)
        self.filtered_image = cv2.cvtColor(embossed, cv2.COLOR_GRAY2RGB)

    def undo(self):
        """Undo the last filter application"""
        if self.undo_stack:
            self.filtered_image = self.undo_stack.pop()
            self.update_image(self.filtered_image)
            self.status_label.config(text="Undo applied")
        else:
            self.status_label.config(text="Nothing to undo")

    def resize_image(self):
        """Resize the current image"""
        if self.filtered_image is None:
            return
        resize_input = simpledialog.askstring("Resize Image", "Enter width and height (e.g., 800x600):")
        if resize_input:
            try:
                width, height = map(int, resize_input.split('x'))
                if width <= 0 or height <= 0:
                    raise ValueError("Width and height must be positive")
                self.filtered_image = cv2.resize(self.filtered_image, (width, height), interpolation=cv2.INTER_AREA)
                self.update_image(self.filtered_image)
                self.status_label.config(text=f"Resized to {width}x{height} px")
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid input: {str(e)}")

    def adjust_brightness_contrast(self):
        """Adjust brightness and contrast"""
        if self.original_image is None:
            return
        brightness = self.brightness_slider.get()
        contrast = self.contrast_slider.get()
        self.filtered_image = cv2.convertScaleAbs(self.original_image, alpha=contrast, beta=brightness)
        self.update_image(self.filtered_image)

    def on_brightness_change(self, val):
        self.adjust_brightness_contrast()

    def on_contrast_change(self, val):
        self.adjust_brightness_contrast()

    def update_blur_radius(self, val):
        """Update blur radius and reapply blur if active"""
        self.blur_radius = int(val)
        if "blur" in self.status_label.cget("text").lower():
            self.apply_blur()
            self.update_image(self.filtered_image)

    def reset_image(self):
        """Reset to original image"""
        if self.original_image is not None:
            self.filtered_image = self.original_image.copy()
            self.undo_stack.clear()
            self.brightness_slider.set(0)
            self.contrast_slider.set(1)
            self.blur_slider.set(15)
            self.update_image(self.filtered_image)
            self.status_label.config(text="Image reset")

    def save_image(self):
        """Save the current image"""
        if self.filtered_image is None:
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".png", 
                                               filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("All Files", "*.*")])
        if file_path:
            try:
                cv2.imwrite(file_path, self.filtered_image)
                self.status_label.config(text=f"Saved: {file_path.split('/')[-1]}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image: {str(e)}")

if __name__ == "__main__":
    root = Tk()
    app = ImageFilterApp(root)
    root.mainloop()