import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, TclError
from PIL import Image
import io
import os
import requests
import re

class ImageCompressorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Compressor")
        self.root.geometry("600x500")
        self.root.configure(bg="#F4F4F4")
        self.output_folder = None

        # Styling variables
        self.bg_color = "#F4F4F4"
        self.accent_color = "#1F6AA5"
        self.hover_color = "#144875"
        self.text_color = "#333333"
        self.font_title = ("Helvetica", 16, "bold") if self.is_font_available("Helvetica") else ("Arial", 16, "bold")
        self.font_button = ("Helvetica", 12, "bold") if self.is_font_available("Helvetica") else ("Arial", 12, "bold")
        self.font_label = ("Helvetica", 10) if self.is_font_available("Helvetica") else ("Arial", 10)

        # Main frame
        self.main_frame = tk.Frame(self.root, bg=self.bg_color, padx=20, pady=20)
        self.main_frame.pack(fill="both", expand=True)

        # Title
        self.title_label = tk.Label(
            self.main_frame, text="Image Compressor", font=self.font_title,
            bg=self.bg_color, fg=self.text_color
        )
        self.title_label.pack(pady=10)

        # Select Images button
        self.select_button = tk.Button(
            self.main_frame, text="Select Images", font=self.font_button,
            bg=self.accent_color, fg="white", activebackground=self.hover_color,
            activeforeground="white", command=self.select_files, relief="flat", padx=10, pady=5
        )
        self.select_button.pack(pady=10)
        self.select_button.bind("<Enter>", lambda e: self.select_button.config(bg=self.hover_color))
        self.select_button.bind("<Leave>", lambda e: self.select_button.config(bg=self.accent_color))

        # Select Output Folder button
        self.output_button = tk.Button(
            self.main_frame, text="Select Output Folder", font=self.font_button,
            bg=self.accent_color, fg="white", activebackground=self.hover_color,
            activeforeground="white", command=self.select_output_folder, relief="flat", padx=10, pady=5
        )
        self.output_button.pack(pady=10)
        self.output_button.bind("<Enter>", lambda e: self.output_button.config(bg=self.hover_color))
        self.output_button.bind("<Leave>", lambda e: self.output_button.config(bg=self.accent_color))

        # Status label
        self.status_label = tk.Label(
            self.main_frame, text="Ready to select images", font=self.font_label,
            bg=self.bg_color, fg=self.text_color, wraplength=500
        )
        self.status_label.pack(pady=10)

    def is_font_available(self, font_name):
        try:
            tkfont.Font(family=font_name)
            return True
        except TclError:
            return False

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder = folder
            self.status_label.config(text=f"Output folder selected: {folder}")
        else:
            self.status_label.config(text="No output folder selected")

    def compress_image(self, image, output_path, max_size=102400):
        # Check initial size
        buffer = io.BytesIO()
        image.save(buffer, format=image.format if image.format in ['JPEG', 'PNG'] else 'JPEG')
        if buffer.tell() <= max_size:
            image.save(output_path, format=image.format if image.format in ['JPEG', 'PNG'] else 'JPEG')
            return output_path, buffer.tell()

        format = image.format if image.format in ['JPEG', 'PNG'] else 'JPEG'

        # Try original format compression
        if format == 'JPEG':
            for quality in range(95, 9, -5):
                buffer = io.BytesIO()
                image.save(buffer, format='JPEG', quality=quality)
                size = buffer.tell()
                if size <= max_size:
                    image.save(output_path, format='JPEG', quality=quality)
                    return output_path, size
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
            if 'resized_image' in locals() and current_width > 0 and current_height > 0:
                resized_image.save(output_path, format='PNG', optimize=True)
            else:
                palette_image.save(output_path, format='PNG', optimize=True)
        else:
            image.save(output_path, format='JPEG')

        compressed_size = os.path.getsize(output_path)
        if compressed_size <= max_size:
            return output_path, compressed_size
        else:
            webp_output_path = os.path.splitext(output_path)[0] + '.webp'
            for webp_quality in range(100, 9, -10):
                buffer = io.BytesIO()
                image.save(buffer, format='WEBP', quality=webp_quality, lossless=False)
                webp_size = buffer.tell()
                if webp_size <= max_size:
                    image.save(webp_output_path, format='WEBP', quality=webp_quality, lossless=False)
                    return webp_output_path, webp_size
            image.save(webp_output_path, format='WEBP', quality=10, lossless=False)
            return webp_output_path, os.path.getsize(webp_output_path)

    def select_files(self):
        # Create a new window for URL input and name input
        url_window = tk.Toplevel(self.root)
        url_window.title("Enter Image URLs and Names")
        url_window.geometry("800x400")
        url_window.configure(bg=self.bg_color)

        # Main frame for the new window
        url_main_frame = tk.Frame(url_window, bg=self.bg_color, padx=20, pady=20)
        url_main_frame.pack(fill="both", expand=True)

        # Two-column layout
        left_frame = tk.Frame(url_main_frame, bg=self.bg_color)
        left_frame.pack(side="left", fill="both", expand=True, padx=10)

        right_frame = tk.Frame(url_main_frame, bg=self.bg_color)
        right_frame.pack(side="right", fill="both", expand=True, padx=10)

        # Left column: URL input
        url_label = tk.Label(
            left_frame, text="Enter Image URLs:", font=self.font_label,
            bg=self.bg_color, fg=self.text_color
        )
        url_label.pack(anchor="w")

        # Canvas for scrollable URL entries
        url_canvas = tk.Canvas(left_frame, bg=self.bg_color, highlightthickness=0)
        url_scrollbar = tk.Scrollbar(left_frame, orient="vertical", command=url_canvas.yview)
        url_scrollable_frame = tk.Frame(url_canvas, bg=self.bg_color)

        url_scrollable_frame.bind(
            "<Configure>",
            lambda e: url_canvas.configure(scrollregion=url_canvas.bbox("all"))
        )

        url_canvas.create_window((0, 0), window=url_scrollable_frame, anchor="nw")
        url_canvas.configure(yscrollcommand=url_scrollbar.set)

        url_canvas.pack(side="left", fill="both", expand=True)
        url_scrollbar.pack(side="right", fill="y")

        # Right column: Name input
        name_label = tk.Label(
            right_frame, text="Compressed Image Names:", font=self.font_label,
            bg=self.bg_color, fg=self.text_color
        )
        name_label.pack(anchor="w")

        # Canvas for scrollable name entries
        name_canvas = tk.Canvas(right_frame, bg=self.bg_color, highlightthickness=0)
        name_scrollbar = tk.Scrollbar(right_frame, orient="vertical", command=name_canvas.yview)
        name_scrollable_frame = tk.Frame(name_canvas, bg=self.bg_color)

        name_scrollable_frame.bind(
            "<Configure>",
            lambda e: name_canvas.configure(scrollregion=name_canvas.bbox("all"))
        )

        name_canvas.create_window((0, 0), window=name_scrollable_frame, anchor="nw")
        name_canvas.configure(yscrollcommand=name_scrollbar.set)

        name_canvas.pack(side="left", fill="both", expand=True)
        name_scrollbar.pack(side="right", fill="y")

        # Lists to store URL and name entries
        self.url_entries = []
        self.name_entries = []

        # Add initial URL and name entry pair
        self.add_url_entry(url_scrollable_frame, name_scrollable_frame, 1)

        # Add URL button
        add_url_button = tk.Button(
            left_frame, text="Add URL", font=self.font_button,
            bg=self.accent_color, fg="white", activebackground=self.hover_color,
            activeforeground="white", command=lambda: self.add_url_entry(url_scrollable_frame, name_scrollable_frame, len(self.url_entries) + 1), relief="flat", padx=10, pady=5
        )
        add_url_button.pack(pady=5)
        add_url_button.bind("<Enter>", lambda e: add_url_button.config(bg=self.hover_color))
        add_url_button.bind("<Leave>", lambda e: add_url_button.config(bg=self.accent_color))

        # Download and Compress button
        compress_button = tk.Button(
            left_frame, text="Download and Compress", font=self.font_button,
            bg=self.accent_color, fg="white", activebackground=self.hover_color,
            activeforeground="white", command=lambda: self.download_and_compress(url_window, self.url_entries, self.name_entries), relief="flat", padx=10, pady=5
        )
        compress_button.pack(pady=5)
        compress_button.bind("<Enter>", lambda e: compress_button.config(bg=self.hover_color))
        compress_button.bind("<Leave>", lambda e: compress_button.config(bg=self.accent_color))

    def add_url_entry(self, url_frame, name_frame, index):
        # URL entry
        url_entry = tk.Entry(url_frame, font=self.font_label, width=50)
        url_entry.pack(pady=5)
        self.url_entries.append(url_entry)

        # Name entry with default placeholder
        name_entry = tk.Entry(name_frame, font=self.font_label, width=50)
        name_entry.insert(0, f"image_{index}")
        name_entry.pack(pady=5)
        self.name_entries.append(name_entry)

    def download_and_compress(self, url_window, url_entries, name_entries):
        if not self.output_folder:
            self.output_folder = os.getcwd()
            self.status_label.config(text=f"No output folder selected; using {self.output_folder}")

        total_urls = len([entry.get() for entry in url_entries if entry.get().strip()])
        if total_urls == 0:
            self.status_label.config(text="No URLs provided")
            return

        # Track used filenames to avoid conflicts
        used_filenames = set()

        for index, (url_entry, name_entry) in enumerate(zip(url_entries, name_entries), 1):
            url = url_entry.get().strip()
            if not url:
                continue

            self.status_label.config(text=f"Processing {index} of {total_urls} images...")
            self.root.update()

            try:
                # Download image
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                content_type = response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    self.status_label.config(text=f"Error: {url} is not an image")
                    continue

                # Open image
                image = Image.open(io.BytesIO(response.content))
                if image.format not in ['JPEG', 'PNG', 'GIF', 'BMP']:
                    image = image.convert('RGB')

                # Get and sanitize custom name
                custom_name = name_entry.get().strip()
                if not custom_name:
                    custom_name = f"downloaded_image_{index}"

                # Remove invalid filename characters
                custom_name = re.sub(r'[<>:"/\\|?*]', '', custom_name)
                if not custom_name:
                    custom_name = f"downloaded_image_{index}"

                # Determine extension
                ext = '.jpg' if image.format == 'JPEG' else '.png' if image.format == 'PNG' else '.jpg'
                base_name = custom_name
                output_filename = f"{base_name}{ext}"
                output_path = os.path.join(self.output_folder, output_filename)

                # Handle filename conflicts
                counter = 1
                while output_filename.lower() in used_filenames or os.path.exists(output_path):
                    output_filename = f"{base_name}{counter}{ext}"
                    output_path = os.path.join(self.output_folder, output_filename)
                    counter += 1
                used_filenames.add(output_filename.lower())

                # Compress image
                final_path, size = self.compress_image(image, output_path)
                self.status_label.config(text=f"Compressed {os.path.basename(final_path)} ({size} bytes)")

            except (requests.RequestException, IOError) as e:
                self.status_label.config(text=f"Error processing {url}: {str(e)}")
                continue

        self.status_label.config(text="Compression complete!")
        url_window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageCompressorApp(root)
    root.mainloop()