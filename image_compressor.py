import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, TclError
from PIL import Image
import io
import os

class ImageCompressorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Compressor")
        self.root.geometry("600x500")
        self.root.configure(bg="#F4F4F4")

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

        # Status label
        self.status_label = tk.Label(
            self.main_frame, text="Ready to select images", font=self.font_label,
            bg=self.bg_color, fg=self.text_color, wraplength=500
        )
        self.status_label.pack(pady=10)

        # File listbox with scrollbar
        self.listbox_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        self.listbox_frame.pack(fill="both", expand=True, pady=10)

        self.file_listbox = tk.Listbox(
            self.listbox_frame, font=self.font_label, bg="white", fg=self.text_color,
            selectbackground=self.accent_color, selectforeground="white", height=15
        )
        self.file_listbox.pack(side="left", fill="both", expand=True)

        self.scrollbar = tk.Scrollbar(self.listbox_frame, orient="vertical")
        self.scrollbar.pack(side="right", fill="y")
        self.file_listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.file_listbox.yview)

    def is_font_available(self, font_name):
        try:
            tkfont.Font(family=font_name)
            return True
        except TclError:
            return False

    def compress_image(self, input_path, output_path, max_size=102400):
        if os.path.getsize(input_path) <= max_size:
            with open(input_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
                f_out.write(f_in.read())
            return output_path, os.path.getsize(input_path)
        
        image = Image.open(input_path)
        format = image.format
        
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
            image.save(output_path, format=format)
        
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
        file_paths = filedialog.askopenfilenames(filetypes=[("Image files", ("*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp"))])
        if not file_paths:
            return

        self.file_listbox.delete(0, tk.END)
        for file_path in file_paths:
            self.file_listbox.insert(tk.END, f"Selected: {os.path.basename(file_path)}")
        
        total_files = len(file_paths)
        for index, file_path in enumerate(file_paths, 1):
            self.status_label.config(text=f"Processing {index} of {total_files} images...")
            self.root.update()
            base, ext = os.path.splitext(file_path)
            output_path = base + "_compressed" + ext
            final_path, size = self.compress_image(file_path, output_path)
            self.file_listbox.insert(tk.END, f"Compressed: {os.path.basename(final_path)} ({size} bytes)")
            self.file_listbox.see(tk.END)
        
        self.status_label.config(text="Compression complete!")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageCompressorApp(root)
    root.mainloop()