import torch
from PIL import Image
from PIL import ImageTk
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

def create_window():
    global root, label
    root = tk.Tk()
    root.title("Image Viewer")
    label = tk.Label(root)
    label.pack()

def update_image(filename):
    global img, root, label
    img = Image.open(filename)
    img = img.resize((int(img.width * 0.5), int(img.height * 0.5)), Image.BILINEAR)
    img = ImageTk.PhotoImage(img)
    label.configure(image=img)
    label.image = img  # Keep a reference to avoid garbage collection

while True:
    prompt = input("Prompt: ")
    ar = input("Aspect ratio:\n1. Square\n2. Widescreen\n3. Tall\n4. Ultra Widescreen\n")
    steps_input = input("Number of steps (default: 20, press Enter to use default): ")

    if ar not in ['1', '2', '3', '4']:
        print("Please enter a valid choice. 1, 2, 3, or 4")
    else:
        ar = int(ar)
        steps = 20 if steps_input == '' else int(steps_input)  # Use default if input is empty

        if ar == 1:
            width = 1024
            height = 1024
        elif ar == 2:
            width = 1344
            height = 768
        elif ar == 3:
            width = 896
            height = 1152
        elif ar == 4:
            width = 1536
            height = 640

        # Pass the steps parameter to the pipeline
        image = pipe(prompt=prompt, width=width, height=height, num_inference_steps=steps).images[0]

        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"output_{timestamp}.jpg"

        with io.BytesIO() as output_bytes:
            image.save(output_bytes, format="JPEG")
            image_data = output_bytes.getvalue()

        with open(filename, "wb") as file:
            file.write(image_data)

        # Create the window if it doesn't exist, otherwise update the image
        if not root:
            create_window()
        update_image(filename)

        # Update the window without blocking
        root.update_idletasks()
        root.update()
