<p align="center">
  <img src="https://github.com/Tolerable/SDXL-Fast_UI/blob/main/output_20231107-144208.jpg" width="400" height="400" alt="Generated Image">
</p>

# SDXL-Fast_UI: Accelerated Text-to-Image Generation with SDXL

## Overview

SDXL-Fast_UI enhances the original SDXL-Fast script, offering a user-friendly interface and additional features for the StableDiffusionXLPipeline. This Python script accelerates text-to-image generation, producing high-quality 1024x1024 images in mere seconds. Optimized for speed, it can generate images in about 15 seconds on an RTX 3060 Ti, with even faster results on higher-end GPUs.

---

## Getting Started

1. Clone the repository to your local machine using Git:
```bash
git clone https://github.com/Jeffman112/SDXL-Fast.git
```
2. Navigate to the project directory:
```bash
cd SDXL-Fast
```
3. Install the required dependencies using pip and the provided requirements.txt file:
```bash
pip install -r requirements.txt
```

## Enhanced Features

Interactive GUI: Provides a Tkinter-based graphical user interface for easier interaction.
Aspect Ratio Selection: Users can choose from various aspect ratios (Square, Widescreen, Tall, Ultra Widescreen) for image generation.
Upscaling Option: Allows for generating higher resolution images.
Clipboard Integration: Enables copying of generated images directly to the clipboard.
Multiline Prompt Input: Supports multiline text input for more detailed prompts.

## Usage
Once you've completed the setup, you can start generating images from text prompts using SDXL-Fast. Here's how:

Run the script using the following command:
```bash
python main.py
```
Enter a text prompt and select aspect ratio using the GUI.

An image based on your prompt will be generated and displayed.

You can copy the generated image to the clipboard for easy sharing.

After providing the prompt, an image will be generated.

## Example Outputs
<p align="center">
  <img src="https://github.com/Jeffman112/SDXL-Fast/assets/123284838/ddf57c26-49a4-4789-ad85-357b4dab8da9" alt="dragonborn" width="300">
  <img src="https://github.com/Jeffman112/SDXL-Fast/assets/123284838/a0f6b0b8-3257-4aa1-b3c2-a4bf3b70ad35" alt="red panda" width="300">
  <img src="https://github.com/Jeffman112/SDXL-Fast/assets/123284838/73153707-892c-4222-96c7-dfd5030e8a85" alt="angel" width="300">
</p>


### Credits
This script uses the StableDiffusionXLPipeline from the Segmind organization.
The underlying models are powered by PyTorch and Hugging Face's Transformers library.

If you encounter any issues or have questions, please don't hesitate to reach out to me in the Issue Tracker.
