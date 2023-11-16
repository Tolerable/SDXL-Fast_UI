import torch
from PIL import Image, ImageTk
import io
import os
from diffusers import StableDiffusionXLPipeline
import datetime
import tkinter as tk

# Initialize the Stable Diffusion pipeline
pipe = StableDiffusionXLPipeline.from_pretrained("segmind/SSD-1B", torch_dtype=torch.float16, use_safetensors=True, variant="fp16")
pipe.to("cuda")

root = None
label = None

output_folder = './OUTPUT'
default_image = 'output_20231107 - 144208.jpg'
default_image_path = os.path.join(output_folder, default_image)

def create_window():
    global root, label
    root = tk.Tk()
    root.title("Image Viewer")
    label = tk.Label(root)
    label.pack()

def update_image(filename, is_upscaled):
    global img, root, label
    img = Image.open(filename)
    resize_ratio = 0.5 if is_upscaled else 1.0
    img = img.resize((int(img.width * resize_ratio), int(img.height * resize_ratio)), Image.BILINEAR)
    img = ImageTk.PhotoImage(img)
    label.configure(image=img)
    label.image = img

def generate_image(prompt, width, height, steps, seed=None):
    return pipe(prompt=prompt, width=width, height=height, num_inference_steps=steps, seed=seed).images[0]

last_prompt, last_ar, last_steps, last_seed, last_upscale, image_generated = None, None, None, None, None, False

# Create output folder if it doesn't exist
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Display default image on startup if it exists
if os.path.exists(default_image_path):
    create_window()
    update_image(default_image_path, False)
    image_generated = True

while True:
    if image_generated:
        redo = input("Redo last image? (y/n, default: n): ").strip().lower() == 'y'
        if redo:
            prompt, ar, steps, seed, upscale = last_prompt, last_ar, last_steps, last_seed, last_upscale
        else:
            image_generated = False  # Reset flag if not redoing

    if not image_generated:
        prompt = input("Prompt: ").strip()
        if prompt.lower() == 'exit':
            break
        elif prompt == '':
            continue

        ar = input("Aspect ratio (default: 1. Square):\n1. Square\n2. Widescreen\n3. Tall\n4. Ultra Widescreen\n") or '1'
        upscale = input("Upscale? (y/n, default: n): ").strip().lower() == 'y'
        steps_input = input("Number of steps (default: 20, press Enter to use default): ") or '20'
        seed_input = input("Seed (optional, press Enter for random): ").strip()
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

    image = generate_image(prompt, width, height, steps, seed)

    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = os.path.join(output_folder, f"output_{timestamp}.jpg")

    with io.BytesIO() as output_bytes:
        image.save(output_bytes, format="JPEG")
        image_data = output_bytes.getvalue()

    with open(filename, "wb") as file:
        file.write(image_data)

    if not root:
        create_window()
    update_image(filename, upscale)

    last_prompt, last_ar, last_steps, last_seed, last_upscale = prompt, ar, steps, seed, upscale
    image_generated = True  # Set flag to indicate an image has been generated

    root.update_idletasks()
    root.update()
