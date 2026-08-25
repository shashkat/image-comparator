#!/usr/bin/env python3
"""
Image Grid Comparator - GUI Version
Displays multiple images in a grid and allows navigation through their neighbors
using arrow keys. Includes a GUI for file selection and layout configuration.

Optional dependencies for enhanced features:
- reportlab: For creating PDF placeholders (pip install reportlab)
  If not installed, PNG placeholders will be created instead.
"""

import sys
import os
from pathlib import Path

# Set matplotlib backend before importing pyplot
import matplotlib
matplotlib.use('TkAgg')  # Use TkAgg backend for compatibility with tkinter

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
# from pdf2image import convert_from_path
import pymupdf
import numpy as np
from PIL import Image
import math
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

class ImageComparator:
    def __init__(self, image_paths, num_cols=2):
        """
        Initialize the image comparator with multiple images.
        
        Args:
            image_paths: List of paths to image files
            num_cols: Number of columns in the grid layout
        """
        self.num_images = len(image_paths)
        self.num_cols = num_cols
        self.num_rows = math.ceil(self.num_images / self.num_cols)
        
        # Convert paths and get directories
        self.paths = [Path(p).resolve() for p in image_paths]
        self.dirs = [p.parent for p in self.paths]

        # Get all image files in each directory (sorted alphabetically)
        self.all_files = []
        self.indices = []
        
        for i, path in enumerate(self.paths):
            files = self._get_image_files(self.dirs[i])
            self.all_files.append(files) # note that this is appending the whole list into the all_files list. So after this all_files becomes a list of lists
            
            # Find index of the starting file
            try:
                index = files.index(path)
                self.indices.append(index)
            except ValueError:
                print(f"Error: {path} not found in directory")
                sys.exit(1)
        
        # Set up the plot
        fig_width = 8 * self.num_cols
        fig_height = 6 * self.num_rows
        self.fig, self.axes = plt.subplots(self.num_rows, self.num_cols, 
                                           figsize=(fig_width, fig_height), 
                                           layout='constrained')
        
        # Make axes always iterable (handle single row/col cases)
        if self.num_images == 1:
            self.axes = np.array([self.axes])
        else:
            self.axes = self.axes.flatten()
        
        # Hide extra subplots if we don't have enough images to fill the grid
        for i in range(self.num_images, len(self.axes)):
            self.axes[i].axis('off')
        
        self.fig.canvas.mpl_connect('key_press_event', self._on_key) # register the self._on_key method as a callback for the matplotlib 
        # event 'key_press_event', which is emitted when a key is pressed on the keyboard when the canvas is active
        
        # Display initial images
        self.update_display()
        
    def _get_image_files(self, directory):
        """Get all image files in directory, sorted alphabetically."""
        image_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.tif'}
        files = []
        
        for file in sorted(directory.iterdir()): # directory.iterdir() lists all the files in a given directory
            if file.is_file() and file.suffix.lower() in image_extensions:
                files.append(file)
        
        return files
    
    def _load_image(self, filepath):
        """Load an image file (handles PDFs and regular images). Returns np.array()"""
        filepath = Path(filepath)
        
        if filepath.suffix.lower() == '.pdf':
            # Convert PDF to image (first page only)
            # images = convert_from_path(str(filepath), first_page=1, last_page=1)

            doc = pymupdf.open(str(filepath))

            # Render the first PDF page at higher resolution.
            page = doc[0]
            pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)

            # Convert the rendered page to an image array for matplotlib.
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n
            )
            doc.close()

            return img
        else:
            # Load regular image
            return mpimg.imread(str(filepath))
    
    def update_display(self):
        """Update all image displays."""
        # Clear and update each subplot
        for i in range(self.num_images):
            ax = self.axes[i]
            ax.clear()
            
            try:
                img = self._load_image(self.all_files[i][self.indices[i]]) # img is a np.array
                ax.imshow(img)
                filename = f'{self.all_files[i][self.indices[i]].parent.name}/{self.all_files[i][self.indices[i]].name}'
                position = f"({self.indices[i] + 1}/{len(self.all_files[i])})"
                ax.set_title(f"{filename}\n{position}", fontsize=10)
                ax.axis('off')
            except Exception as e:
                ax.text(0.5, 0.5, f"Error loading image:\n{str(e)}", 
                       ha='center', va='center', transform=ax.transAxes)
                filename = f'{self.all_files[i][self.indices[i]].parent.name}/{self.all_files[i][self.indices[i]].name}'
                ax.set_title(f"{filename} (ERROR)", fontsize=10)
                ax.axis('off')
        
        # self.fig.tight_layout()
        self.fig.canvas.draw()
    
    def _on_key(self, event):
        """Handle keyboard events."""
        if event.key == 'up':
            # Previous images - check if all can go back
            if all(idx > 0 for idx in self.indices):
                self.indices = [idx - 1 for idx in self.indices]
                self.update_display()
            else:
                print("Already at the first images")
                
        elif event.key == 'down':
            # Next images - check if all can go forward
            if all(self.indices[i] < len(self.all_files[i]) - 1 
                   for i in range(self.num_images)):
                self.indices = [idx + 1 for idx in self.indices]
                self.update_display()
            else:
                print("Already at the last images")
                
        elif event.key == 'q' or event.key == 'escape':
            # Quit
            plt.close(self.fig)
    
    def show(self):
        """Display the viewer window."""
        print(f"\nImage Comparator - Displaying {self.num_images} images in a {self.num_rows}x{self.num_cols} grid")
        print("Controls:")
        print("  ↑ (Up Arrow)   : Previous set")
        print("  ↓ (Down Arrow) : Next set")
        print("  Q or ESC       : Quit")
        print("\nShowing images...")
        plt.show()


