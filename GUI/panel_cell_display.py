import tkinter as tk
import numpy as np
import cv2

from tkinter import ttk
from PIL import Image, ImageTk

from anaylsis import calculate_cell_score
from tools import cropping_region

class SelectedCellPanel(tk.Frame):
    def __init__(
        self, window: tk.Tk, parent: tk.Widget,
        rows: int = 10, cols: int = 4, block_size: tuple = (70, 70), 
        *args, **kwargs
    )-> None:
        super().__init__(parent, *args, **kwargs)
        self.window = window
        
        self.rows = rows
        self.cols = cols
        self.block_size = block_size
        
        self.items = []
        self.images = []
        self.buttons = []

        # Create a 2D grid to track empty and occupied positions
        self.grid_occupancy = [[False for _ in range(self.cols)] for _ in range(self.rows)]

        self.window.selected_cell_panel = self
        self._initialize_widgets()

    def _initialize_widgets(self):
        """Initialize and pack all widgets."""
        title = tk.Label(
            self,
            text='Selected Cell', font='Arial 12 bold',
            bg='#292929', fg='#FFFFFF',
            anchor='center', 
        )
        title.pack(fill=tk.X, ipady=5)
        
        self.canvas = tk.Canvas(
            master=self, 
            bg='#303030', 
            width=250, height=300,
            highlightthickness=0,
        )
        
        self.scrollable_frame = tk.Frame(self.canvas, bg='#303030')
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.canvas.bind("<Enter>", self._bind_mouse_scroll)
        self.canvas.bind("<Leave>", self._unbind_mouse_scroll)
        
    def _bind_mouse_scroll(self, event):
        """Bind mouse scroll event to the canvas."""
        self.canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind_all("<Button-4>", self._on_mouse_wheel)
        self.canvas.bind_all("<Button-5>", self._on_mouse_wheel)

    def _unbind_mouse_scroll(self, event):
        """Unbind mouse scroll event when the mouse leaves the panel."""
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mouse_wheel(self, event):
        """Handle mouse wheel scroll."""
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")

    def _create_button(self, parent, image, label_text, row, col):
        """Create a button with an image and label, and return its frame."""
        from PIL import ImageTk
        image_resized = image.resize(self.block_size)
        photo = ImageTk.PhotoImage(image_resized)

        button_frame = tk.Frame(parent, bg='#303030')
        button_frame.grid(row=row, column=col, padx=5, pady=5)

        button = ttk.Button(button_frame, image=photo, command=lambda: self.on_button_click(label_text))
        button.pack(side="top")
        
        self.images.append(photo)
        self.buttons.append(button)
        
        return button_frame

    def _find_next_empty_position(self):
        """Find the next empty position (row, col) in the grid."""
        for row in range(self.rows):
            for col in range(self.cols):
                if not self.grid_occupancy[row][col]:
                    return row, col
        return None, None

    def add_button(self, image, label_text):
        """Add a button with the given image and ID to the next available position in the grid."""
        row, col = self._find_next_empty_position()
        
        if row is not None and col is not None:
            self.items.append((image, label_text))
            self._create_button(self.scrollable_frame, image, label_text, row, col)
            self.grid_occupancy[row][col] = True
        else:
            print("No more space available for new buttons.")

    def remove_button(self, button_id):
        """Remove a specific button by its ID and free up the position."""
        for i, (_, id_) in enumerate(self.items):
            if id_ == button_id:
                # Find the button's position in the grid
                button_frame = self.buttons[i].master
                grid_info = button_frame.grid_info()
                row = grid_info['row']
                col = grid_info['column']
                
                # Remove the button and its associated data
                self.items.pop(i)
                self.buttons.pop(i).master.destroy()
                self.images.pop(i)
                
                # Mark the position as empty
                self.grid_occupancy[row][col] = False
                break
        else:
            print("Item not found.")
            return

    def on_button_click(self, label_text):
        """Handle button click events by selecting the corresponding Treeview item."""
        
        cell_treeview = self.window.cell_treeview
        selected_item = cell_treeview.selection()

        for item in cell_treeview.get_children():
            cell_label = cell_treeview.item(item, 'text')
            
            if cell_label == label_text:
                if selected_item:
                    cell_treeview.selection_remove(selected_item[0])
                cell_treeview.selection_set(item)
                cell_treeview.focus(item)
                break

    def remove_all_buttons(self):
        """Remove all cell buttons and clear associated data."""
        # Destroy all button frame widgets
        for button in self.buttons:
            button.master.destroy()

        # Clear all lists tracking buttons, images, and items
        self.items.clear()
        self.images.clear()
        self.buttons.clear()

        # Reset the grid occupancy
        self.grid_occupancy = [[False for _ in range(self.cols)] for _ in range(self.rows)]


