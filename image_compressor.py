import tkinter as tk
from tkinter import filedialog
from PIL import Image
import io
import os

def compress_image(input_path, output_path, max_size=102400):
    if os.path.getsize(input_path) <= max_size:
        with open(input_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
            f_out.write(f_in.read())
        return output_path, os.path.getsize(output_path)
    
    image = Image.open(input_path)
    format = image.format
    
    # Try original format compression
    if format == 'JPEG':
        for quality in range(95, 9, -5):  # from 95 to 10, step -5
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=quality)
            size = buffer.tell()
            if size <= max_size:
                image.save(output_path, format='JPEG', quality=quality)
                return output_path, size
        # Save with quality=10
        image.save(output_path, format='JPEG', quality=10)
    elif format == 'PNG':
        palette_image = image.convert('P', palette=Image.ADAPTIVE, colors=256)
        buffer = io.BytesIO()
        palette_image.save(buffer, format='PNG', optimize=True)
        size = buffer.tell()
        if size <= max_size:
            palette_image.save(output_path, format='PNG', optimize=True)
            return output_path, size
        factor = 1
        while True:
            current_width = int(palette_image.width / factor)
            current_height = int(palette_image.height / factor)
            if current_width < 1 or current_height < 1:
                break
            resized_image = palette_image.resize((current_width, current_height), Image.LANCZOS)
            buffer = io.BytesIO()
            resized_image.save(buffer, format='PNG', optimize=True)
            size = buffer.tell()
            if size <= max_size:
                resized_image.save(output_path, format='PNG', optimize=True)
                return output_path, size
            factor *= 2
        # Save the last resized image or palette_image
        if 'resized_image' in locals() and current_width > 0 and current_height > 0:
            resized_image.save(output_path, format='PNG', optimize=True)
        else:
            palette_image.save(output_path, format='PNG', optimize=True)
    else:
        image.save(output_path, format=format)
    
    # After trying original format, check size
    compressed_size = os.path.getsize(output_path)
    if compressed_size <= max_size:
        return output_path, compressed_size
    else:
        # Try WebP
        webp_output_path = os.path.splitext(output_path)[0] + '.webp'
        for webp_quality in range(100, 9, -10):  # from 100 to 10, step -10
            buffer = io.BytesIO()
            image.save(buffer, format='WEBP', quality=webp_quality, lossless=False)
            webp_size = buffer.tell()
            if webp_size <= max_size:
                image.save(webp_output_path, format='WEBP', quality=webp_quality, lossless=False)
                return webp_output_path, webp_size
        # Save with webp_quality=10
        image.save(webp_output_path, format='WEBP', quality=10, lossless=False)
        return webp_output_path, os.path.getsize(webp_output_path)

def select_files():
    file_paths = filedialog.askopenfilenames(filetypes=[("Image files", ("*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp"))])
    for file_path in file_paths:
        base, ext = os.path.splitext(file_path)
        output_path = base + "_compressed" + ext
        final_path, size = compress_image(file_path, output_path)
        print(f"Compressed {file_path} to {final_path} with size {size} bytes")

# Create the main window
root = tk.Tk()
root.title("Image Compressor")

# Add a button to select files
button = tk.Button(root, text="Select Images", command=select_files)
button.pack(pady=20)

# Run the application
root.mainloop()