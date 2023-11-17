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

# Global variable declarations
img, label = None, None
refiner_var = None  # Initialize as None
last_prompt, last_ar, last_steps, last_upscale, last_seed, last_refiner = None, None, None, None, None, None
image_generated, last_generated_image_path = False, None
seed_entry, prompt_entry, aspect_ratio_var, upscale_var, steps_var, seed_var = None, None, None, None, None, None
root, output_folder = None, None

# Initialize the Stable Diffusion pipeline
pipe = StableDiffusionXLPipeline.from_pretrained("segmind/SSD-1B", torch_dtype=torch.float16, use_safetensors=True, variant="fp16")
pipe.to("cuda")

def update_image(filename, is_upscaled, is_default_image=False):
    global img, label
    img = Image.open(filename)
    resize_ratio = 0.5 if is_upscaled or is_default_image else 1.0
    img = img.resize((int(img.width * resize_ratio), int(img.height * resize_ratio)), Image.BILINEAR)
    img = ImageTk.PhotoImage(img)
    label.configure(image=img)
    label.image = img

def generate_image(prompt, width, height, steps, seed=None, use_refiner=False):
    if seed is not None:
        response = pipe(prompt=prompt, width=width, height=height, num_inference_steps=steps, generator=torch.Generator("cuda").manual_seed(seed), use_refiner=use_refiner)
    else:
        response = pipe(prompt=prompt, width=width, height=height, num_inference_steps=steps, use_refiner=use_refiner)
    image = response.images[0]
    return image

def handle_user_input(event=None, new_generation=True):
    global last_prompt, last_ar, last_steps, last_upscale, last_seed, last_refiner, image_generated, last_generated_image_path
    
    # Get the prompt text and strip leading/trailing whitespace
    prompt = prompt_entry.get("1.0", "end-1c").strip()

    # Check if the prompt is empty
    if not prompt:
        return  # Do nothing if the prompt is empty or only contains whitespace
        
    # Check if refiner_var is initialized
    if refiner_var is None:
        return  # Exit the function if refiner_var is not yet available

    use_refiner = refiner_var.get() == 'y'
    
    prompt = prompt_entry.get("1.0", "end-1c") if new_generation or last_prompt is None else last_prompt
    ar = aspect_ratio_var.get() or '1'
    upscale = upscale_var.get() == 'y'
    steps_input = steps_var.get()
    steps = int(steps_input) if steps_input.isdigit() else 20 if new_generation or last_steps is None else last_steps
    seed_input = seed_var.get()
    seed = int(seed_input) if seed_input.isdigit() else random.randint(0, 999999999999) if new_generation or last_seed is None else last_seed


    base_width, base_height = 512, 512  
    if ar == '2':
        base_width, base_height = 672, 384
    elif ar == '3':
        base_width, base_height = 448, 576
    elif ar == '4':
        base_width, base_height = 768, 320

    width, height = (base_width * 2, base_height * 2) if upscale else (base_width, base_height)
    image = generate_image(prompt, width, height, steps, seed, use_refiner)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = os.path.join(output_folder, f"output_{timestamp}.jpg")

    with io.BytesIO() as output_bytes:
        image.save(output_bytes, format="JPEG")
        image_data = output_bytes.getvalue()
    with open(filename, "wb") as file:
        file.write(image_data)

    update_image(filename, upscale)
    if new_generation:
        last_prompt, last_ar, last_steps, last_upscale, last_seed = prompt, ar, steps, upscale, seed
    last_generated_image_path = filename
    image_generated = True

    if new_generation:
        prompt_entry.delete("1.0", "end")
        if seed_entry is not None:
            seed_entry.delete(0, tk.END)

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

def redo_image_generation():
    # Call handle_user_input for redo operation
    handle_user_input(new_generation=False)

def on_enter_key(event):
    # Call the function to handle user input submission
    handle_user_input()
    # Prevent the default behavior of the Enter key
    return "break"
	
    prompt_entry.bind("<Return>", on_enter_key)

