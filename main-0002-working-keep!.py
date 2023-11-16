import torch
from PIL import Image
from PIL import ImageTk  # Add this import statement
import io
import os
from diffusers import StableDiffusionXLPipeline
import datetime
import tkinter as tk

# Initialize the Stable Diffusion pipeline
pipe = StableDiffusionXLPipeline.from_pretrained("segmind/SSD-1B", torch_dtype=torch.float16, use_safetensors=True, variant="fp16")
pipe.to("cuda")

while True:
    prompt = input("Prompt: ")
    ar = input("Aspect ratio:\n1. Square\n2. Widescreen\n3. Tall\n4. Ultra Widescreen\n")
    if ar not in ['1', '2', '3', '4']:
        print("Please enter a valid choice. 1, 2, 3, or 4")
    else:
        ar = int(ar)

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
        image = pipe(prompt=prompt, width=width, height=height).images[0]

        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"output_{timestamp}.jpg"

        with io.BytesIO() as output_bytes:
            image.save(output_bytes, format="JPEG")
            image_data = output_bytes.getvalue()

        with open(filename, "wb") as file:
            file.write(image_data)

        # Open the image using tkinter at 50% size
        root = tk.Tk()
        root.title("Image Viewer")
        img = Image.open(filename)
        img = img.resize((int(img.width * 0.5), int(img.height * 0.5)), Image.BILINEAR)  # Use BILINEAR for resizing
        img = ImageTk.PhotoImage(img)
        label = tk.Label(root, image=img)
        label.pack()
        root.mainloop()
