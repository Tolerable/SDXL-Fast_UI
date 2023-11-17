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
import json

# Global variable declarations
img, label = None, None
refiner_var = None  # Initialize as None
last_prompt, last_ar, last_steps, last_upscale, last_seed, last_refiner = None, None, None, None, None, None
image_generated, last_generated_image_path = False, None
seed_entry, prompt_entry, aspect_ratio_var, upscale_var, steps_var, seed_var = None, None, None, None, None, None
root, output_folder = None, None
show_seed_var, show_refiner_var, show_steps_var, show_aspect_ratio_var, show_upscale_var = None, None, None, None, None


# Initialize the Stable Diffusion pipeline
pipe = StableDiffusionXLPipeline.from_pretrained("segmind/SSD-1B", torch_dtype=torch.float16, use_safetensors=True, variant="fp16")
pipe.to("cuda")

# Add global variables for UI elements that can be shown/hidden
seed_frame, refiner_frame, steps_frame, aspect_ratio_frame, upscale_frame = None, None, None, None, None


# Add the save and load settings functions
def save_settings(settings):
    with open('settings.json', 'w') as f:
        json.dump(settings, f)

def load_settings():
    try:
        with open('settings.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def update_image(filename, is_upscaled, is_default_image=False):
    global img, label
    img = Image.open(filename)
    resize_ratio = 0.5 if is_upscaled or is_default_image else 1.0
    img = img.resize((int(img.width * resize_ratio), int(img.height * resize_ratio)), Image.BILINEAR)
    img = ImageTk.PhotoImage(img)
    label.configure(image=img)
    label.image = img

def generate_image(prompt, width, height, steps, seed, use_refiner):
    print(f"Generating image with refiner: {'On' if use_refiner else 'Off'}")
    if seed is not None:
        response = pipe(prompt=prompt, width=width, height=height, num_inference_steps=steps, generator=torch.Generator("cuda").manual_seed(seed), use_refiner=use_refiner)
    else:
        response = pipe(prompt=prompt, width=width, height=height, num_inference_steps=steps, use_refiner=use_refiner)
    image = response.images[0]
    return image

def handle_user_input(event=None, new_generation=True):
    global last_prompt, last_ar, last_steps, last_upscale, last_seed, last_refiner, image_generated, last_generated_image_path
    
    if new_generation:
        prompt = prompt_entry.get("1.0", "end-1c").strip()
        if not prompt:
            return  # Exit if the prompt is empty

        # Update last_* variables with current settings
        last_prompt = prompt
        last_ar = aspect_ratio_var.get() or '1'
        last_upscale = upscale_var.get() == 'y'
        steps_input = steps_var.get()
        last_steps = int(steps_input) if steps_input.isdigit() else 20
        seed_input = seed_var.get()
        last_seed = int(seed_input) if seed_input.isdigit() else random.randint(0, 999999999999)
        last_refiner = refiner_var.get() if refiner_var is not None else 'n'

        # Set current settings based on UI input
        use_refiner = last_refiner == 'y'
    else:
        # Redo operation: Reuse the last used settings
        prompt = last_prompt
        use_refiner = last_refiner == 'y'
    
    ar = last_ar
    upscale = last_upscale
    steps = last_steps
    seed = last_seed

    # Debugging output
    print(f"Redo Generation with parameters: Seed={seed}, Refiner={'Yes' if use_refiner else 'No'}, Resolution 2x={'Yes' if upscale else 'No'}")


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

def load_settings():
    settings_file = 'settings.json'
    if os.path.exists(settings_file):
        with open(settings_file, 'r') as file:
            return json.load(file)
    return {}

def save_settings(settings):
    with open('settings.json', 'w') as file:
        json.dump(settings, file)

def toggle_element(element, is_shown):
    settings = load_settings()
    settings[element] = is_shown
    save_settings(settings)
    update_ui_elements()

def update_ui_elements():
    global seed_frame, refiner_frame, steps_frame, aspect_ratio_frame, upscale_frame

    # Check the state of each BooleanVar and update the UI elements
    if show_seed_var.get():
        seed_frame.pack(fill='x', padx=(10, 10), pady=5) if not seed_frame.winfo_viewable() else None
    else:
        seed_frame.pack_forget() if seed_frame.winfo_viewable() else None

    if show_refiner_var.get():
        refiner_frame.pack(side=tk.LEFT, padx=(30, 10), pady=5) if not refiner_frame.winfo_viewable() else None
    else:
        refiner_frame.pack_forget() if refiner_frame.winfo_viewable() else None

    if show_steps_var.get():
        steps_frame.pack(side=tk.LEFT, padx=(35, 10)) if not steps_frame.winfo_viewable() else None
    else:
        steps_frame.pack_forget() if steps_frame.winfo_viewable() else None

    if show_aspect_ratio_var.get():
        aspect_ratio_frame.pack(fill='x', padx=(70, 10)) if not aspect_ratio_frame.winfo_viewable() else None
    else:
        aspect_ratio_frame.pack_forget() if aspect_ratio_frame.winfo_viewable() else None

    if show_upscale_var.get():
        upscale_frame.pack(fill='x', padx=(70, 10)) if not upscale_frame.winfo_viewable() else None
    else:
        upscale_frame.pack_forget() if upscale_frame.winfo_viewable() else None
   
def toggle_all_elements():
    current_state = show_all_var.get()
    new_state = not current_state
    show_all_var.set(new_state)

    print(f"toggle_all_elements called: current_state={current_state}, new_state={new_state}")

    show_seed_var.set(new_state)
    show_refiner_var.set(new_state)
    show_steps_var.set(new_state)
    show_aspect_ratio_var.set(new_state)
    show_upscale_var.set(new_state)

    update_ui_elements()




def run_tkinter():
    global root, prompt_entry, aspect_ratio_var, upscale_var, steps_var, seed_var, refiner_var, output_folder, label, last_prompt, last_ar, last_steps, last_upscale, last_seed, image_generated, last_generated_image_path
    global seed_frame, refiner_frame, steps_frame, aspect_ratio_frame, upscale_frame, show_all_var, show_seed_var, show_refiner_var, show_steps_var, show_aspect_ratio_var, show_upscale_var

    root = tk.Tk()
    refiner_var = tk.StringVar(value='n')
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

    # Create a menu bar
    menu_bar = tk.Menu(root)
    root.config(menu=menu_bar)
    
    # Create an "Options" menu
    options_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Options", menu=options_menu)
    
    # Load settings and determine the initial state for show_all_var
    settings = load_settings()
    initial_state = all(settings.get(key, True) for key in ['show_seed', 'show_refiner', 'show_steps', 'show_aspect_ratio', 'show_upscale'])
    show_all_var = tk.BooleanVar(value=initial_state)

    # Add the "Show/Hide All" checkbutton to the options menu
    options_menu.add_checkbutton(label="Show/Hide All", onvalue=1, offvalue=0, variable=show_all_var, command=toggle_all_elements)

    # Checkboxes within the Options menu to toggle UI elements
    show_all_var = tk.BooleanVar(value=True)  # Default value can be True or False

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

    # Checkboxes within the Options menu to toggle UI elements
    show_seed_var = tk.BooleanVar(value=load_settings().get('show_seed', True))
    options_menu.add_checkbutton(label="Show Seed", onvalue=1, offvalue=0, variable=show_seed_var, command=lambda: toggle_element('show_seed', show_seed_var.get()))
    show_refiner_var = tk.BooleanVar(value=load_settings().get('show_refiner', True))
    options_menu.add_checkbutton(label="Show Refiner", onvalue=1, offvalue=0, variable=show_refiner_var, command=lambda: toggle_element('show_refiner', show_refiner_var.get()))
    show_steps_var = tk.BooleanVar(value=load_settings().get('show_steps', True))
    options_menu.add_checkbutton(label="Show Steps", onvalue=1, offvalue=0, variable=show_steps_var, command=lambda: toggle_element('show_steps', show_steps_var.get()))
    show_aspect_ratio_var = tk.BooleanVar(value=load_settings().get('show_aspect_ratio', True))
    options_menu.add_checkbutton(label="Show Aspect Ratio", onvalue=1, offvalue=0, variable=show_aspect_ratio_var, command=lambda: toggle_element('show_aspect_ratio', show_aspect_ratio_var.get()))
    show_upscale_var = tk.BooleanVar(value=load_settings().get('show_upscale', True))
    options_menu.add_checkbutton(label="Show Upscale", onvalue=1, offvalue=0, variable=show_upscale_var, command=lambda: toggle_element('show_upscale', show_upscale_var.get()))

    update_ui_elements()  # Apply the settings to the UI

    root.mainloop()

if __name__ == "__main__":
    run_tkinter()