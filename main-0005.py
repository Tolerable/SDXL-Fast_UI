import torch
import random
from PIL import Image, ImageTk
import io
import os
from diffusers import StableDiffusionXLPipeline
import datetime
import tkinter as tk

# Initialize the Stable Diffusion pipeline
pipe = StableDiffusionXLPipeline.from_pretrained("segmind/SSD-1B", torch_dtype=torch.float16, use_safetensors=True, variant="fp16")
pipe.to("cuda")

root = tk.Tk()
root.title("Image Viewer")
label = tk.Label(root)
label.pack()

output_folder = './OUTPUT'
default_image = 'output_20231107-144208.jpg'  # Corrected filename format
script_directory = os.path.dirname(os.path.realpath(__file__))  # Directory where the script is located
default_image_path = os.path.join(script_directory, default_image)

def update_image(filename, is_upscaled, is_default_image=False):
    global img, label
    img = Image.open(filename)
    resize_ratio = 0.5 if is_upscaled or is_default_image else 1.0
    img = img.resize((int(img.width * resize_ratio), int(img.height * resize_ratio)), Image.BILINEAR)
    img = ImageTk.PhotoImage(img)
    label.configure(image=img)
    label.image = img

def generate_image(prompt, width, height, steps, seed=None):
    if seed is None:
        seed = random.randint(0, 2**32 - 1)  # Generate a random seed if none provided
    response = pipe(prompt=prompt, width=width, height=height, num_inference_steps=steps, seed=seed)
    image = response.images[0]
    return image, seed  # Return the image and the seed

def handle_user_input():
    global last_prompt, last_ar, last_steps, last_seed, last_upscale, image_generated
    prompt = prompt_entry.get()
    ar = aspect_ratio_var.get() or '1'
    upscale = upscale_var.get() == 'y'
    steps = int(steps_var.get() or '20')
    seed_input = seed_var.get()
    seed = int(seed_input) if seed_input.isdigit() else None

    steps = int(steps_input)
    base_width, base_height = 512, 512  # Adjusted base dimensions for Square
    if ar == '2':
        base_width, base_height = 672, 384  # Adjusted for Widescreen
    elif ar == '3':
        base_width, base_height = 448, 576  # Adjusted for Tall
    elif ar == '4':
        base_width, base_height = 768, 320  # Adjusted for Ultra Widescreen

    width, height = (base_width * 2, base_height * 2) if upscale else (base_width, base_height)

    image, seed = generate_image(prompt, width, height, steps, seed)

    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = os.path.join(output_folder, f"output_{timestamp}.jpg")

    with io.BytesIO() as output_bytes:
        image.save(output_bytes, format="JPEG")
        image_data = output_bytes.getvalue()

    with open(filename, "wb") as file:
        file.write(image_data)

    update_image(filename, upscale)

    last_prompt, last_ar, last_steps, last_seed, last_upscale = prompt, ar, steps, seed, upscale
    image_generated = True

def copy_image_to_clipboard(event=None):
    global img
    clipboard = tk.Toplevel()
    clipboard.withdraw()
    clipboard.clipboard_clear()
    clipboard.clipboard_append(ImageTk.getimage(img))
    clipboard.update()
    clipboard.destroy()

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
prompt_entry = tk.Entry(root)
prompt_entry.pack()

aspect_ratio_var = tk.StringVar()
aspect_ratio_entry = tk.Entry(root, textvariable=aspect_ratio_var)
aspect_ratio_entry.pack()

upscale_var = tk.StringVar()
upscale_entry = tk.Entry(root, textvariable=upscale_var)
upscale_entry.pack()

steps_var = tk.StringVar()
steps_entry = tk.Entry(root, textvariable=steps_var)
steps_entry.pack()

seed_var = tk.StringVar()
seed_entry = tk.Entry(root, textvariable=seed_var)
seed_entry.pack()

generate_button = tk.Button(root, text="Generate Image", command=handle_user_input)
generate_button.pack()

label.bind("<Button-3>", copy_image_to_clipboard)  # Right-click copy

# Main loop
while True:
    root.update_idletasks()
    root.update()
