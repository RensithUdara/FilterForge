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
        self.root.geometry("850x750")
        self.root.configure(bg="#2C2F33")
        
        # Image variables
        self.original_image = None
        self.filtered_image = None
        self.undo_stack = []
        self.max_undo_steps = 10  # Limit undo stack size
        
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the UI components"""
        # Style configuration
        style = ttk.Style()
        style.configure("TButton", font=("Arial", 12, "bold"), padding=10)

        # Filter buttons frame
        self.button_frame = Frame(self.root, bg="#23272A")
        self.button_frame.pack(pady=15)

        filters = [
            ("Grayscale", "#808080", self.apply_grayscale),
            ("Blur", "#3498DB", self.apply_blur),
            ("Edges", "#E74C3C", self.apply_edges),
            ("Sharpen", "#27AE60", self.apply_sharpen),
            ("Pencil Sketch", "#D4AC0D", self.apply_pencil_sketch)
        ]

        for text, color, func in filters:
            btn = Button(self.button_frame, text=text, bg=color, fg="white", width=12, 
                        height=2, relief=RAISED, font=("Arial", 12, "bold"), 
                        command=partial(self.apply_filter, func))
            btn.pack(side=LEFT, padx=10)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="white", fg="black"))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.config(bg=c, fg="white"))

        # Action buttons frame
        self.action_frame = Frame(self.root, bg="#23272A")
        self.action_frame.pack(pady=10)

        action_buttons = [
            ("Load Image", self.load_image),
            ("Save Image", self.save_image),
            ("Undo", self.undo),
            ("Resize Image", self.resize_image),
            ("Reset Image", self.reset_image)
        ]

        for text, cmd in action_buttons:
            Button(self.action_frame, text=text, bg="#1F1F1F", fg="white", width=12, 
                  height=2, font=("Arial", 12, "bold"), command=cmd).pack(side=LEFT, padx=5)

        # Sliders frame
        self.slider_frame = Frame(self.root, bg="#2C2F33")
        self.slider_frame.pack(pady=10)

        self.brightness_slider = Scale(self.slider_frame, from_=-100, to_=100, orient=HORIZONTAL, 
                                     label="Brightness", command=self.on_brightness_change, 
                                     bg="#2C2F33", fg="white", font=("Helvetica", 12))
        self.brightness_slider.pack(side=LEFT, padx=20)

        self.contrast_slider = Scale(self.slider_frame, from_=0, to_=3, resolution=0.1, orient=HORIZONTAL, 
                                   label="Contrast", command=self.on_contrast_change, 
                                   bg="#2C2F33", fg="white", font=("Helvetica", 12))
        self.contrast_slider.pack(side=LEFT, padx=20)

        # Image display
        self.image_label = Label(self.root, bg="#2C2F33", width=500, height=400, relief="solid", bd=2)
        self.image_label.pack(pady=20)

        # Status bar
        self.status_label = Label(self.root, text="Ready", bg="#2C2F33", fg="white", font=("Arial", 10))
        self.status_label.pack(pady=5)

    def convert_image(self, img):
        """Convert OpenCV image to Tkinter-compatible format"""
        try:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to convert image: {str(e)}")
            return None

    def update_image(self, img):
        """Update the displayed image"""
        tk_img = self.convert_image(img)
        if tk_img:
            self.image_label.config(image=tk_img)
            self.image_label.image = tk_img  # Keep reference to prevent garbage collection

    def load_image(self):
        """Load an image from file"""
        file_path = filedialog.askopenfilename(title="Select an Image", 
                                             filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])
        if file_path:
            try:
                threading.Thread(target=self._load_image_thread, args=(file_path,), daemon=True).start()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {str(e)}")

    def _load_image_thread(self, file_path):
        """Load image in a separate thread to prevent UI freeze"""
        self.original_image = cv2.imread(file_path)
        if self.original_image is not None:
            self.original_image = cv2.resize(self.original_image, (500, 400), interpolation=cv2.INTER_AREA)
            self.filtered_image = self.original_image.copy()
            self.undo_stack.clear()
            self.update_image(self.original_image)
            self.status_label.config(text=f"Loaded: {file_path.split('/')[-1]} | {self.original_image.shape[1]}x{self.original_image.shape[0]} px")
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

    # Filter methods
    def apply_grayscale(self):
        self.filtered_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
        self.filtered_image = cv2.cvtColor(self.filtered_image, cv2.COLOR_GRAY2RGB)

    def apply_blur(self):
        self.filtered_image = cv2.GaussianBlur(self.original_image, (15, 15), 0)

    def apply_edges(self):
        self.filtered_image = cv2.Canny(self.original_image, 100, 200)
        self.filtered_image = cv2.cvtColor(self.filtered_image, cv2.COLOR_GRAY2RGB)

    def apply_sharpen(self):
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        self.filtered_image = cv2.filter2D(self.original_image, -1, kernel)

    def apply_pencil_sketch(self):
        gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
        inv_gray = 255 - gray
        blurred = cv2.GaussianBlur(inv_gray, (21, 21), 0)
        self.filtered_image = cv2.cvtColor(cv2.divide(gray, 255 - blurred, scale=256), cv2.COLOR_GRAY2RGB)

    def undo(self):
        """Undo the last filter application"""
        if self.undo_stack:
            self.filtered_image = self.undo_stack.pop()
            self.update_image(self.filtered_image)
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

    def reset_image(self):
        """Reset to original image"""
        if self.original_image is not None:
            self.filtered_image = self.original_image.copy()
            self.undo_stack.clear()
            self.brightness_slider.set(0)
            self.contrast_slider.set(1)
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