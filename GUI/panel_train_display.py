import tkinter as tk
import numpy as np
import cv2

from tkinter import ttk
from PIL import Image, ImageTk

class TrainDisplayPanel(tk.Frame):
    def __init__(
        self, 
        parent: tk.Widget,
        window: tk.Tk,
        button_width: int = 6,
        button_background: str = '#505050',
        button_foreground: str = '#FFFFFF',
        activate_background: str = '#3C3B3B',
        activate_foreground: str = '#FFFFFF',
    ) -> None:
        super().__init__(parent, bg = '#202020')
        window.train_display = self
        
        self.image_id = None
        self.foreground_mask = None
        self.background_mask = None
        
        self.show_all = False
        self.show_foreground = False
        self.show_background = False
        
        # Toolbar Setup
        toolbar = tk.Frame(self, bg = '#303030')
        toolbar.pack(side = tk.TOP)
        
        # Canvas Setup
        self.canvas = tk.Canvas(master = self, bg = '#212121', highlightthickness = 0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Button Setup
        drag_button = tk.Button(
            master = toolbar,
            text = 'Drag', width= button_width,
            bg = button_background, fg = button_foreground,
            activebackground = activate_background, activeforeground = activate_foreground,
            borderwidth = 0, highlightthickness = 0,
            relief = tk.FLAT, command= lambda args = 'drag': self._update_keybind(args),
        )
        drag_button.pack(side=tk.LEFT, padx=(10,5), pady=5)
        
        reset_button = tk.Button(
            master = toolbar, 
            text = 'Reset', width= button_width,
            bg = button_background, fg = button_foreground,
            activebackground = activate_background, activeforeground = activate_foreground,
            borderwidth = 0, highlightthickness = 0,
            relief = tk.FLAT, command= lambda args = 'reset': self._update_keybind(args),
        )
        reset_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        result_button = tk.Button(
            master = toolbar,
            text = 'Result', width= button_width + 4,
            bg = button_background, fg = button_foreground,
            activebackground = activate_background, activeforeground = activate_foreground,
            borderwidth = 0, highlightthickness = 0,
            relief = tk.FLAT, command= lambda args = 'all': self._update_keybind(args),
        )
        result_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        foreground_button = tk.Button(
            master = toolbar,
            text = 'Foreground', width= button_width + 4,
            bg = button_background, fg = button_foreground,
            activebackground = activate_background, activeforeground = activate_foreground,
            borderwidth = 0, highlightthickness = 0,
            relief = tk.FLAT, command= lambda args = 'foreground': self._update_keybind(args),
        )
        foreground_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        background_button = tk.Button(
            master = toolbar, 
            text = 'Background', width= button_width + 4,
            bg = button_background, fg = button_foreground,
            activebackground = activate_background, activeforeground = activate_foreground,
            borderwidth = 0, highlightthickness = 0,
            relief = tk.FLAT, command= lambda args = 'background': self._update_keybind(args),
        )
        background_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.entry_size = ttk.Entry(master=toolbar,  width=5)
        self.entry_size.pack(side=tk.LEFT, padx=(5, 10), pady=5)
        self.entry_size.insert(0, '2')
        
        self.canvas.bind("<Enter>", self.canvas.master.focus_set())
        self.canvas.bind("<Leave>", self.canvas.focus_set())
        
    def input_image_path(self, path: str) -> None:
        self.scale = 0.2
        self.show_foreground = False
        self.show_background = False
        self.show_all = False
        
        self.coordinates = (int(self.canvas.winfo_width() // 2), int(self.canvas.winfo_height() // 2))
        
        self.display_img = np.array(Image.open(path))
        self.foreground_mask = np.zeros_like(self.display_img)
        self.background_mask = np.zeros_like(self.display_img)
        self.resulting_mask = np.zeros_like(self.display_img)
        
        self._update_image()
        
    def _update_image(self) -> None:
        if self.show_foreground: display_img = cv2.addWeighted(self.display_img, 1, self.foreground_mask, 0.5, 0)
        elif self.show_background: display_img = cv2.addWeighted(self.display_img, 1, self.background_mask, 0.5, 0)
        elif self.show_all: display_img = cv2.addWeighted(self.display_img, 1, self.resulting_mask, 0.5, 0)
        else: display_img = self.display_img
        
        height, width = display_img.shape[:2]
        display = cv2.resize(display_img, (int(width * self.scale), int(height * self.scale)), interpolation=cv2.INTER_NEAREST)
        
        display = Image.fromarray(display, mode= 'RGB')
        self.tk_image = ImageTk.PhotoImage(display)
        
        if self.image_id:
            self.canvas.itemconfig(self.image_id, image=self.tk_image)
            self.canvas.coords(self.image_id, *self.coordinates)
        else:
            self.image_id = self.canvas.create_image(self.coordinates, image=self.tk_image)
        
    def _update_keybind(self, mode) -> None:
        """Update canvas keybindings based on the selected mode."""
        
        # Unbind all events before updating
        for event in [
            "<ButtonPress-1>", "<B1-Motion>", "<ButtonRelease-1>",
            "<ButtonPress-3>", "<B3-Motion>", "<ButtonRelease-3>",
            "<MouseWheel>"
        ]:
            self.canvas.unbind(event)
        
        # Common bindings for dragging and zooming
        def bind_dragging():
            self.canvas.bind("<ButtonPress-1>", self._start_drag)
            self.canvas.bind("<ButtonPress-3>", self._start_drag)
            self.canvas.bind("<B1-Motion>", self._drag)
            self.canvas.bind("<B3-Motion>", self._drag)
            self.canvas.bind("<ButtonRelease-1>", self._end_drag)
            self.canvas.bind("<ButtonRelease-3>", self._end_drag)
            self.canvas.bind("<MouseWheel>", self._zoom)

        # Common bindings for drawing
        def bind_drawing():
            self.canvas.bind("<ButtonPress-1>", self._start_draw)
            self.canvas.bind("<ButtonPress-3>", self._start_erase)
            self.canvas.bind("<B1-Motion>", self._draw)
            self.canvas.bind("<B3-Motion>", self._draw)
            self.canvas.bind("<ButtonRelease-1>", self._end_draw)
            self.canvas.bind("<ButtonRelease-3>", self._end_draw)
        
        # Handle mode-specific logic
        match mode:
            case "drag" | "reset" | "all":
                if mode == "reset":
                    self.coordinates = (self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2)
                    self.scale = 0.2
                if mode == "all":
                    self.show_all = not self.show_all
                    self.show_foreground = self.show_background = False
                bind_dragging()
            
            case "foreground":
                self.show_foreground = not self.show_foreground
                self.show_background = self.show_all = False
                self._prep_canvas()
                bind_drawing()

            case "background":
                self.show_background = not self.show_background
                self.show_foreground = self.show_all = False
                self._prep_canvas()
                bind_drawing()

        self._update_image()
        
    # Drag Button Command
    def _zoom(self, event):
        if event.delta > 0:
            self.scale = self.scale * 1.2
        elif event.delta < 0:
            self.scale = self.scale / 1.2
        
        if self.scale > 2.5: self.scale = 2.5
        elif self.scale < 0.2: self.scale = 0.2
        else: self.scale = round(self.scale, 3)
        
        self.coordinates = (event.x, event.y)
        self._update_image()
        
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
        height, width = self.display_img.shape[:2]
        
        if self.show_foreground: current_mask = self.foreground_mask
        elif self.show_background: current_mask = self.background_mask
            
        self.canvas_base = cv2.resize(self.display_img.copy(), (int(width * self.scale), int(height * self.scale)), interpolation=cv2.INTER_AREA)
        self.canvas_mask = cv2.resize(current_mask.copy(),(int(width * self.scale), int(height * self.scale)),interpolation=cv2.INTER_AREA)
        
    def _start_draw(self, _):
        if self.show_foreground: self.color = [0, 255, 0]
        else: self.color = [0, 200, 255]
        self.size = int(self.entry_size.get())
            
    def _start_erase(self, _):
        self.color = [0, 0, 0]
        self.size = int(self.entry_size.get()) * 2
        
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
        height, width = self.display_img.shape[:2]
        
        if self.show_foreground:
            self.foreground_mask = cv2.resize(self.canvas_mask, (int(width), int(height)), interpolation=cv2.INTER_NEAREST)
            
        elif self.show_background:
            self.background_mask = cv2.resize(self.canvas_mask, (int(width), int(height)), interpolation=cv2.INTER_NEAREST)