class ConfigDialog:
    """GUI dialog for selecting files and configuring the layout."""
    
    def __init__(self):
        self.root = tk.Tk() # self.root is toplevel widget on a certain screen
        self.root.title("Image Comparator Configuration")
        self.root.geometry("900x700")
        
        # Force window to appear on top and gain focus
        self.root.lift() # raise the self.root widget in stacking order
        self.root.attributes('-topmost', True) # sets the value of '-topmost' flag (specific to platform) to True.
        self.root.after_idle(self.root.attributes, '-topmost', False) # call self.root.attributes with the args ('-topmost', False) if the Tcl main loop has no event to process
        self.root.focus_force() # Direct input focus to this widget even if the application doesn't have the focus. Should be used with caution
        
        self.selected_files = []
        self.num_cols = tk.IntVar(value=2) # construct an integer variable
        self.sync_directories = tk.BooleanVar(value=False) # construct a boolean variable
        
        self._create_widgets()
        
    def _create_widgets(self):
        """Create the GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10") # construct a ttk frame with self.root widget as parent
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S)) # position the main_frame widget in its parent (self.root) in a grid. row and column indicate the indices of the grid cell to put main_frame in. Sticky indicate which boundaries should main_frame stick to if its smaller than the cell
        self.root.columnconfigure(0, weight=1) # configure the 0-indexed column of self.root by setting its weight (how much does additional space propagate to this column) to 1
        # my understanding of weight=1 in columnconfigure and rowconfigure is that it lets that cell of the grid take as much space as other things allow.
        self.root.rowconfigure(0, weight=1) # configure the 0-indexed row of self.root by setting its weight (how much does additional space propagate to this row) to 1
        
        # Title
        title = ttk.Label(main_frame, text="Image Grid Comparator", # construct a ttk label with main_frame widget as parent
                         font=('TkDefaultFont', 16, 'bold'))
        title.grid(row=0, column=0, columnspan=3, pady=(0, 20)) # position the title widget in its parent (self.root) in a grid. columnspan indicates how many columns this widget will span. pady indicates the padding in y direction
        
        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="Selected Files", padding="10") # Labelframe widget is a container used to group other widgets together.
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        main_frame.rowconfigure(1, weight=1) # configure the 1-indexed row of main_frame by setting its weight (how much does additional space propagate to this row) to 1
        
        # Listbox with scrollbar
        scrollbar = ttk.Scrollbar(file_frame, orient=tk.VERTICAL) # Construct a Ttk Scrollbar with file_frame as parent
        self.file_listbox = tk.Listbox(file_frame, yscrollcommand=scrollbar.set, # Construct a Listbox widget with file_frame as parent
                                        height=15, width=80)
        scrollbar.config(command=self.file_listbox.yview) # Configure the scrollbar to have command argument set to vertical position of file_listbox. yview yields the vertical position of file_listbox. 
        
        self.file_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        file_frame.columnconfigure(0, weight=1)
        file_frame.rowconfigure(0, weight=1)
        
        # Button frame
        button_frame = ttk.Frame(file_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(button_frame, text="Add Files", 
                  command=self._add_files).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Remove Selected", 
                  command=self._remove_selected).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Clear All", 
                  command=self._clear_all).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Move Up", 
                  command=self._move_up).grid(row=0, column=3, padx=5)
        ttk.Button(button_frame, text="Move Down", 
                  command=self._move_down).grid(row=0, column=4, padx=5)
        
        # Layout configuration
        layout_frame = ttk.LabelFrame(main_frame, text="Layout Configuration", padding="10") # Labelframe widget is a container used to group other widgets together.
        layout_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(layout_frame, text="Number of Columns:").grid(row=0, column=0, padx=(0, 10))
        cols_spinbox = ttk.Spinbox(layout_frame, from_=1, to=10, 
                                   textvariable=self.num_cols, width=10)
        cols_spinbox.grid(row=0, column=1)
        
        # Preview label
        self.preview_label = ttk.Label(layout_frame, text="")
        self.preview_label.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        self._update_preview()
        
        # Bind spinbox change
        self.num_cols.trace('w', lambda *args: self._update_preview()) # Defines a trace callback for the variable. 'w' is mode. This means that whenever self.num_cols is written, self._update_preview() is called. args doesn't play a role here.
        
        # Directory synchronization section
        sync_frame = ttk.LabelFrame(main_frame, text="Directory Synchronization", padding="10")
        sync_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Checkbox
        sync_checkbox = ttk.Checkbutton(
            sync_frame, 
            text="Synchronize directories (create placeholder files for missing images)",
            variable=self.sync_directories
        )
        sync_checkbox.grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        # Explanation label
        explanation = ttk.Label(
            sync_frame,
            text="When enabled, analyzes all selected file directories and creates placeholder\n"
                 "files for any missing filenames. This keeps navigation synchronized.",
            foreground='gray'
        )
        explanation.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Sync button
        ttk.Button(
            sync_frame,
            text="Sync Directories Now",
            command=self._sync_directories
        ).grid(row=2, column=0, pady=(10, 0), sticky=tk.W)
        
        self.sync_status_label = ttk.Label(sync_frame, text="", foreground='blue')
        self.sync_status_label.grid(row=2, column=1, pady=(10, 0), padx=(10, 0), sticky=tk.W)
        
        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=4, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(action_frame, text="Start Comparator", 
                  command=self._start_comparator, 
                  style='Accent.TButton').grid(row=0, column=0, padx=5)
        ttk.Button(action_frame, text="Quit", 
                  command=self.root.quit).grid(row=0, column=1, padx=5)
        
        # Status bar
        self.status_label = ttk.Label(main_frame, text="Ready. Add files to begin.", 
                                     relief=tk.SUNKEN, anchor=tk.W) # relief=tk.SUNKEN makes the status bar appear in a sunked-like fashion
        self.status_label.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))

    def _add_files(self):
        """Open file dialog to add image files."""
        filetypes = [
            ('All supported images', '*.pdf *.png *.jpg *.jpeg *.bmp *.gif *.tiff *.tif'),
            ('PDF files', '*.pdf'),
            ('PNG files', '*.png'),
            ('JPEG files', '*.jpg *.jpeg'),
            ('All files', '*.*')
        ]
        
        files = filedialog.askopenfilenames(
            title="Select Image Files",
            filetypes=filetypes
        )
        
        if files:
            for file in files:
                if file not in self.selected_files:
                    self.selected_files.append(file)
                    # Show just the filename, but store full path
                    display_name = f'{Path(file).parent}/{Path(file).name}'
                    self.file_listbox.insert(tk.END, f"{len(self.selected_files)}. {display_name}") # .insert inserts elements at the specified index
            
            self._update_status(f"Added {len(files)} file(s)")
            self._update_preview()
    
    def _remove_selected(self):
        """Remove selected files from the list."""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select files to remove.")
            return
        
        # Remove in reverse order to maintain indices
        for index in reversed(selection):
            del self.selected_files[index]
            self.file_listbox.delete(index)
        
        # Renumber remaining items
        self._refresh_listbox()
        self._update_status("Removed selected file(s)")
        self._update_preview()
    
    def _clear_all(self):
        """Clear all selected files."""
        if self.selected_files and messagebox.askyesno("Clear All", 
                                                       "Remove all files from the list?"):
            self.selected_files.clear()
            self.file_listbox.delete(0, tk.END)
            self._update_status("Cleared all files")
            self._update_preview()
    
    def _move_up(self):
        """Move selected file up in the list."""
        selection = self.file_listbox.curselection()
        if not selection or selection[0] == 0:
            return
        
        index = selection[0]
        # Swap in list
        self.selected_files[index], self.selected_files[index-1] = \
            self.selected_files[index-1], self.selected_files[index]
        
        self._refresh_listbox()
        self.file_listbox.selection_clear(0, tk.END)
        self.file_listbox.selection_set(index-1)
        self.file_listbox.see(index-1)
    
    def _move_down(self):
        """Move selected file down in the list."""
        selection = self.file_listbox.curselection()
        if not selection or selection[0] == len(self.selected_files) - 1:
            return
        
        index = selection[0]
        # Swap in list
        self.selected_files[index], self.selected_files[index+1] = \
            self.selected_files[index+1], self.selected_files[index]
        
        self._refresh_listbox()
        self.file_listbox.selection_clear(0, tk.END)
        self.file_listbox.selection_set(index+1)
        self.file_listbox.see(index+1)
    
    def _refresh_listbox(self):
        """Refresh the listbox display with current files."""
        self.file_listbox.delete(0, tk.END)
        for i, file in enumerate(self.selected_files, 1):
            display_name = f'{Path(file).parent}/{Path(file).name}'
            self.file_listbox.insert(tk.END, f"{i}. {display_name}")
    
    def _update_preview(self):
        """Update the layout preview text."""
        if not self.selected_files:
            self.preview_label.config(text="")
            return
        
        num_files = len(self.selected_files)
        cols = self.num_cols.get() # get returns the value of the variable as an integer
        rows = math.ceil(num_files / cols)
        
        self.preview_label.config(
            text=f"Layout: {rows} row(s) × {cols} column(s) = {rows * cols} grid cells "
                 f"({num_files} images)"
        )
    
    def _update_status(self, message):
        """Update the status bar message."""
        self.status_label.config(text=message)

    def _get_all_filenames_from_directories(self, directories):
        """Get union of all image filenames across directories."""
        image_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.tif'}
        all_filenames = set()
        
        for directory in directories:
            dir_path = Path(directory)
            for file in dir_path.iterdir():
                if file.is_file() and file.suffix.lower() in image_extensions:
                    all_filenames.add(file.name)
        
        return sorted(all_filenames)
    
    def _create_placeholder_pdf(self, filepath, filename):
        """Create a placeholder PDF with a 'not found' message."""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            c = canvas.Canvas(str(filepath), pagesize=letter)
            width, height = letter
            
            # Draw message in center
            c.setFont("Helvetica-Bold", 24)
            c.drawCentredString(width / 2, height / 2 + 20, "Plot Not Found")
            
            c.setFont("Helvetica", 14)
            c.drawCentredString(width / 2, height / 2 - 20, f"Missing file: {filename}")
            c.drawCentredString(width / 2, height / 2 - 45, "This is a placeholder created by directory sync")
            
            c.save()
            return True
        except ImportError:
            # Return False if reportlab not available
            return False
    
    def _create_placeholder_image(self, filepath, filename):
        """Create a placeholder image with a 'not found' message."""
        from PIL import Image, ImageDraw, ImageFont
        
        # Create white image
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a font, fall back to default if not available
        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
            font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        except:
            try:
                font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
        
        # Draw text
        text1 = "Plot Not Found"
        text2 = f"Missing file: {filename}"
        text3 = "Placeholder created by directory sync"
        
        # Get bounding boxes and center text
        bbox1 = draw.textbbox((0, 0), text1, font=font_large)
        bbox2 = draw.textbbox((0, 0), text2, font=font_small)
        bbox3 = draw.textbbox((0, 0), text3, font=font_small)
        
        draw.text(((800 - (bbox1[2] - bbox1[0])) / 2, 250), text1, fill='red', font=font_large)
        draw.text(((800 - (bbox2[2] - bbox2[0])) / 2, 310), text2, fill='black', font=font_small)
        draw.text(((800 - (bbox3[2] - bbox3[0])) / 2, 340), text3, fill='gray', font=font_small)
        
        img.save(filepath)
    
    def _sync_directories(self):
        """Synchronize directories by creating placeholder files."""
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please add files first before syncing directories.")
            return
        
        # Get unique directories from selected files
        directories = list(set(Path(f).parent for f in self.selected_files))
        
        if len(directories) < 2:
            messagebox.showinfo("Single Directory", 
                              "Only one directory detected. Synchronization requires multiple directories.")
            return
        
        # Show confirmation dialog with directory list
        dir_list = "\n".join([f"  • {d}" for d in directories])
        message = f"This will synchronize the following directories:\n\n{dir_list}\n\n" \
                  f"Placeholder files will be created for missing images.\n\nContinue?"
        
        if not messagebox.askyesno("Confirm Synchronization", message):
            return
        
        try:
            # Get all unique filenames across all directories
            all_filenames = self._get_all_filenames_from_directories(directories)
            
            created_files = 0
            failed_pdfs = []
            
            # For each directory, check which files are missing
            for directory in directories:
                dir_path = Path(directory)
                existing_files = {f.name for f in dir_path.iterdir() 
                                if f.is_file() and f.suffix.lower() in 
                                {'.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.tif'}}
                
                missing_files = set(all_filenames) - existing_files
                
                for filename in missing_files:
                    filepath = dir_path / filename
                    
                    # Determine file type and create appropriate placeholder
                    if filepath.suffix.lower() == '.pdf':
                        success = self._create_placeholder_pdf(filepath, filename)
                        if success:
                            created_files += 1
                        else:
                            # reportlab not available - cannot create PDF placeholder
                            failed_pdfs.append(filename)
                    else:
                        self._create_placeholder_image(filepath, filename)
                        created_files += 1
            
            # Show results
            if failed_pdfs:
                result_msg = f"Synchronization incomplete!\n\n" \
                            f"Created {created_files} placeholder file(s)\n\n" \
                            f"⚠️ Could not create {len(failed_pdfs)} PDF placeholder(s):\n" \
                            f"reportlab package is required for PDF placeholders.\n\n" \
                            f"Install with: pip install reportlab\n\n" \
                            f"Failed files: {', '.join(failed_pdfs[:5])}" \
                            f"{'...' if len(failed_pdfs) > 5 else ''}"
                messagebox.showwarning("Sync Incomplete", result_msg)
                self.sync_status_label.config(text=f"⚠ Partial sync ({len(failed_pdfs)} PDFs failed)", 
                                             foreground='orange')
            else:
                result_msg = f"Synchronization complete!\n\n" \
                            f"Created {created_files} placeholder file(s)"
                messagebox.showinfo("Sync Complete", result_msg)
                self.sync_status_label.config(text=f"✓ Synced ({created_files} files created)", 
                                             foreground='green')
            
            self._update_status(f"Synchronized {len(directories)} directories")
            
        except Exception as e:
            messagebox.showerror("Sync Error", f"Error during synchronization:\n{str(e)}")
            self.sync_status_label.config(text="✗ Sync failed", foreground='red')
    
    def _start_comparator(self):
        """Validate and start the image comparator."""
        if not self.selected_files:
            messagebox.showerror("No Files", "Please add at least one image file.")
            return
        
        num_cols = self.num_cols.get()
        if num_cols < 1:
            messagebox.showerror("Invalid Columns", "Number of columns must be at least 1.")
            return
        
        # Validate that all files exist
        for file in self.selected_files:
            if not os.path.exists(file):
                messagebox.showerror("File Not Found", f"File not found: {file}")
                return
        
        # Check if auto-sync is enabled
        if self.sync_directories.get():
            directories = list(set(Path(f).parent for f in self.selected_files))
            if len(directories) > 1:
                response = messagebox.askyesno(
                    "Auto-Sync Enabled",
                    f"Directory synchronization is enabled.\n\n"
                    f"Do you want to sync {len(directories)} directories before starting the comparator?"
                )
                if response:
                    self._sync_directories()
        
        # Close the config dialog
        self.root.withdraw()
        
        # Create and show the comparator
        try:
            comparator = ImageComparator(self.selected_files, num_cols)
            comparator.show()
        except Exception as e:
            messagebox.showerror("Error", f"Error starting comparator:\n{str(e)}")
            self.root.deiconify()
            return
        
        # After comparator is closed, show the config dialog again
        self.root.deiconify()
        self._update_status("Comparator closed. Ready for new configuration.")
    
    def run(self):
        """Run the GUI application."""
        self.root.mainloop()


def main():
    """Main entry point for the GUI application."""
    print("Starting Image Comparator GUI...")
    print("If the window doesn't appear, check if it's behind other windows.")
    
    # Check if display is available
    try:
        app = ConfigDialog()
        print("GUI window created successfully.")
        app.run()
    except tk.TclError as e:
        print(f"\nError: Could not create GUI window.")
        print(f"Details: {e}")
        print("\nPossible causes:")
        print("1. No display available (are you using SSH without X forwarding?)")
        print("2. Missing tkinter installation")
        print("\nTo fix:")
        print("- On macOS: tkinter should be included with Python")
        print("- On Linux: install python3-tk (e.g., 'sudo apt-get install python3-tk')")
        print("- If using SSH: enable X forwarding with 'ssh -X' or use VNC")
        sys.exit(1)


if __name__ == "__main__":
    main()