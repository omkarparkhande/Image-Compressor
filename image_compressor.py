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
        self.debug = True  # Enable debug logging

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

        # Select Images via URLs button (initially disabled)
        self.select_url_button = tk.Button(
            self.main_frame, text="Select Images via URLs", font=self.font_button,
            bg=self.accent_color, fg="white", activebackground=self.hover_color,
            activeforeground="white", disabledforeground="white", command=self.select_files,
            relief="flat", padx=10, pady=5, state="disabled"
        )
        self.select_url_button.pack(pady=10)
        self.select_url_button.bind("<Enter>", lambda e: self.select_url_button.config(bg=self.hover_color) if self.select_url_button["state"] == "normal" else None)
        self.select_url_button.bind("<Leave>", lambda e: self.select_url_button.config(bg=self.accent_color) if self.select_url_button["state"] == "normal" else None)

        # Select Local Images button (initially disabled)
        self.select_local_button = tk.Button(
            self.main_frame, text="Select Local Images", font=self.font_button,
            bg=self.accent_color, fg="white", activebackground=self.hover_color,
            activeforeground="white", disabledforeground="white", command=self.select_local_files,
            relief="flat", padx=10, pady=5, state="disabled"
        )
        self.select_local_button.pack(pady=10)
        self.select_local_button.bind("<Enter>", lambda e: self.select_local_button.config(bg=self.hover_color) if self.select_local_button["state"] == "normal" else None)
        self.select_local_button.bind("<Leave>", lambda e: self.select_local_button.config(bg=self.accent_color) if self.select_local_button["state"] == "normal" else None)

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
            self.main_frame, text="Please select an output folder to begin", font=self.font_label,
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
            try:
                folder = os.path.abspath(folder)  # Ensure absolute path
                if not os.path.exists(folder):
                    os.makedirs(folder, exist_ok=True)
                if not os.access(folder, os.W_OK):
                    self.status_label.config(text="Error: Selected folder is not writable")
                    return
                self.output_folder = folder
                self.status_label.config(text=f"Output folder selected: {folder}")
                if self.debug:
                    print(f"Output folder set to: {self.output_folder}")
                # Enable image selection buttons
                self.select_url_button.config(state="normal")
                self.select_local_button.config(state="normal")
            except Exception as e:
                self.status_label.config(text=f"Error setting output folder: {str(e)}")
        else:
            self.status_label.config(text="No output folder selected")

    def compress_image(self, image, output_path, max_size=100352):  # 98 KB
        try:
            output_path = os.path.abspath(output_path)  # Ensure absolute path
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            if self.debug:
                print(f"Attempting to save to: {output_path}")

            # Pre-resize the image to a maximum dimension of 1920 pixels
            max_dim = 1920
            if image.width > max_dim or image.height > max_dim:
                ratio = min(max_dim / image.width, max_dim / image.height)
                new_width = int(image.width * ratio)
                new_height = int(image.height * ratio)
                image = image.resize((new_width, new_height), Image.LANCZOS)

            # Determine the format to save as
            saved_format = image.format if image.format in ['JPEG', 'PNG'] else 'JPEG'
            if saved_format == 'JPEG' and image.mode != 'RGB':
                image = image.convert('RGB')
            final_quality = None  # For JPEG quality feedback

            # Check initial size
            buffer = io.BytesIO()
            if saved_format == 'JPEG':
                image.save(buffer, format='JPEG', quality=95, optimize=True, progressive=True)
            else:  # PNG
                image.save(buffer, format='PNG', optimize=True)

            if buffer.tell() <= max_size:
                if saved_format == 'JPEG':
                    image.save(output_path, format='JPEG', quality=95, optimize=True, progressive=True)
                    final_quality = 95
                else:
                    image.save(output_path, format='PNG', optimize=True)
            else:
                # Compress based on format
                if saved_format == 'JPEG':
                    for quality in range(95, 29, -5):
                        buffer = io.BytesIO()
                        image.save(buffer, format='JPEG', quality=quality, optimize=True, progressive=True)
                        size = buffer.tell()
                        if size <= max_size:
                            image.save(output_path, format='JPEG', quality=quality, optimize=True, progressive=True)
                            final_quality = quality
                            break
                    else:
                        image.save(output_path, format='JPEG', quality=30, optimize=True, progressive=True)
                        compressed_size = os.path.getsize(output_path)
                        if compressed_size > max_size:
                            raise IOError(f"Could not compress JPEG image to {max_size} bytes (final size: {compressed_size} bytes) at minimum quality 30")
                        final_quality = 30
                else:  # PNG
                    # Convert to 128-color palette
                    palette_image = image.convert('P', palette=Image.ADAPTIVE, colors=128)
                    buffer = io.BytesIO()
                    palette_image.save(buffer, format='PNG', optimize=True)
                    size = buffer.tell()
                    if size <= max_size:
                        palette_image.save(output_path, format='PNG', optimize=True)
                    else:
                        # Resize progressively
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
                                break
                            factor *= 2
                        else:
                            # If still too large, save the smallest version and check size
                            if 'resized_image' in locals() and current_width > 0 and current_height > 0:
                                resized_image.save(output_path, format='PNG', optimize=True)
                            else:
                                palette_image.save(output_path, format='PNG', optimize=True)
                            compressed_size = os.path.getsize(output_path)
                            if compressed_size > max_size:
                                raise IOError(f"Could not compress PNG image to {max_size} bytes (final size: {compressed_size} bytes)")

            # Check if file exists after saving
            if not os.path.exists(output_path):
                raise IOError(f"Failed to save file: {output_path}")

            compressed_size = os.path.getsize(output_path)
            final_path = output_path

            # Validate the saved image
            try:
                with Image.open(final_path) as test_image:
                    test_image.verify()  # Verify image integrity
            except Exception as e:
                raise IOError(f"Saved image is corrupted: {final_path}, Error: {str(e)}")

            return final_path, compressed_size, final_quality

        except (PermissionError, OSError) as e:
            raise IOError(f"Error saving image to {output_path}: {str(e)}")

    def process_images(self, images, names, source_description="image"):
        try:
            if not os.path.exists(self.output_folder):
                os.makedirs(self.output_folder, exist_ok=True)
            if not os.access(self.output_folder, os.W_OK):
                self.status_label.config(text=f"Error: Output folder {self.output_folder} is not writable")
                return
        except Exception as e:
            self.status_label.config(text=f"Error accessing output folder: {str(e)}")
            return

        if len(images) != len(names):
            self.status_label.config(text="Error: Number of images and names must match")
            return

        total_images = len(images)
        used_filenames = set()

        for index, (image, custom_name) in enumerate(zip(images, names), 1):
            self.status_label.config(text=f"Processing {index} of {total_images} {source_description}s")
            self.root.update()

            try:
                if not custom_name:
                    custom_name = f"image_{index}"
                custom_name = re.sub(r'[<>:"/\\|?*]', '', custom_name)
                if not custom_name:
                    custom_name = f"image_{index}"

                # Determine extension based on image format
                ext = '.jpg' if image.format == 'JPEG' else '.png' if image.format == 'PNG' else '.jpg'
                base_name = custom_name
                output_filename = f"{base_name}_compressed{ext}"
                output_path = os.path.join(self.output_folder, output_filename)

                counter = 1
                while output_filename.lower() in used_filenames or os.path.exists(output_path):
                    output_filename = f"{base_name}_compressed_{counter}{ext}"
                    output_path = os.path.join(self.output_folder, output_filename)
                    counter += 1
                used_filenames.add(output_filename.lower())

                if self.debug:
                    print(f"Saving {output_filename} to: {output_path}")

                final_path, size, final_quality = self.compress_image(image, output_path)
                if os.path.exists(final_path):
                    status_message = f"Compressed {os.path.basename(final_path)} ({size} bytes) to {final_path}"
                    if final_quality is not None and final_quality < 50:  # Only for JPEGs
                        status_message += f"\nWarning: Low quality ({final_quality}) used, may appear degraded"
                    self.status_label.config(text=status_message)
                    if self.debug:
                        print(f"Success: File saved to {final_path}" + (f" with quality {final_quality}" if final_quality is not None else ""))
                else:
                    self.status_label.config(text=f"Error: Failed to save {os.path.basename(final_path)} to {final_path}")
                    if self.debug:
                        print(f"Failure: File not found at {final_path}")
                    continue

            except (IOError, Exception) as e:
                self.status_label.config(text=f"Error processing {source_description} {index}: {str(e)}")
                if self.debug:
                    print(f"Error: {str(e)}")
                continue

        self.status_label.config(text="Compression complete!")

    def select_files(self):
        url_window = tk.Toplevel(self.root)
        url_window.title("Enter Image URLs and Names")
        url_window.geometry("800x400")
        url_window.configure(bg=self.bg_color)

        url_main_frame = tk.Frame(url_window, bg=self.bg_color, padx=20, pady=20)
        url_main_frame.pack(fill="both", expand=True)

        left_frame = tk.Frame(url_main_frame, bg=self.bg_color)
        left_frame.pack(side="left", fill="both", expand=True, padx=10)

        right_frame = tk.Frame(url_main_frame, bg=self.bg_color)
        right_frame.pack(side="right", fill="both", expand=True, padx=10)

        url_label = tk.Label(
            left_frame, text="Enter Image URLs (one per line):", font=self.font_label,
            bg=self.bg_color, fg=self.text_color
        )
        url_label.pack(anchor="w")

        url_text_frame = tk.Frame(left_frame, bg=self.bg_color)
        url_text_frame.pack(fill="both", expand=True)

        url_scrollbar = tk.Scrollbar(url_text_frame, orient="vertical")
        url_scrollbar.pack(side="right", fill="y")

        url_text = tk.Text(
            url_text_frame, font=self.font_label, width=50, height=15, bg="white",
            fg=self.text_color, yscrollcommand=url_scrollbar.set
        )
        url_text.pack(side="left", fill="both", expand=True)
        url_scrollbar.config(command=url_text.yview)

        name_label = tk.Label(
            right_frame, text="Compressed Image Names (one per line):\n(Leave blank to use default names)", font=self.font_label,
            bg=self.bg_color, fg=self.text_color
        )
        name_label.pack(anchor="w")

        name_text_frame = tk.Frame(right_frame, bg=self.bg_color)
        name_text_frame.pack(fill="both", expand=True)

        name_scrollbar = tk.Scrollbar(name_text_frame, orient="vertical")
        name_scrollbar.pack(side="right", fill="y")

        name_text = tk.Text(
            name_text_frame, font=self.font_label, width=50, height=15, bg="white",
            fg=self.text_color, yscrollcommand=name_scrollbar.set
        )
        name_text.pack(side="left", fill="both", expand=True)
        name_scrollbar.config(command=name_text.yview)

        compress_button = tk.Button(
            left_frame, text="Download and Compress", font=self.font_button,
            bg=self.accent_color, fg="white", activebackground=self.hover_color,
            activeforeground="white", command=lambda: self.download_and_compress(url_window, url_text, name_text), relief="flat", padx=10, pady=5
        )
        compress_button.pack(pady=5)
        compress_button.bind("<Enter>", lambda e: compress_button.config(bg=self.hover_color))
        compress_button.bind("<Leave>", lambda e: compress_button.config(bg=self.accent_color))

    def select_local_files(self):
        filetypes = (
            ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"),
            ("All files", "*.*")
        )
        files = filedialog.askopenfilenames(
            title="Select Local Images",
            filetypes=filetypes
        )

        if not files:
            self.status_label.config(text="No local images selected")
            return

        local_window = tk.Toplevel(self.root)
        local_window.title("Enter Names for Local Images")
        local_window.geometry("800x400")
        local_window.configure(bg=self.bg_color)

        local_main_frame = tk.Frame(local_window, bg=self.bg_color, padx=20, pady=20)
        local_main_frame.pack(fill="both", expand=True)

        left_frame = tk.Frame(local_main_frame, bg=self.bg_color)
        left_frame.pack(side="left", fill="both", expand=True, padx=10)

        right_frame = tk.Frame(local_main_frame, bg=self.bg_color)
        right_frame.pack(side="right", fill="both", expand=True, padx=10)

        files_label = tk.Label(
            left_frame, text="Selected Image Files:", font=self.font_label,
            bg=self.bg_color, fg=self.text_color
        )
        files_label.pack(anchor="w")

        files_text_frame = tk.Frame(left_frame, bg=self.bg_color)
        files_text_frame.pack(fill="both", expand=True)

        files_scrollbar = tk.Scrollbar(files_text_frame, orient="vertical")
        files_scrollbar.pack(side="right", fill="y")

        files_text = tk.Text(
            files_text_frame, font=self.font_label, width=50, height=15, bg="white",
            fg=self.text_color, yscrollcommand=files_scrollbar.set
        )
        files_text.pack(side="left", fill="both", expand=True)
        files_scrollbar.config(command=files_text.yview)

        for file in files:
            files_text.insert(tk.END, f"{file}\n")
        files_text.config(state="disabled")

        name_label = tk.Label(
            right_frame, text="Compressed Image Names (one per line):\n(Defaults to file names if blank)", font=self.font_label,
            bg=self.bg_color, fg=self.text_color
        )
        name_label.pack(anchor="w")

        name_text_frame = tk.Frame(right_frame, bg=self.bg_color)
        name_text_frame.pack(fill="both", expand=True)

        name_scrollbar = tk.Scrollbar(name_text_frame, orient="vertical")
        name_scrollbar.pack(side="right", fill="y")

        name_text = tk.Text(
            name_text_frame, font=self.font_label, width=50, height=15, bg="white",
            fg=self.text_color, yscrollcommand=name_scrollbar.set
        )
        name_text.pack(side="left", fill="both", expand=True)
        name_scrollbar.config(command=name_text.yview)

        for file in files:
            default_name = os.path.splitext(os.path.basename(file))[0]
            name_text.insert(tk.END, f"{default_name}\n")

        compress_button = tk.Button(
            left_frame, text="Compress Local Images", font=self.font_button,
            bg=self.accent_color, fg="white", activebackground=self.hover_color,
            activeforeground="white", command=lambda: self.compress_local_files(local_window, files, name_text), relief="flat", padx=10, pady=5
        )
        compress_button.pack(pady=5)
        compress_button.bind("<Enter>", lambda e: compress_button.config(bg=self.hover_color))
        compress_button.bind("<Leave>", lambda e: compress_button.config(bg=self.accent_color))

    def download_and_compress(self, url_window, url_text, name_text):
        urls = [url.strip() for url in url_text.get("1.0", tk.END).splitlines() if url.strip()]
        names = [name.strip() for name in name_text.get("1.0", tk.END).splitlines() if name.strip()]

        if not urls:
            self.status_label.config(text="No URLs provided")
            url_window.destroy()
            return

        while len(names) < len(urls):
            names.append("")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Accept': 'image/jpeg,image/png,image/webp,image/*,*/*;q=0.8'
        }
        fallback_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15',
            'Accept': 'image/*,*/*;q=0.8'
        }

        images = []
        valid_names = []
        total_urls = len(urls)

        for index, (url, name) in enumerate(zip(urls, names), 1):
            self.status_label.config(text=f"Downloading {index} of {total_urls} images: {url}")
            self.root.update()

            try:
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                except requests.HTTPError as e:
                    if response.status_code == 406:
                        if self.debug:
                            print(f"406 Error for {url}, retrying with fallback headers: {response.text[:100]}...")
                        response = requests.get(url, headers=fallback_headers, timeout=10)
                        response.raise_for_status()

                content_type = response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    self.status_label.config(text=f"Error: {url} is not an image")
                    if self.debug:
                        print(f"Invalid content-type: {content_type}")
                    continue

                image = Image.open(io.BytesIO(response.content))
                if image.format not in ['JPEG', 'PNG', 'GIF', 'BMP']:
                    image = image.convert('RGB')
                images.append(image)
                valid_names.append(name)

            except requests.HTTPError as e:
                self.status_label.config(text=f"Error: 406 Client Error for {url}. Server may block automated requests.")
                if self.debug:
                    print(f"HTTP Error: {str(e)}, Response: {response.text[:100]}...")
                continue
            except (requests.RequestException, IOError) as e:
                self.status_label.config(text=f"Error downloading {url}: {str(e)}")
                if self.debug:
                    print(f"Error: {str(e)}")
                continue

        if images:
            self.process_images(images, valid_names, source_description="image from URL")
        else:
            self.status_label.config(text="No valid images to process")

        url_window.destroy()

    def compress_local_files(self, local_window, file_paths, name_text):
        names = [name.strip() for name in name_text.get("1.0", tk.END).splitlines() if name.strip()]
        images = []
        valid_names = []

        while len(names) < len(file_paths):
            names.append("")

        for file_path, name in zip(file_paths, names):
            try:
                ext = os.path.splitext(file_path)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    self.status_label.config(text=f"Skipping {file_path}: Unsupported file format")
                    if self.debug:
                        print(f"Unsupported format: {file_path}")
                    continue

                image = Image.open(file_path)
                if image.format not in ['JPEG', 'PNG', 'GIF', 'BMP']:
                    image = image.convert('RGB')
                images.append(image)
                valid_names.append(name)

            except (IOError, Exception) as e:
                self.status_label.config(text=f"Error loading {file_path}: {str(e)}")
                if self.debug:
                    print(f"Error loading local file {file_path}: {str(e)}")
                continue

        if images:
            self.process_images(images, valid_names, source_description="local image")
        else:
            self.status_label.config(text="No valid local images to process")

        local_window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageCompressorApp(root)
    root.mainloop()