class CellDisplayPanel(tk.Frame):
    def __init__(
        self,  parent: tk.Widget, window: tk.Tk,
        button_width: int = 6,
        button_background: str = '#505050', button_foreground: str = '#FFFFFF',
        activate_background: str = '#3C3B3B', activate_foreground: str = '#FFFFFF',
    ) -> None:
        super().__init__(parent, bg = '#202020')
        window.cell_display = self
        
        self.window = window
        
        self.raw_image = None
        self.boundary_image = None
        
        self.her2_mask = None
        self.chr17_mask = None
        
        self.show_raw = False
        self.show_all = False
        self.show_her2 = False
        self.show_chr17 = False
        
        # Toolbar Setup
        toolbar = tk.Frame(self, bg = '#303030')
        toolbar.pack(side = tk.TOP)
        
        # Canvas Setup
        self.canvas = tk.Canvas(master = self,  bg = '#212121', highlightthickness = 0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Button Setup
        drag_button = tk.Button(
            master = toolbar, text = 'Drag', width= button_width,
            bg = button_background, fg = button_foreground,
            activebackground = activate_background, activeforeground = activate_foreground,
            borderwidth = 0, highlightthickness = 0,
            relief = tk.FLAT, command= lambda args = 'drag': self._update_keybind(args),
        )
        drag_button.pack(side=tk.LEFT, padx=(10,5), pady=5)
        
        raw_button = tk.Button(
            master = toolbar,  text = 'Raw', width= button_width,
            bg = button_background, fg = button_foreground,
            activebackground = activate_background, activeforeground = activate_foreground,
            borderwidth = 0, highlightthickness = 0,
            relief = tk.FLAT, command= lambda args = 'raw': self._update_keybind(args),
        )
        raw_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        all_button = tk.Button(
            master = toolbar,  text = 'All', width= button_width,
            bg = button_background, fg = button_foreground,
            activebackground = activate_background, activeforeground = activate_foreground,
            borderwidth = 0, highlightthickness = 0,
            relief = tk.FLAT, command= lambda args = 'all': self._update_keybind(args),
        )
        all_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        her2_button = tk.Button(
            master = toolbar,  text = 'HER2', width= button_width,
            bg = button_background, fg = button_foreground,
            activebackground = activate_background, activeforeground = activate_foreground,
            borderwidth = 0, highlightthickness = 0,
            relief = tk.FLAT, command= lambda args = 'her2': self._update_keybind(args),
        )
        her2_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        chr17_button = tk.Button(
            master = toolbar,  text = 'Chr17', width= button_width,
            bg = button_background, fg = button_foreground,
            activebackground = activate_background, activeforeground = activate_foreground,
            borderwidth = 0, highlightthickness = 0,
            relief = tk.FLAT, command= lambda args = 'chr17': self._update_keybind(args),
        )
        chr17_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.entry_size = ttk.Entry(master=toolbar, width=5)
        self.entry_size.pack(side=tk.LEFT, padx=(5, 10), pady=5)
        self.entry_size.insert(0, '2')
        
        self.canvas.bind("<Enter>", self.canvas.master.focus_set())
        self.canvas.bind("<Leave>", self.canvas.focus_set())
        
    def input_image_cell(self, cell_id: int, name: str) -> None:
        self.cell_id = cell_id
        self.name = name
        
        self.scale = 1.2
        self.show_raw = False
        self.check_mask()
        
        cell_mask = np.where(self.cells_mask == self.cell_id, 255, 0).astype(np.uint8)
        contours, _ = cv2.findContours(cell_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self.boundary_image = self.raw_image.copy()
        self.boundary_image = cv2.drawContours(self.boundary_image, contours, 0, (255, 255, 0), 1)
        
        M = cv2.moments(contours[0])
        center_x = int(M['m10'] / M['m00'])
        center_y = int(M['m01'] / M['m00'])
        canvas_x = self.canvas.winfo_width() // 2
        canvas_y = self.canvas.winfo_height() // 2
        height, width = self.boundary_image.shape[:2]
        
        self.coordinates = (
            int(canvas_x - (center_x - width // 2) * self.scale),
            int(canvas_y - (center_y - height // 2) * self.scale),
        )
        
        self.update_image()
        self._prep_canvas()
        
    def check_mask(self) -> None:
        try:
            container = self.window.cargo.get_container(self.name)
            self.raw_image = container.get('raw')
        except:
            self.raw_image = np.array(Image.open(self.path))
        
        try: 
            self.her2_mask = cv2.cvtColor(container.get('her2').astype(np.uint8), cv2.COLOR_GRAY2BGR)
            self.her2_mask[np.where((self.her2_mask == [255, 255, 255]).all(axis=2))] = [0, 255, 0]
            self.chr17_mask = cv2.cvtColor(container.get('chr17').astype(np.uint8), cv2.COLOR_GRAY2BGR)
            self.chr17_mask[np.where((self.chr17_mask == [255, 255, 255]).all(axis=2))] = [0, 200, 255]
            self.cells_mask = container.get('cell')
        except:
            return
        
    def update_image(self) -> None:
        if self.show_raw: display_img = self.raw_image.copy()
        else: display_img = self.boundary_image.copy()
        
        if self.show_her2: display_img = cv2.addWeighted(display_img, 1, self.her2_mask, 0.5, 0)
        elif self.show_chr17: display_img = cv2.addWeighted(display_img, 1, self.chr17_mask, 0.5, 0)
        elif self.show_all: display_img = cv2.addWeighted(display_img, 1, (self.her2_mask + self.chr17_mask), 0.5, 0)
        
        height, width = display_img.shape[:2]
        display = cv2.resize(
            display_img, 
            (int(width * self.scale), int(height * self.scale)),
            interpolation=cv2.INTER_AREA
        )
        
        display = Image.fromarray(display, mode= 'RGB')
        self.tk_image = ImageTk.PhotoImage(display)
        
        try:
            self.canvas.itemconfig(self.image_id, image=self.tk_image)
            self.canvas.coords(self.image_id, *self.coordinates)
        except:
            self.image_id = self.canvas.create_image(self.coordinates, image=self.tk_image)
        
    def _update_keybind(self, mode) -> None:
        self.canvas.unbind("<ButtonPress-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.canvas.unbind("<ButtonPress-3>")
        self.canvas.unbind("<B3-Motion>")
        self.canvas.unbind("<ButtonRelease-3>")
        self.canvas.unbind("<MouseWheel>")
        
        match mode:
            case 'drag':
                self.canvas.bind("<ButtonPress-1>", self._start_drag)
                self.canvas.bind("<ButtonPress-3>", self._start_drag)
                self.canvas.bind("<B1-Motion>", self._drag)
                self.canvas.bind("<B3-Motion>", self._drag)
                self.canvas.bind("<ButtonRelease-1>", self._end_drag)
                self.canvas.bind("<ButtonRelease-3>", self._end_drag)
                self.canvas.bind("<MouseWheel>", self._zoom)
                
            case 'raw':
                if self.boundary_image is not None:
                    self.show_raw = not self.show_raw
                
            case 'her2':
                if self.her2_mask is not None:
                    self.show_her2 = not self.show_her2
                    self.show_chr17 = False
                    self.show_all = False
                    
                    self.canvas.bind("<ButtonPress-1>", self._start_draw)
                    self.canvas.bind("<ButtonPress-3>", self._start_erase)
                    self.canvas.bind("<B1-Motion>", self._draw)
                    self.canvas.bind("<B3-Motion>", self._draw)
                    self.canvas.bind("<ButtonRelease-1>", self._end_draw)
                    self.canvas.bind("<ButtonRelease-3>", self._end_draw)
                            
                    self._prep_canvas()
                
            case 'chr17':
                if self.chr17_mask is not None:
                    self.show_chr17 = not self.show_chr17
                    self.show_her2 = False
                    self.show_all = False
                    
                    self.canvas.bind("<ButtonPress-1>", self._start_draw)
                    self.canvas.bind("<ButtonPress-3>", self._start_erase)
                    self.canvas.bind("<B1-Motion>", self._draw)
                    self.canvas.bind("<B3-Motion>", self._draw)
                    self.canvas.bind("<ButtonRelease-1>", self._end_draw)
                    self.canvas.bind("<ButtonRelease-3>", self._end_draw)
                    
                    self._prep_canvas()
                
            case 'all':
                if self.chr17_mask is not None and self.her2_mask is not None:
                    self.show_all = not self.show_all
                    self.show_her2 = False
                    self.show_chr17 = False
            
        self.update_image()
        
    # Drag Button Command
    def _zoom(self, event):
        if event.delta > 0:
            self.scale = self.scale * 1.2
        elif event.delta < 0:
            self.scale = self.scale / 1.2
        
        if self.scale > 2: self.scale = 2
        elif self.scale < 0.6: self.scale = 0.6
        else: self.scale = round(self.scale, 3)
        
        self.coordinates = (event.x, event.y)
        self.update_image()
        
    def _start_drag(self, event):
        self.last_x, self.last_y = event.x, event.y
        
    def _drag(self, event):
        delta_x, delta_y = event.x - self.last_x, event.y - self.last_y
        self.canvas.move(self.image_id, delta_x, delta_y)
        self.last_x, self.last_y = event.x, event.y
        
    def _end_drag(self, event):
        self.coordinates = (event.x, event.y)
    
    # Draw Command
    def _prep_canvas(self):
        if self.show_raw: display_img = self.raw_image.copy()
        else: display_img = self.boundary_image.copy()
        
        height, width = display_img.shape[:2]
        
        if self.show_her2: current_mask = self.her2_mask
        elif self.show_chr17: current_mask = self.chr17_mask
        else: return
            
        self.canvas_base = cv2.resize(
            display_img.copy(), 
            (int(width * self.scale), int(height * self.scale)),
            interpolation=cv2.INTER_AREA
        )
        
        self.canvas_mask = cv2.resize(
            current_mask.copy(),
            (int(width * self.scale), int(height * self.scale)),
            interpolation=cv2.INTER_AREA
        )
        
    def _start_draw(self, _):
        if self.show_her2: self.color = [0, 255, 0]
        else: self.color = [0, 200, 255]
        
        self.size = int(self.entry_size.get())
            
    def _start_erase(self, _):
        self.color = [0, 0, 0]
        
        self.size = int(self.entry_size.get())*2
        
    def _draw(self, event):
        x, y = self.coordinates
        
        height, width = self.canvas_mask.shape[:2]
        
        image_x = int((width // 2) - (x - event.x))
        image_y = int((height // 2) - (y - event.y))
        
        cv2.circle(self.canvas_mask, (image_x, image_y), self.size, self.color, -1)
        
        display_img = cv2.addWeighted(self.canvas_base, 1, self.canvas_mask, 0.5, 0)
        
        display_img = Image.fromarray(display_img, mode= 'RGB')
        self.tk_image = ImageTk.PhotoImage(display_img)
        
        self.canvas.itemconfig(self.image_id, image=self.tk_image)
        self.canvas.coords(self.image_id, *self.coordinates)
    
    def _end_draw(self, _):
        height, width = self.cells_mask.shape[:2]
        
        if self.show_her2:
            self.her2_mask = cv2.resize(
                self.canvas_mask, 
                (int(width), int(height)),
                interpolation=cv2.INTER_NEAREST
            )
            self.her2_mask[self.her2_mask != 0] = 255
            
        elif self.show_chr17:
            self.chr17_mask = cv2.resize(
                self.canvas_mask, 
                (int(width), int(height)),
                interpolation=cv2.INTER_NEAREST,
            )
            self.chr17_mask[self.chr17_mask != 0] = 255
            
        her2_mask = cv2.cvtColor(self.her2_mask, cv2.COLOR_BGR2GRAY)
        chr17_mask = cv2.cvtColor(self.chr17_mask, cv2.COLOR_BGR2GRAY)
        cell_mask = np.where(self.cells_mask == self.cell_id, 1, 0).astype(np.uint8)
        
        results = calculate_cell_score(cell_mask= cell_mask, her2_mask= her2_mask, chr17_mask= chr17_mask)
        
        her2, chr17 = results[1]
        ratio = her2 / chr17 if chr17 != 0 else 0
        
        self.window.third_panel.update_number(ratio, her2, chr17)
        
    def get_cropped_cell(self):
        x1, y1, x2, y2, _, _ = cropping_region(
            input_cell_mask= self.cells_mask,
            id_value= self.cell_id,
            extend= 10,
        )
        
        raw_img = self.boundary_image[y1:y2, x1:x2]
        her2_mask = self.her2_mask[y1:y2, x1:x2]
        chr17_mask = self.chr17_mask[y1:y2, x1:x2]
        
        overlay_img = cv2.addWeighted(raw_img.copy(), 1, her2_mask, 0.5, 0)
        overlay_img = cv2.addWeighted(overlay_img, 1, chr17_mask, 0.5, 0)
        
        raw_img = Image.fromarray(raw_img).convert('RGB')
        overlay_img = Image.fromarray(overlay_img).convert('RGB')
        
        return raw_img, overlay_img