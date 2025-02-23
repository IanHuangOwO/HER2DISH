import tkinter as tk
import numpy as np
import cv2

from pathlib import Path
from PIL import Image, ImageTk


class ImageDisplayPanel(tk.Frame):
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
        window.image_display = self
        
        self.window = window
        
        self.image_id = None
        self.raw_image = None
        self.her2_mask = None
        self.chr17_mask = None
        
        # Toolbar Setup
        toolbar = tk.Frame(self, bg = '#303030')
        toolbar.pack(side = tk.TOP)
        
        # Canvas Setup
        self.canvas = tk.Canvas(master = self,  bg = '#212121', highlightthickness = 0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Control Setup
        self.canvas.bind("<ButtonPress-1>", self._start_drag)
        self.canvas.bind("<ButtonPress-3>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<B3-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._end_drag)
        self.canvas.bind("<ButtonRelease-3>", self._end_drag)
        self.canvas.bind("<MouseWheel>", self._zoom)
        
        # Button Setup    
        reset_button = tk.Button(
            master = toolbar,  text = 'Reset', width= button_width,
            bg = button_background, fg = button_foreground,
            activebackground = activate_background, activeforeground = activate_foreground,
            borderwidth = 0, highlightthickness = 0,
            relief = tk.FLAT,
            command= lambda args = 'reset': self._update_keybind(args),
        )
        reset_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        all_button = tk.Button(
            master = toolbar,  text = 'All', width= button_width,
            bg = button_background, fg = button_foreground,
            activebackground = activate_background, activeforeground = activate_foreground,
            borderwidth = 0, highlightthickness = 0,
            relief = tk.FLAT,
            command= lambda args = 'all': self._update_keybind(args),
        )
        all_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        her2_button = tk.Button(
            master = toolbar,  text = 'HER2', width= button_width,
            bg = button_background, fg = button_foreground,
            activebackground = activate_background, activeforeground = activate_foreground,
            borderwidth = 0, highlightthickness = 0,
            relief = tk.FLAT,
            command= lambda args = 'her2': self._update_keybind(args),
        )
        her2_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        chr17_button = tk.Button(
            master = toolbar,  text = 'Chr17', width= button_width,
            bg = button_background, fg = button_foreground,
            activebackground = activate_background, activeforeground = activate_foreground,
            borderwidth = 0, highlightthickness = 0,
            relief = tk.FLAT,
            command= lambda args = 'chr17': self._update_keybind(args),
        )
        chr17_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.canvas.bind("<Enter>", self.canvas.focus_set())
        self.canvas.bind("<Leave>", self.canvas.focus_set())
        
    def input_image_path(self, path: str) -> None:
        self.path = Path(path)
        self.name = self.path.stem
        
        self.show_all = False
        self.show_her2 = False
        self.show_chr17 = False
        
        self.scale = 0.6
        self._check_mask()
        
        self.coordinates = (
            int(self.canvas.winfo_width() // 2), 
            int(self.canvas.winfo_height() // 2)
        )
        
        self._update_image()
        
    def _check_mask(self) -> None:
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
        except:
            return
        
    def _update_image(self) -> None:
        self.display_img = self.raw_image
        
        if self.show_her2: display_img = cv2.addWeighted(self.display_img, 1, self.her2_mask, 0.5, 0)
        elif self.show_chr17: display_img = cv2.addWeighted(self.display_img, 1, self.chr17_mask, 0.5, 0)
        elif self.show_all: display_img = cv2.addWeighted(self.display_img, 1, (self.her2_mask + self.chr17_mask), 0.5, 0)
        else: display_img = self.display_img
        
        height, width = display_img.shape[:2]
        display = cv2.resize(
            display_img, 
            (int(width * self.scale), int(height * self.scale)),
            interpolation=cv2.INTER_AREA
        )
        
        display = Image.fromarray(display, mode= 'RGB')
        self.tk_image = ImageTk.PhotoImage(display)
        
        if self.image_id:
            self.canvas.itemconfig(self.image_id, image=self.tk_image)
            self.canvas.coords(self.image_id, *self.coordinates)
        else:
            self.image_id = self.canvas.create_image(self.coordinates, image=self.tk_image)
        
    def _update_keybind(self, mode) -> None:
        match mode:
            case 'reset':
                self.coordinates = (int(self.canvas.winfo_width() // 2), int(self.canvas.winfo_height() // 2))
                self.scale = 0.6
                
            case 'her2':
                if self.her2_mask is not None:
                    self.show_her2 = not self.show_her2
                    self.show_chr17 = False
                    self.show_all = False
                
            case 'chr17':
                if self.chr17_mask is not None:
                    self.show_chr17 = not self.show_chr17
                    self.show_her2 = False
                    self.show_all = False
                
            case 'all':
                if self.chr17_mask is not None and self.her2_mask is not None:
                    self.show_all = not self.show_all
                    self.show_her2 = False
                    self.show_chr17 = False
            
        self._update_image()
        
    def _zoom(self, event):
        if event.delta > 0: self.scale = self.scale * 1.2
        elif event.delta < 0: self.scale = self.scale / 1.2
        
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