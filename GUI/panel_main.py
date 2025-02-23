import tkinter as tk

from tkinter import messagebox
from ttkthemes import ThemedStyle
from typing import Dict

from GUI.panel_select_image import TopMenu, ImageSelectPanel

from GUI.panel_smi import FirstPanel, SecondPanel, ThirdPanel, FourthPanel
from GUI.panel_auto import ProcessAllPanel
from GUI.panel_train import TrainPanel

from GUI.panel_image_display import ImageDisplayPanel
from GUI.panel_cell_display import CellDisplayPanel, SelectedCellPanel
from GUI.panel_train_display import TrainDisplayPanel

class MainPanel(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Her2DISH')
        self.state('zoomed')
        
        # Set Window style 
        style = ThemedStyle(self)
        style.set_theme('equilux')
        
        # Configure the grid layout for the main window
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.protocol("WM_DELETE_WINDOW", self._check_close)
        
        # Setup Different Frame
        self.frames: Dict[str, tk.Frame] = {}
        
        # Loading Frame
        self.loading_frame = tk.Frame(self, bg="#202020")
        
        loading_screen = LoadingScreen(parent = self.loading_frame, window = self)
        loading_screen.pack(expand=True)
        
        self.loading_frame.grid(row=0, column=0, rowspan=3, columnspan=3, sticky="nsew")
        
        
        # Working Frame
        self.working_frame = tk.Frame(self, bg='#202020')
        
        top_panel = TopMenu(parent = self.working_frame, window = self)
        top_panel.pack(side=tk.TOP, fill=tk.X)
        
        right_panel = tk.Frame(master = self.working_frame)
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)
        selected_cell_frame = SelectedCellPanel(window=self, parent=right_panel)
        selected_cell_frame.grid(row=0, column=0, sticky="nsew")
        for F in (TrainPanel, ProcessAllPanel, FourthPanel, ThirdPanel, SecondPanel, FirstPanel,):
            page_name = F.__name__
            frame = F(window=self, parent=right_panel)
            self.frames[page_name] = frame
            frame.grid(row=1, column=0, sticky="nsew")
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        
        left_panel = tk.Frame(master = self.working_frame)
        left_panel.grid_rowconfigure(0, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)
        for F in (ImageSelectPanel,):
            page_name = F.__name__
            frame = F(window=self, parent=left_panel)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        left_panel.pack(side=tk.LEFT, fill=tk.Y)
        
        middle_panel = tk.Frame(master = self.working_frame)
        middle_panel.grid_rowconfigure(0, weight=1)
        middle_panel.grid_columnconfigure(0, weight=1)
        for F in (TrainDisplayPanel, CellDisplayPanel, ImageDisplayPanel,):
            page_name = F.__name__
            frame = F(window=self, parent=middle_panel)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        middle_panel.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.working_frame.grid(row=0, column=0, rowspan=3, columnspan=3, sticky="nsew")
        
    def show_frame(self, page_name: str) -> None:
        frame = self.frames[page_name]
        frame.tkraise()
    
    def load_start(self) -> None:
        self.loading_frame.tkraise()
    
    def log_info(self, message: str) -> None:
        self.text.config(text=message)
        
    def load_end(self) -> None:
        self.working_frame.tkraise()
        
    def _check_close(self):
        """Callback to handle the close event."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()
            raise SystemExit
        

class LoadingScreen(tk.Frame):
    def __init__(self, parent: tk.Widget, window: tk.Tk, *args, **kwargs) -> None:
        super().__init__(parent, bg="#202020", *args, **kwargs)
        self.current_frame = 0
        
        loading = tk.Label(self, text='Loading...', font='Arial 12', bg='#202020', fg='#FFFFFF')
        loading.pack(pady=10)
        
        self.gif_label = tk.Label(self, bg="#202020")
        self.gif_label.pack()
        
        window.text = tk.Label(self, text='', font='Arial 8', bg='#202020', fg='#FFFFFF')
        window.text.pack(pady=10)
        
        self._load_gif()
        self._animate_gif()
        
    def _load_gif(self) -> None:
        from PIL import Image, ImageTk, ImageSequence
        self.gif_image = Image.open(r".\GUI\loading.gif")
        self.gif_frames = [ImageTk.PhotoImage(frame) for frame in ImageSequence.Iterator(self.gif_image)]
        self.frame_durations = [frame.info['duration'] for frame in ImageSequence.Iterator(self.gif_image)]

    def _animate_gif(self) -> None:
        self.gif_label.configure(image=self.gif_frames[self.current_frame])
        duration = self.frame_durations[self.current_frame]
        self.current_frame = (self.current_frame + 1) % len(self.gif_frames)
        self.after(duration, self._animate_gif)