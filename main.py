import torch
import random
from PIL import Image, ImageTk
import io
import os
from diffusers import StableDiffusionXLPipeline
import datetime
import tkinter as tk
import shutil
import pyperclip
import base64
import tempfile
import subprocess
import win32clipboard

# Initialize the Stable Diffusion pipeline
pipe = StableDiffusionXLPipeline.from_pretrained("segmind/SSD-1B", torch_dtype=torch.float16, use_safetensors=True, variant="fp16")
pipe.to("cuda")

root = tk.Tk()
root.title("Image Viewer")

output_folder = './OUTPUT'
default_image = 'output_20231107-144208.jpg'
script_directory = os.path.dirname(os.path.realpath(__file__))
default_image_path = os.path.join(script_directory, default_image)
last_generated_image_path = None

# Define label variable for the image
label = tk.Label(root)
label.pack()

def update_image(filename, is_upscaled, is_default_image=False):
    global img, label
    img = Image.open(filename)
    resize_ratio = 0.5 if is_upscaled or is_default_image else 1.0
    img = img.resize((int(img.width * resize_ratio), int(img.height * resize_ratio)), Image.BILINEAR)
    img = ImageTk.PhotoImage(img)
    label.configure(image=img)
    label.image = img

def generate_image(prompt, width, height, steps):
    response = pipe(prompt=prompt, width=width, height=height, num_inference_steps=steps)
    image = response.images[0]
    return image

def handle_user_input():
    global last_prompt, last_ar, last_steps, last_upscale, image_generated, last_generated_image_path
    prompt = prompt_entry.get("1.0", "end-1c")  # Retrieve the text from the prompt input
    ar = aspect_ratio_var.get() or '1'  # Get the aspect ratio
    upscale = upscale_var.get() == 'y'  # Determine if upscaling is selected
    steps_input = steps_var.get()  # Get the number of steps from the input
    steps = int(steps_input) if steps_input.isdigit() else 20  # Convert steps to an integer, default to 20 if not specified

    # Set the base width and height based on the aspect ratio
    base_width, base_height = 512, 512  # Default: Square
    if ar == '2':
        base_width, base_height = 672, 384  # Widescreen
    elif ar == '3':
        base_width, base_height = 448, 576  # Tall
    elif ar == '4':
        base_width, base_height = 768, 320  # Ultra Widescreen

    # Determine the final width and height, considering whether upscaling is enabled
    width, height = (base_width * 2, base_height * 2) if upscale else (base_width, base_height)

    # Generate the image
    image = generate_image(prompt, width, height, steps)

    # Create a filename for the generated image
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = os.path.join(output_folder, f"output_{timestamp}.jpg")

    # Save the generated image to a file
    with io.BytesIO() as output_bytes:
        image.save(output_bytes, format="JPEG")
        image_data = output_bytes.getvalue()
    with open(filename, "wb") as file:
        file.write(image_data)

    # Update the displayed image
    update_image(filename, upscale)

    # Update global variables
    last_prompt, last_ar, last_steps, last_upscale = prompt, ar, steps, upscale
    last_generated_image_path = filename
    image_generated = True

    # Clear the prompt after generating the image
    prompt_entry.delete("1.0", "end")


def copy_image_to_clipboard():
    global last_generated_image_path
    if last_generated_image_path is None:
        return

    with Image.open(last_generated_image_path) as img:
        output = io.BytesIO()
        img.save(output, format="BMP")
        data = output.getvalue()[14:]
        output.close()

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()

# Create output folder if it doesn't exist
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Display default image on startup if it exists
if os.path.exists(default_image_path):
    update_image(default_image_path, False, is_default_image=True)
    first_image_displayed = True
else:
    first_image_displayed = False

# User input fields and buttons

# Prompt Input Frame
prompt_frame = tk.Frame(root)
prompt_frame.pack(fill='x', padx=5, pady=5)  # Adding padding for better spacing

prompt_label = tk.Label(prompt_frame, text="Prompt:\n")
prompt_label.pack(side=tk.LEFT, padx=5)

prompt_entry = tk.Text(prompt_frame, height=3, width=60)  # Changed to Text widget for multiline input, width adjusted
prompt_entry.pack(side=tk.LEFT, expand=True, fill='x')

# Number of Steps Frame
steps_frame = tk.Frame(root)
steps_frame.pack(fill='x')

steps_label = tk.Label(steps_frame, text="Number of Steps (default: 20):")
steps_label.pack(side=tk.LEFT)

steps_var = tk.StringVar()
steps_entry = tk.Entry(steps_frame, textvariable=steps_var, width=4)
steps_entry.pack(side=tk.LEFT)

# Aspect Ratio Frame
aspect_ratio_frame = tk.Frame(root)
aspect_ratio_frame.pack(fill='x')

aspect_ratio_label = tk.Label(aspect_ratio_frame, text="Aspect Ratio:")
aspect_ratio_label.pack(side=tk.LEFT)

aspect_ratios = {'BOX': '1', 'WIDE': '2', 'TALL': '3', 'UHD': '4'}
aspect_ratio_var = tk.StringVar(value='1')
for text, value in aspect_ratios.items():
    tk.Radiobutton(aspect_ratio_frame, text=text, variable=aspect_ratio_var, value=value).pack(side=tk.LEFT)

# Upscale Option Frame
upscale_frame = tk.Frame(root)
upscale_frame.pack(fill='x')

upscale_label = tk.Label(upscale_frame, text="Upscale?")
upscale_label.pack(side=tk.LEFT)

upscale_var = tk.StringVar(value='n')
tk.Radiobutton(upscale_frame, text="Yes", variable=upscale_var, value='y').pack(side=tk.LEFT)
tk.Radiobutton(upscale_frame, text="No", variable=upscale_var, value='n').pack(side=tk.LEFT)

# Button Frame
button_frame = tk.Frame(root)
button_frame.pack()

generate_button = tk.Button(button_frame, text="Generate Image", command=handle_user_input)
generate_button.pack(side=tk.LEFT, padx=5)

copy_button = tk.Button(button_frame, text="Copy Image", command=copy_image_to_clipboard)
copy_button.pack(side=tk.LEFT, padx=5)

# Right-click context menu
right_click_menu = tk.Menu(root, tearoff=0)
right_click_menu.add_command(label="Copy Image", command=copy_image_to_clipboard)

label.bind("<Button-3>", lambda event: right_click_menu.post(event.x_root, event.y_root))

# Main loop
while True:
    root.update_idletasks()
    root.update()
