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
from collections import Counter

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
from matplotlib.backend_tools import Cursors

IMAGE_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.tif'}


def get_image_files(directory):
    """Get all image files in directory, sorted alphabetically by filename without extension."""
    files = []
    dir_path = Path(directory).resolve()
    if dir_path.is_dir():
        # sort on the stem first, so that directories holding the same filenames with
        # different extensions are ordered identically (e.g. 'a-b.jpg' vs 'a.png')
        for file in sorted(dir_path.iterdir(), key=lambda f: (f.stem, f.suffix)):
            if file.is_file() and file.suffix.lower() in IMAGE_EXTENSIONS:
                files.append(file.resolve())
    return files


class ImageComparator:
    def __init__(self, image_paths, num_cols=2, dpi_for_pdf=96):
        """
        Initialize the image comparator with multiple images.
        
        Args:
            image_paths: List of paths to image files
            num_cols: Number of columns in the grid layout
        """
        self.num_images = len(image_paths)
        self.dpi_for_pdf = dpi_for_pdf
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
        self.fig = plt.figure(figsize=(fig_width, fig_height), layout='constrained')
        
        # Each row gets its own sub-gridspec, so that column widths can be adjusted per row
        # (by dragging the gaps between panels) without affecting the other rows
        self.outer_gs = self.fig.add_gridspec(self.num_rows, 1)
        self.row_gs = [self.outer_gs[r].subgridspec(1, self.num_cols) for r in range(self.num_rows)]
        self.height_ratios = [1.0] * self.num_rows
        self.width_ratios = [[1.0] * self.num_cols for _ in range(self.num_rows)]
        self.axes = np.array([self.fig.add_subplot(self.row_gs[r][0, c])
                              for r in range(self.num_rows) for c in range(self.num_cols)])
        
        # Hide extra subplots if we don't have enough images to fill the grid
        for i in range(self.num_images, len(self.axes)):
            self.axes[i].axis('off')
        
        self.fig.canvas.mpl_connect('key_press_event', self._on_key) # register the self._on_key method as a callback for the matplotlib 
        # event 'key_press_event', which is emitted when a key is pressed on the keyboard when the canvas is active
        
        # Mouse callbacks for resizing panels by dragging the gaps between them
        self._drag = None
        self._resize_cursor_shown = False
        self.fig.canvas.mpl_connect('button_press_event', self._on_press)
        self.fig.canvas.mpl_connect('motion_notify_event', self._on_motion)
        self.fig.canvas.mpl_connect('button_release_event', self._on_release)
        
        # Display initial images
        self.update_display()
        
    def _get_image_files(self, directory):
        """Get all image files in directory, sorted alphabetically."""
        return get_image_files(directory)
    
    def _load_image(self, filepath):
        """Load an image file (handles PDFs and regular images). Returns np.array()"""
        filepath = Path(filepath)
        
        if filepath.suffix.lower() == '.pdf':
            # Convert PDF to image (first page only)
            # images = convert_from_path(str(filepath), first_page=1, last_page=1)

            doc = pymupdf.open(str(filepath))

            # Render the first PDF page at higher resolution.
            page = doc[0]
            pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False, dpi=self.dpi_for_pdf)

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
        
        # Update window title with current comparator index if available
        if hasattr(self.fig.canvas, 'manager') and self.fig.canvas.manager:
            try:
                curr_idx = 1 + min(self.indices)
                max_idx = curr_idx + min(len(self.all_files[j]) - 1 - self.indices[j] for j in range(self.num_images))
                self.fig.canvas.manager.set_window_title(f"Image Comparator (Index {curr_idx}/{max_idx})")
            except Exception:
                pass

        # Reset the toolbar's zoom/pan history so that Home returns to the view of the
        # currently displayed images, not to the images that were shown when first zooming
        toolbar = getattr(self.fig.canvas, 'toolbar', None)
        if toolbar is not None:
            toolbar.update()

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
                
        elif event.key == 'd':
            # Back to the default mode (resizing panels by dragging) from zoom or pan mode.
            # Zoom ('o') and pan ('p') are toggled by matplotlib's own toolbar shortcuts.
            toolbar = getattr(self.fig.canvas, 'toolbar', None)
            if toolbar is not None:
                if toolbar.mode == 'zoom rect':
                    toolbar.zoom()
                elif toolbar.mode == 'pan/zoom':
                    toolbar.pan()
                
        elif event.key == 'e':
            # Make all panels equally sized again
            self.height_ratios = [1.0] * self.num_rows
            self.width_ratios = [[1.0] * self.num_cols for _ in range(self.num_rows)]
            self._apply_ratios()
                
        elif event.key == 'q' or event.key == 'escape':
            # Quit
            plt.close(self.fig)
    
    def _apply_ratios(self):
        """Apply the current row heights and per-row column widths to the grid and redraw."""
        self.outer_gs.set_height_ratios(self.height_ratios)
        for r, gs in enumerate(self.row_gs):
            gs.set_width_ratios(self.width_ratios[r])
        self.fig.canvas.draw_idle()
    
    def _row_boxes(self, r):
        """Layout boxes (in figure fractions, before aspect-ratio shrinking) of the panels in row r."""
        return [ax.get_position(original=True) for ax in self.axes[r * self.num_cols:(r + 1) * self.num_cols]]
    
    def _find_boundary(self, x, y):
        """
        Return the panel boundary under the figure-fraction point (x, y), or None.
        A boundary is the gap between two neighbouring rows, or between two neighbouring
        panels in the same row.
        """
        tol_x = 6 / self.fig.bbox.width
        tol_y = 6 / self.fig.bbox.height
        rows = [self._row_boxes(r) for r in range(self.num_rows)]
        tops = [max(b.y1 for b in boxes) for boxes in rows]
        bottoms = [min(b.y0 for b in boxes) for boxes in rows]
        
        # Gaps between rows (row r is above row r + 1)
        for r in range(self.num_rows - 1):
            if tops[r + 1] - tol_y <= y <= bottoms[r] + tol_y:
                return {'kind': 'row', 'index': r, 'start': tops[r], 'end': bottoms[r + 1]}
        
        # Gaps between panels within the row that contains y
        for r, boxes in enumerate(rows):
            if bottoms[r] <= y <= tops[r]:
                for c in range(self.num_cols - 1):
                    if boxes[c].x1 - tol_x <= x <= boxes[c + 1].x0 + tol_x:
                        return {'kind': 'col', 'row': r, 'index': c, 'start': boxes[c].x0, 'end': boxes[c + 1].x1}
        return None
    
    def _toolbar_busy(self):
        """True while the toolbar's zoom or pan mode is active, so that dragging doesn't conflict with it."""
        toolbar = getattr(self.fig.canvas, 'toolbar', None)
        return toolbar is not None and bool(toolbar.mode)
    
    def _on_press(self, event):
        if event.button != 1 or event.dblclick or self._toolbar_busy():
            return
        x, y = self.fig.transFigure.inverted().transform((event.x, event.y))
        self._drag = self._find_boundary(x, y)
    
    def _on_motion(self, event):
        x, y = self.fig.transFigure.inverted().transform((event.x, event.y))
        
        if self._drag is None:
            # Show a resize cursor when hovering over a draggable gap
            boundary = None if self._toolbar_busy() else self._find_boundary(x, y)
            if boundary is not None:
                cursor = Cursors.RESIZE_VERTICAL if boundary['kind'] == 'row' else Cursors.RESIZE_HORIZONTAL
                self.fig.canvas.set_cursor(cursor)
                self._resize_cursor_shown = True
            elif self._resize_cursor_shown:
                self.fig.canvas.set_cursor(Cursors.POINTER)
                self._resize_cursor_shown = False
            return
        
        # Split the combined size of the two neighbouring panels at the mouse position.
        # The span is measured at the start of the drag, from the far edge of the first panel
        # to the far edge of the second one.
        d = self._drag
        pos = x if d['kind'] == 'col' else y
        fraction = (pos - d['start']) / (d['end'] - d['start'])
        fraction = min(max(fraction, 0.05), 0.95)
        
        ratios = self.width_ratios[d['row']] if d['kind'] == 'col' else self.height_ratios
        i = d['index']
        total = ratios[i] + ratios[i + 1]
        ratios[i], ratios[i + 1] = total * fraction, total * (1 - fraction)
        self._apply_ratios()
    
    def _on_release(self, event):
        self._drag = None
    
    def show(self):
        """Display the viewer window."""
        curr_idx = 1 + min(self.indices)
        max_idx = curr_idx + min(len(self.all_files[j]) - 1 - self.indices[j] for j in range(self.num_images))
        print(f"\nImage Comparator - Displaying {self.num_images} images in a {self.num_rows}x{self.num_cols} grid (Index {curr_idx}/{max_idx})")
        print("Controls:")
        print("  ↑ (Up Arrow)   : Previous set")
        print("  ↓ (Down Arrow) : Next set")
        print("  D              : Default mode (drag gaps between panels to resize them)")
        print("  O              : Toggle zoom mode (drag a rectangle to zoom in)")
        print("  P              : Toggle pan mode (drag to pan, right-drag to zoom)")
        print("  H              : Reset zoom/pan of all panels")
        print("  Drag gap       : Resize neighbouring panels (in default mode)")
        print("  E              : Make all panels equally sized again")
        print("  Q or ESC       : Quit")
        print("\nShowing images...")
        plt.show()