def run_tkinter():
    global root, prompt_entry, aspect_ratio_var, upscale_var, steps_var, seed_var, refiner_var, output_folder, label, last_prompt, last_ar, last_steps, last_upscale, last_seed, image_generated, last_generated_image_path
    root = tk.Tk()
    refiner_var = tk.StringVar(value='n')  # Now correctly initialize refiner_var as a global variable
    root.title("Image Viewer")

    output_folder = './OUTPUT'
    default_image = 'output_20231107-144208.jpg'
    script_directory = os.path.dirname(os.path.realpath(__file__))
    default_image_path = os.path.join(script_directory, default_image)
    last_generated_image_path = None

    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Define label variable for the image
    label = tk.Label(root)
    label.pack()

    # Display default image on startup if it exists
    if os.path.exists(default_image_path):
        update_image(default_image_path, False, is_default_image=True)
    else:
        first_image_displayed = False

    # User input fields and buttons
    # Prompt Input Frame
    prompt_frame = tk.Frame(root)
    prompt_frame.pack(fill='x', padx=5, pady=5)

    prompt_label = tk.Label(prompt_frame, text="P\nR\nO\nM\nP\nT")
    prompt_label.pack(side=tk.LEFT, padx=5)

    prompt_entry = tk.Text(prompt_frame, height=4, width=30)
    prompt_entry.pack(side=tk.LEFT, expand=True, fill='x', padx=(0, 10), pady=5)
    prompt_entry.bind("<Return>", on_enter_key)

    # Frame containing Seed, Refiner, and Steps Options
    seed_refiner_frame = tk.Frame(root)
    seed_refiner_frame.pack(fill='x', padx=(5, 5), pady=5)

     # Seed Input Frame
    seed_frame = tk.Frame(seed_refiner_frame)
    seed_frame.pack(side=tk.LEFT, padx=(10, 10), pady=5)
    seed_label = tk.Label(seed_frame, text="Seed:")
    seed_label.pack(side=tk.LEFT)
    seed_var = tk.StringVar()
    seed_entry = tk.Entry(seed_frame, textvariable=seed_var, width=10)
    seed_entry.pack(side=tk.LEFT)
    seed_entry.bind("<Return>", on_enter_key)  # Bind Enter key

    # Refiner Option Frame
    refiner_frame = tk.Frame(seed_refiner_frame)
    refiner_frame.pack(side=tk.LEFT, padx=(30, 10), pady=5)
    refiner_label = tk.Label(refiner_frame, text="Refiner:")
    refiner_label.pack(side=tk.LEFT)
    tk.Radiobutton(refiner_frame, text="Yes", variable=refiner_var, value='y').pack(side=tk.LEFT)
    tk.Radiobutton(refiner_frame, text="No", variable=refiner_var, value='n').pack(side=tk.LEFT)

    # Steps Frame
    steps_frame = tk.Frame(seed_refiner_frame)
    steps_frame.pack(side=tk.LEFT, padx=(35, 10))
    steps_label = tk.Label(steps_frame, text="Steps (default: 20):")
    steps_label.pack(side=tk.LEFT)
    steps_var = tk.StringVar()
    steps_entry = tk.Entry(steps_frame, textvariable=steps_var, width=4)
    steps_entry.pack(side=tk.LEFT)
    steps_entry.bind("<Return>", on_enter_key)  # Bind Enter key


    # Aspect Ratio Frame
    aspect_ratio_frame = tk.Frame(root)
    aspect_ratio_frame.pack(fill='x', padx=(70, 10))

    aspect_ratio_label = tk.Label(aspect_ratio_frame, text="Aspect Ratio:")
    aspect_ratio_label.pack(side=tk.LEFT)

    aspect_ratios = {'BOX': '1', 'WIDE': '2', 'TALL': '3', 'UHD': '4'}
    aspect_ratio_var = tk.StringVar(value='1')
    for text, value in aspect_ratios.items():
        tk.Radiobutton(aspect_ratio_frame, text=text, variable=aspect_ratio_var, value=value).pack(side=tk.LEFT)

    # Resolution (2x) Option Frame
    upscale_frame = tk.Frame(root)
    upscale_frame.pack(fill='x', padx=(70, 10))

    upscale_label = tk.Label(upscale_frame, text="Resolution (2x)")
    upscale_label.pack(side=tk.LEFT)

    upscale_var = tk.StringVar(value='n')
    tk.Radiobutton(upscale_frame, text="Yes", variable=upscale_var, value='y').pack(side=tk.LEFT)
    tk.Radiobutton(upscale_frame, text="No", variable=upscale_var, value='n').pack(side=tk.LEFT)

    upscale_info_label = tk.Label(upscale_frame, text="(Changes Seed Results)")
    upscale_info_label.pack(side=tk.LEFT)

    # Button Frame
    button_frame = tk.Frame(root)
    button_frame.pack(padx=5, pady=5)

    generate_button = tk.Button(button_frame, text="Generate Image", command=handle_user_input)
    generate_button.pack(side=tk.LEFT, padx=5, pady=5)

    copy_button = tk.Button(button_frame, text="Copy Image", command=copy_image_to_clipboard)
    copy_button.pack(side=tk.LEFT, padx=5, pady=5)

    redo_button = tk.Button(button_frame, text="Redo Image", command=redo_image_generation)
    redo_button.pack(side=tk.LEFT, padx=5, pady=5)

    # Right-click context menu
    right_click_menu = tk.Menu(root, tearoff=0)
    right_click_menu.add_command(label="Copy Image", command=copy_image_to_clipboard)

    label.bind("<Button-3>", lambda event: right_click_menu.post(event.x_root, event.y_root))

    root.mainloop()

if __name__ == "__main__":
    run_tkinter()