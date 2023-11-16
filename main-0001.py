import torch
from PIL import Image, ImageTk
import io
import os
import base64
from diffusers import StableDiffusionXLPipeline
import datetime
import pyperclip
import tkinter as tk
import win32clipboard

# Initialize the Stable Diffusion pipeline
pipe = StableDiffusionXLPipeline.from_pretrained("segmind/SSD-1B", torch_dtype=torch.float16, use_safetensors=True, variant="fp16")
pipe.to("cuda")

# Ensure the OUTPUT folder exists
output_folder = "./OUTPUT"
os.makedirs(output_folder, exist_ok=True)

# Initialize Tkinter window but keep it hidden
window = tk.Tk()
window.title("Image Viewer")
window.geometry("512x512")  # Set an initial size for the window
window.withdraw()  # Window starts hidden

canvas = tk.Canvas(window)
canvas.pack(fill=tk.BOTH, expand=True)

original_image = None
photo = None

def calculate_display_size(window_width, window_height, image_width, image_height):
    aspect_ratio = image_width / image_height

    if window_width / window_height > aspect_ratio:
        display_width = window_height * aspect_ratio
        display_height = window_height
    else:
        display_width = window_width
        display_height = window_width / aspect_ratio

    return int(display_width), int(display_height)

def update_image(event):
    global photo, original_image

    if not original_image:
        return

    display_width, display_height = calculate_display_size(event.width, event.height, original_image.width, original_image.height)
    resized_image = original_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(resized_image)
    canvas.delete("all")  # Clear the canvas
    canvas.create_image(0, 0, image=photo, anchor=tk.NW)  # Bind the image to the top-left corner

def display_image(image_path):
    global original_image, window, canvas

    original_image = Image.open(image_path)
    window_width = window.winfo_width()
    window_height = window.winfo_height()

    display_width, display_height = calculate_display_size(window_width, window_height, original_image.width, original_image.height)

    resized_image = original_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
    global photo
    photo = ImageTk.PhotoImage(resized_image)
    canvas.delete("all")  # Clear the canvas
    canvas.create_image(0, 0, image=photo, anchor=tk.NW)  # Bind the image to the top-left corner

    window.deiconify()  # Show the window when the image is ready
    window.bind("<Configure>", update_image)

def copy_image_to_clipboard():
    global original_image
    output = io.BytesIO()
    original_image.save(output, format="BMP")
    data = output.getvalue()[14:]  # BMP file header is 14 bytes
    output.close()

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()

def right_click(event):
    try:
        right_click_menu.tk_popup(event.x_root, event.y_root)
    finally:
        right_click_menu.grab_release()

# Right-click context menu
right_click_menu = tk.Menu(window, tearoff=0)
right_click_menu.add_command(label="Copy", command=copy_image_to_clipboard)

canvas.bind("<Button-3>", right_click)  # Bind right-click event

while True:
    prompt = input("Prompt: ")

    if prompt.lower() == 'exit':
        break

    ar = input("Aspect ratio:\n1. Square\n2. Widescreen\n3. Tall\n4. Ultra Widescreen\n")
    if ar not in ['1', '2', '3', '4']:
        print("Please enter a valid choice. 1, 2, 3, or 4")
        continue

    ar = int(ar)
    width, height = {1: (1024, 1024), 2: (1344, 768), 3: (896, 1152), 4: (1536, 640)}.get(ar, (1024, 1024))

    generated_image = pipe(prompt=prompt, width=width, height=height).images[0]
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = os.path.join(output_folder, f"output_{timestamp}.jpg")
    generated_image.save(filename)

    display_image(filename)

window.destroy()