class ConfigDialog:
    """GUI dialog for selecting files and configuring the layout."""
    
    def __init__(self):
        self.root = tk.Tk() # self.root is toplevel widget on a certain screen
        self.root.title("Image Comparator Configuration")
        self.root.geometry("800x760")
        
        # Force window to appear on top and gain focus
        self.root.lift() # raise the self.root widget in stacking order
        self.root.attributes('-topmost', True) # sets the value of '-topmost' flag (specific to platform) to True.
        self.root.after_idle(self.root.attributes, '-topmost', False) # call self.root.attributes with the args ('-topmost', False) if the Tcl main loop has no event to process
        self.root.focus_force() # Direct input focus to this widget even if the application doesn't have the focus. Should be used with caution
        
        self.selected_files = []
        self.dpi_for_pdf = tk.IntVar(value=200) # construct an integer variable
        self.num_cols = tk.IntVar(value=2) # construct an integer variable
        
        self.starting_index_var = tk.StringVar(value="")
        self.default_starting_index = None
        self.min_valid_index = None
        self.max_valid_index = None
        self.cached_dir_files = []
        self.cached_selected_indices = []

        self._create_widgets()
        self._update_starting_index()
        
    def _create_widgets(self):
        """Create the GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10") # construct a ttk frame with self.root widget as parent
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S)) # position the main_frame widget in its parent (self.root) in a grid. row and column indicate the indices of the grid cell to put main_frame in. Sticky indicate which boundaries should main_frame stick to if its smaller than the cell
        self.root.columnconfigure(0, weight=1) # configure the 0-indexed column of self.root by setting its weight (how much does additional space propagate to this column) to 1
        # my understanding of weight=1 in columnconfigure and rowconfigure is that it lets that cell of the grid take as much space as other things allow.
        self.root.rowconfigure(0, weight=1) # configure the 0-indexed row of self.root by setting its weight (how much does additional space propagate to this row) to 1
        
        # Title
        title = ttk.Label(main_frame, text="Image Comparator", # construct a ttk label with main_frame widget as parent
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
        
        # Starting index section
        index_frame = ttk.LabelFrame(main_frame, text="Starting Index", padding="10")
        index_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(index_frame, text="Starting-index-value according to chosen plots:").grid(
            row=0, column=0, padx=(0, 10), pady=(0, 5), sticky=tk.W
        )
        self.chosen_index_label = ttk.Label(index_frame, text="N/A", font=('TkDefaultFont', 10, 'bold'))
        self.chosen_index_label.grid(row=0, column=1, padx=(0, 15), pady=(0, 5), sticky=tk.W)

        self.valid_range_label = ttk.Label(index_frame, text="(Valid range: N/A)", foreground='gray')
        self.valid_range_label.grid(row=0, column=2, pady=(0, 5), sticky=tk.W)

        ttk.Label(index_frame, text="Comparator starting index:").grid(
            row=1, column=0, padx=(0, 10), pady=(5, 5), sticky=tk.W
        )

        index_controls_frame = ttk.Frame(index_frame)
        index_controls_frame.grid(row=1, column=1, columnspan=2, pady=(5, 5), sticky=tk.W)

        self.starting_index_spinbox = ttk.Spinbox(
            index_controls_frame,
            from_=1,
            to=1,
            textvariable=self.starting_index_var,
            width=8,
            state='disabled'
        )
        self.starting_index_spinbox.grid(row=0, column=0, padx=(0, 10), sticky=tk.W)

        self.reset_index_btn = ttk.Button(
            index_controls_frame,
            text="Reset to Chosen Plots",
            command=self._reset_starting_index,
            state='disabled'
        )
        self.reset_index_btn.grid(row=0, column=1, sticky=tk.W)

        self.index_status_label = ttk.Label(
            index_frame,
            text="Add files to calculate starting index.",
            foreground='gray'
        )
        self.index_status_label.grid(row=2, column=0, columnspan=3, pady=(5, 0), sticky=tk.W)

        self.starting_index_var.trace_add('write', self._on_starting_index_change)

        # Layout configuration
        layout_frame = ttk.LabelFrame(main_frame, text="Layout Configuration", padding="10") # Labelframe widget is a container used to group other widgets together.
        layout_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(layout_frame, text="PDF rendering DPI (higher causes clearer plots but slower):").grid(
            row=0, column=0, padx=(0, 10), pady=(10, 0), sticky=tk.W
        )

        self.dpi_spinbox = ttk.Spinbox(
            layout_frame,
            from_=50,
            to=1200,
            increment=50,
            textvariable=self.dpi_for_pdf,
            width=10,
        )
        self.dpi_spinbox.grid(row=0, column=1, pady=(10, 0), sticky=(tk.W, tk.E))
        
        ttk.Label(layout_frame, text="Number of columns in plot grid:").grid(row=1, column=0, padx=(0, 10), sticky=(tk.W))
        self.cols_spinbox = ttk.Spinbox(layout_frame, from_=1, to=10, 
                                        textvariable=self.num_cols, width=10)
        self.cols_spinbox.grid(row=1, column=1, sticky=(tk.W, tk.E))

        # Preview label
        self.preview_label = ttk.Label(layout_frame, text="")
        self.preview_label.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        self._update_preview()
        
        # Bind spinbox change
        self.num_cols.trace_add('write', lambda *args: self._update_preview()) # Defines a trace callback for the variable. 'w' is mode. This means that whenever self.num_cols is written, self._update_preview() is called. args doesn't play a role here.
        
        # Directory synchronization section
        sync_frame = ttk.LabelFrame(main_frame, text="Directory Synchronization", padding="10")
        sync_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Explanation label
        explanation = ttk.Label(
            sync_frame,
            text="Analyzes all selected file directories and creates placeholder files\n"
                 "for any missing filenames. This keeps navigation synchronized.",
            foreground='gray'
        )
        explanation.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # Check sync status button (read-only, creates no files)
        ttk.Button(
            sync_frame,
            text="Check Sync Status",
            command=self._check_sync_status
        ).grid(row=1, column=0, pady=(10, 0), padx=(0, 5), sticky=tk.W)
        
        # Sync button
        ttk.Button(
            sync_frame,
            text="Sync Directories Now",
            command=self._sync_directories
        ).grid(row=1, column=1, pady=(10, 0), sticky=tk.W)
        
        self.sync_status_label = ttk.Label(sync_frame, text="", foreground='blue')
        self.sync_status_label.grid(row=1, column=2, pady=(10, 0), padx=(10, 0), sticky=tk.W)
        
        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=5, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(action_frame, text="Start Comparator", 
                  command=self._start_comparator, 
                  style='Accent.TButton').grid(row=0, column=0, padx=5)
        ttk.Button(action_frame, text="Quit", 
                  command=self.root.quit).grid(row=0, column=1, padx=5)
        
        # Status bar
        self.status_label = ttk.Label(main_frame, text="Ready. Add files to begin.", 
                                     relief=tk.SUNKEN, anchor=tk.W) # relief=tk.SUNKEN makes the status bar appear in a sunked-like fashion
        self.status_label.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))

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
            self._update_starting_index(reset_value=True)
    
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
        self._update_starting_index(reset_value=True)
    
    def _clear_all(self):
        """Clear all selected files."""
        if self.selected_files and messagebox.askyesno("Clear All", 
                                                       "Remove all files from the list?"):
            self.selected_files.clear()
            self.file_listbox.delete(0, tk.END)
            self._update_status("Cleared all files")
            self._update_preview()
            self._update_starting_index(reset_value=True)
    
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
        self._update_starting_index(reset_value=False)
    
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
        self._update_starting_index(reset_value=False)
    
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

    def _get_all_stems_from_directories(self, directories):
        """Get union of all image filenames (without extensions) across directories."""
        all_stems = set()
        for directory in directories:
            for file in get_image_files(directory):
                all_stems.add(file.stem)
        return sorted(all_stems)
    
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
    
    def _check_sync_status(self):
        """Report missing and duplicate filenames (ignoring extensions) without creating any files."""
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please add files first before checking sync status.")
            return
        
        # Unique directories of the selected files, in the order they were selected
        directories = list(dict.fromkeys(Path(f).parent for f in self.selected_files))
        
        def preview(names, limit=5):
            return ", ".join(names[:limit]) + (f", ... ({len(names)} total)" if len(names) > limit else "")
        
        try:
            dir_files = {d: get_image_files(d) for d in directories}
            all_stems = self._get_all_stems_from_directories(directories)
            
            issues = []
            for directory, files in dir_files.items():
                stems = [f.stem for f in files]
                stem_counts = Counter(stems)
                
                # i) filenames present in other directories but missing here
                missing = sorted(set(all_stems) - set(stems))
                # ii) filenames appearing more than once here (e.g. sample_A.png and sample_A.pdf)
                duplicates = sorted(stem for stem, count in stem_counts.items() if count > 1)
                
                if missing or duplicates:
                    lines = [f"{directory.name}/  ({len(files)} files)"]
                    if missing:
                        lines.append(f"    Missing {len(missing)}: {preview(missing)}")
                    if duplicates:
                        dup_names = [f.name for f in files if f.stem in duplicates]
                        lines.append(f"    Duplicated {len(duplicates)}: {preview(dup_names)}")
                    issues.append("\n".join(lines))
        except Exception as e:
            messagebox.showerror("Sync Status Error", f"Error while checking sync status:\n{str(e)}")
            return
        
        if not issues:
            messagebox.showinfo(
                "Sync Status",
                f"All {len(directories)} directories are in sync.\n\n"
                f"Each has the same {len(all_stems)} filenames (ignoring extensions), with no duplicates."
            )
            self.sync_status_label.config(text="✓ In sync", foreground='green')
            self._update_status(f"Checked {len(directories)} directories: in sync")
        else:
            messagebox.showwarning(
                "Sync Status",
                f"{len(issues)} of {len(directories)} directories have issues "
                f"({len(all_stems)} unique filenames across all directories, ignoring extensions):\n\n"
                + "\n\n".join(issues) +
                "\n\nMissing files can be filled with placeholders using \"Sync Directories Now\". "
                "Duplicates must be resolved manually."
            )
            self.sync_status_label.config(text=f"⚠ Out of sync ({len(issues)} directories with issues)",
                                         foreground='orange')
            self._update_status(f"Checked {len(directories)} directories: {len(issues)} with issues")
    
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
            # Get all unique filenames (ignoring extensions) across all directories
            all_stems = self._get_all_stems_from_directories(directories)
            
            created_files = 0
            failed_pdfs = []
            
            # For each directory, check which filenames are missing, regardless of extension
            for directory in directories:
                dir_path = Path(directory)
                files = get_image_files(dir_path)
                existing_stems = {f.stem for f in files}
                
                # Placeholders take the most common extension in this directory
                extension = Counter(f.suffix for f in files).most_common(1)[0][0] if files else '.png'
                
                missing_stems = sorted(set(all_stems) - existing_stems)
                
                for stem in missing_stems:
                    filename = f"{stem}{extension}"
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
            self._update_starting_index(reset_value=False)
            
        except Exception as e:
            messagebox.showerror("Sync Error", f"Error during synchronization:\n{str(e)}")
            self.sync_status_label.config(text="✗ Sync failed", foreground='red')
    
    def _calculate_index_range(self):
        """
        Calculate the valid starting index range and default index based on selected files.
        Returns a dict with:
            valid: bool
            min_index: int or None
            max_index: int or None
            default_index: int or None
            dir_files: list of list of Path
            selected_indices: list of int
            error: str or None
        """
        if not self.selected_files:
            return {
                'valid': False,
                'min_index': None,
                'max_index': None,
                'default_index': None,
                'dir_files': [],
                'selected_indices': [],
                'error': None
            }

        dir_files = []
        selected_indices = []

        for file_str in self.selected_files:
            file_path = Path(file_str).resolve()
            if not file_path.exists():
                return {
                    'valid': False,
                    'min_index': None,
                    'max_index': None,
                    'default_index': None,
                    'dir_files': [],
                    'selected_indices': [],
                    'error': f"File does not exist: {file_path.name}"
                }

            directory = file_path.parent
            files = get_image_files(directory)
            try:
                idx = files.index(file_path)
            except ValueError:
                return {
                    'valid': False,
                    'min_index': None,
                    'max_index': None,
                    'default_index': None,
                    'dir_files': [],
                    'selected_indices': [],
                    'error': f"File not found among valid image files in {directory.name}: {file_path.name}"
                }

            dir_files.append(files)
            selected_indices.append(idx)

        max_backward = min(selected_indices)
        max_forward = min(len(files) - 1 - idx for files, idx in zip(dir_files, selected_indices))
        min_index = 1
        max_index = 1 + max_backward + max_forward
        default_index = 1 + max_backward

        return {
            'valid': True,
            'min_index': min_index,
            'max_index': max_index,
            'default_index': default_index,
            'dir_files': dir_files,
            'selected_indices': selected_indices,
            'error': None
        }

    def _get_preview_filenames_at_index(self, index):
        """Return a compact preview string of filenames at the given index."""
        if not self.cached_dir_files or not self.cached_selected_indices or self.default_starting_index is None:
            return ""

        offset = index - self.default_starting_index
        names = []
        for i, idx in enumerate(self.cached_selected_indices):
            target_idx = idx + offset
            if 0 <= target_idx < len(self.cached_dir_files[i]):
                names.append(self.cached_dir_files[i][target_idx].name)
            else:
                names.append("?")

        if len(names) <= 3:
            return ", ".join(names)
        else:
            return ", ".join(names[:3]) + f", ... ({len(names)} files)"

    def _update_starting_index(self, reset_value=True):
        """Update the starting index display and bounds based on current selected files."""
        result = self._calculate_index_range()

        if not result['valid']:
            self.min_valid_index = None
            self.max_valid_index = None
            self.default_starting_index = None
            self.cached_dir_files = []
            self.cached_selected_indices = []

            self.chosen_index_label.config(text="N/A")
            self.valid_range_label.config(text="(Valid range: N/A)")
            self.starting_index_spinbox.config(state='disabled', from_=1, to=1)
            self.reset_index_btn.config(state='disabled')

            error_msg = result['error']
            if error_msg:
                self.index_status_label.config(text=error_msg, foreground='red')
            else:
                self.index_status_label.config(text="Add files to calculate starting index.", foreground='gray')

            self.starting_index_var.set("")
            return

        self.min_valid_index = result['min_index']
        self.max_valid_index = result['max_index']
        self.default_starting_index = result['default_index']
        self.cached_dir_files = result['dir_files']
        self.cached_selected_indices = result['selected_indices']

        # Display current starting-index-value according to chosen plots and their directories
        self.chosen_index_label.config(text=str(self.default_starting_index))
        total_valid = self.max_valid_index - self.min_valid_index + 1
        self.valid_range_label.config(
            text=f"(Valid range: {self.min_valid_index} to {self.max_valid_index}, total: {total_valid})"
        )

        # Configure spinbox bounds and enable
        self.starting_index_spinbox.config(
            state='normal',
            from_=self.min_valid_index,
            to=self.max_valid_index
        )
        self.reset_index_btn.config(state='normal')

        should_reset = reset_value
        if not should_reset:
            try:
                curr_val = int(self.starting_index_var.get().strip())
                if not (self.min_valid_index <= curr_val <= self.max_valid_index):
                    should_reset = True
            except (ValueError, tk.TclError):
                should_reset = True

        if should_reset:
            self.starting_index_var.set(str(self.default_starting_index))
        else:
            self._on_starting_index_change()

    def _reset_starting_index(self):
        """Reset the comparator starting index to the value corresponding to chosen plots."""
        if self.default_starting_index is not None:
            self.starting_index_var.set(str(self.default_starting_index))

    def _on_starting_index_change(self, *args):
        """Handle changes to the comparator starting index entry/spinbox."""
        if not self.selected_files or self.min_valid_index is None or self.max_valid_index is None:
            return

        val_str = self.starting_index_var.get().strip()
        if not val_str:
            self.index_status_label.config(
                text=f"Please enter an index between {self.min_valid_index} and {self.max_valid_index}.",
                foreground='red'
            )
            return

        try:
            val = int(val_str)
        except ValueError:
            self.index_status_label.config(
                text=f"Invalid number. Please enter an integer between {self.min_valid_index} and {self.max_valid_index}.",
                foreground='red'
            )
            return

        if self.min_valid_index <= val <= self.max_valid_index:
            offset = val - self.default_starting_index
            preview_str = self._get_preview_filenames_at_index(val)
            if offset == 0:
                self.index_status_label.config(
                    text=f"Plots at index {val} (corresponds to chosen plots): {preview_str}",
                    foreground='darkgreen'
                )
            else:
                sign = f"+{offset}" if offset > 0 else f"{offset}"
                step_word = "step" if abs(offset) == 1 else "steps"
                self.index_status_label.config(
                    text=f"Plots at index {val} ({sign} {step_word} from chosen plots): {preview_str}",
                    foreground='#004488'
                )
        else:
            self.index_status_label.config(
                text=f"Out of range! Must be between {self.min_valid_index} and {self.max_valid_index}.",
                foreground='red'
            )

    def _start_comparator(self):
        """Validate and start the image comparator."""
        if not self.selected_files:
            messagebox.showerror("No Files", "Please add at least one image file.")
            return

        try:
            num_cols = self.num_cols.get()
        except tk.TclError:
            messagebox.showerror(
                "Invalid Columns",
                "Number of columns must be a positive whole number."
            )
            self.cols_spinbox.focus_set()
            return

        if num_cols < 1:
            messagebox.showerror(
                "Invalid Columns",
                "Number of columns must be at least 1."
            )
            self.cols_spinbox.focus_set()
            return

        try:
            dpi_for_pdf = self.dpi_for_pdf.get()
        except tk.TclError:
            messagebox.showerror(
                "Invalid PDF DPI",
                "PDF rendering DPI must be a whole number, for example 150, 200, or 300."
            )
            self.dpi_spinbox.focus_set()
            return

        if dpi_for_pdf < 1:
            messagebox.showerror(
                "Invalid PDF DPI",
                "PDF rendering DPI must be at least 1."
            )
            self.dpi_spinbox.focus_set()
            return

        # Validate that all files exist
        for file in self.selected_files:
            if not os.path.exists(file):
                messagebox.showerror("File Not Found", f"File not found: {file}")
                return
        
        # Recalculate index range to ensure up-to-date directory information
        result = self._calculate_index_range()
        if not result['valid']:
            messagebox.showerror("Index Error", result['error'] or "Error calculating index range.")
            return

        min_idx = result['min_index']
        max_idx = result['max_index']
        default_idx = result['default_index']

        try:
            start_idx = int(self.starting_index_var.get().strip())
        except (ValueError, tk.TclError):
            messagebox.showerror(
                "Invalid Starting Index",
                f"Starting index must be an integer between {min_idx} and {max_idx}."
            )
            self.starting_index_spinbox.focus_set()
            return

        if start_idx < min_idx or start_idx > max_idx:
            messagebox.showerror(
                "Invalid Starting Index",
                f"Starting index must be between {min_idx} and {max_idx}."
            )
            self.starting_index_spinbox.focus_set()
            return

        # Compute first plots to show based on user-specified starting-index-value
        offset = start_idx - default_idx
        start_files = []
        for i in range(len(self.selected_files)):
            target_idx = result['selected_indices'][i] + offset
            start_files.append(str(result['dir_files'][i][target_idx]))

        # Close the config dialog
        self.root.withdraw()
        
        # Create and show the comparator
        try:
            comparator = ImageComparator(start_files, num_cols, dpi_for_pdf)
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