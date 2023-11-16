import torch
import random
from PIL import Image, ImageTk
import io
import os
from diffusers import StableDiffusionXLPipeline
import datetime
import tkinter as tk
import pyperclip
import win32clipboard

# Define a dictionary to store the input field values
input_values = {
    "prompt": "",
    "aspect_ratio": "",
    "upscale": "",
    "steps": "",
    "seed": ""
}

# Initialize the Stable Diffusion pipeline
pipe = StableDiffusionXLPipeline.from_pretrained("segmind/SSD-1B", torch_dtype=torch.float16, use_safetensors=True, variant="fp16")
pipe.to("cuda")

root = tk.Tk()
root.title("Image Viewer")

output_folder = './OUTPUT'
default_image = 'output_20231107-144208.jpg'  # Corrected filename format
script_directory = os.path.dirname(os.path.realpath(__file__))  # Directory where the script is located
default_image_path = os.path.join(script_directory, default_image)

# Define label variable
label = tk.Label(root)
label.pack()

# Function to clear input fields
def clear_input_fields():
    prompt_entry.delete(0, tk.END)
    aspect_ratio_entry.delete(0, tk.END)
    upscale_entry.delete(0, tk.END)
    steps_entry.delete(0, tk.END)
    seed_entry.delete(0, tk.END)

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
    steps_input = steps_var.get()
    steps = int(steps_input) if steps_input.isdigit() else 20
    seed_input = seed_var.get()
    seed = int(seed_input) if seed_input.isdigit() else None

    input_values["prompt"] = prompt
    input_values["aspect_ratio"] = ar
    input_values["upscale"] = upscale
    input_values["steps"] = steps
    input_values["seed"] = seed

    clear_input_fields()  # Clear input fields when generating

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

def copy_image_to_clipboard():
    global default_image_path, img

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()

    if img is not None:
        # Convert the PhotoImage to a PIL Image
        img_pil = Image.new("RGBA", (img.width(), img.height()))
        img_pil.paste(img, (0, 0))
        output = io.BytesIO()
        img_pil.save(output, format="BMP")
        data = output.getvalue()[14:]  # BMP file header is 14 bytes
        output.close()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    else:
        # Load the default image from disk
        image = Image.open(default_image_path)
        output = io.BytesIO()
        image.save(output, format="BMP")
        data = output.getvalue()[14:]  # BMP file header is 14 bytes
        output.close()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)

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
input_frame = tk.Frame(root)
input_frame.pack()

prompt_label = tk.Label(input_frame, text="Prompt:")
prompt_label.pack()

prompt_entry = tk.Entry(input_frame)
prompt_entry.pack()

aspect_ratio_label = tk.Label(input_frame, text="Aspect Ratio (1. Square, 2. Widescreen, 3. Tall, 4. Ultra Widescreen):")
aspect_ratio_label.pack()

aspect_ratio_var = tk.StringVar()
aspect_ratio_entry = tk.Entry(input_frame, textvariable=aspect_ratio_var)
aspect_ratio_entry.pack()

upscale_label = tk.Label(input_frame, text="Upscale? (y/n):")
upscale_label.pack()

upscale_var = tk.StringVar()
upscale_entry = tk.Entry(input_frame, textvariable=upscale_var)
upscale_entry.pack()

steps_label = tk.Label(input_frame, text="Number of Steps (default: 20):")
steps_label.pack()

steps_var = tk.StringVar()
steps_entry = tk.Entry(input_frame, textvariable=steps_var)
steps_entry.pack()

seed_label = tk.Label(input_frame, text="Seed (optional):")
seed_label.pack()

seed_var = tk.StringVar()
seed_entry = tk.Entry(input_frame, textvariable=seed_var)
seed_entry.pack()

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