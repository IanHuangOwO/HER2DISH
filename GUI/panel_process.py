import os
import tkinter as tk
import threading

from pathlib import Path
from tkinter import ttk, messagebox, filedialog
from typing import Dict

from process import *
from tools import *


class ProcessImagePanel(tk.Frame):
    def __init__(self, parent: tk.Widget, window: tk.Tk, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.frames: Dict[str, tk.Frame] = {}
        
        self.grid_rowconfigure(1, weight=1)
        
        selected_cell_frame = SelectedCellPanel(
            parent=self,
            window=window,
        )
        selected_cell_frame.grid(row=0, column=0, sticky="nsew")
        
        # Right Sub Panel
        for F in (PreprocessPanel, FourthPanel, ThirdPanel, SecondPanel, FirstPanel,):
            page_name = F.__name__
            frame = F(parent=self, window=window)
            self.frames[page_name] = frame
            frame.grid(row=1, column=0, sticky="nsew")
    
    def show_frame(self, page_name: str) -> None:
        frame = self.frames[page_name]
        frame.tkraise()
        
        
class SelectedCellPanel(tk.Frame):
    def __init__(
        self, parent, window, 
        rows=10, cols=4, 
        block_size=(70, 70), 
        *args, **kwargs):
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
            text='Selected Cell',
            bg='#292929',
            fg='#FFFFFF',
            anchor='center',
            font='Arial 12 bold'
        )
        title.pack(fill=tk.X, ipady=5)
        
        self.canvas = tk.Canvas(
            master=self, 
            bg='#303030', 
            width=250,
            height=300,
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

        # tk.Label(button_frame, text=label_text, font=("Arial", 5), fg="#FFFFFF", bg='#303030').pack(side="bottom")
        
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
        
        
class FirstPanel(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        window: tk.Tk,
        frame_font: str = 'Arial 12 bold',
        frame_background: str = '#333333',
        button_width: int = 30,
        button_height: int = 3,
        button_font: str = 'Arial 12 bold',
        button_background: str = '#454545',
        button_foreground: str = '#FFFFFF',
        active_background: str = '#3C3B3B',
        active_foreground: str = '#FFFFFF',
        *args,
        **kwargs,
    ) -> None:
        super().__init__(master=parent, bg=frame_background, *args, **kwargs)
        
        self.parent: tk.Widget = parent
        self.window: tk.Tk = window
        
        self.grid_columnconfigure(0, weight=1)

        # Progress Label
        progress_label = tk.Label(
            master=self,
            text='Progress 1 of 3', 
            bg='#292929',
            fg='#FFFFFF',
            font=frame_font,
            width=25,
            anchor='center',
        )
        progress_label.pack(side=tk.TOP, fill=tk.X, ipady=5)
        
        # Process Button
        button_frame = tk.Frame(
            master=self,
            bg='#333333',
        )
        button_frame.pack(expand=True)
        
        # Semi-Auto Button
        smei_button = tk.Button(
            master=button_frame,
            text='Semi-Auto Quantification',
            font=button_font,
            bg=button_background,
            fg=button_foreground,
            activebackground=active_background,
            activeforeground=active_foreground,
            width=button_width,
            height=button_height,
            borderwidth=0, 
            highlightthickness=0,
            command=lambda args='SMI': self.process(args),
        )
        smei_button.grid(row=1, column=0, pady=20)

        # Auto All Button
        auto_all_button = tk.Button(
            master=button_frame,
            text='Auto All Quantification',
            font=button_font,
            bg=button_background,
            fg=button_foreground,
            activebackground=active_background,
            activeforeground=active_foreground,
            width=button_width,
            height=button_height,
            borderwidth=0, 
            highlightthickness=0,
            command=lambda args='ALL': self.process(args),
        )
        auto_all_button.grid(row=2, column=0, pady=20)
        
        # Anaylsis Preperation
        preperation_button = tk.Button(
            master=button_frame,
            text='Pre-run Analysis',
            font=button_font,
            bg=button_background,
            fg=button_foreground,
            activebackground=active_background,
            activeforeground=active_foreground,
            width=button_width,
            height=button_height,
            borderwidth=0, 
            highlightthickness=0,
            command=lambda args='PREP': self.process(args),
        )
        preperation_button.grid(row=3, column=0, pady=20)
        
        # # Train Classifier
        # train_classifier_button = tk.Button(
        #     master=button_frame,
        #     text='Train Classifier Model',
        #     font=button_font,
        #     bg=button_background,
        #     fg=button_foreground,
        #     activebackground=active_background,
        #     activeforeground=active_foreground,
        #     width=button_width,
        #     height=button_height,
        #     borderwidth=0, 
        #     highlightthickness=0,
        #     command=lambda args='TRAIN': self.process(args),
        # )
        # train_classifier_button.grid(row=4, column=0, pady=20)
        
        # Anaylsis Preperation
        reset_button = tk.Button(
            master=button_frame,
            text='Reset Analysis',
            font=button_font,
            bg=button_background,
            fg=button_foreground,
            activebackground=active_background,
            activeforeground=active_foreground,
            width=button_width,
            height=button_height,
            borderwidth=0, 
            highlightthickness=0,
            command=lambda args='RESET': self.process(args),
        )
        reset_button.grid(row=4, column=0, pady=20)
        
    def process(self, name: str) -> None: 
        match name:
            case 'SMI':
                self.window.loading_screen.show()
                threading.Thread(target=self.SMI).start()
            
            case 'ALL':
                self.window.loading_screen.show()
                self.window.status = name
                threading.Thread(target=self.All).start()
            
            case 'PREP':
                self.window.loading_screen.show()
                self.window.status = name
                threading.Thread(target=self.All).start()
            
            case 'TRAIN':
                pass
            
            case 'RESET':
                self.window.loading_screen.show()
                threading.Thread(target=self.RESET).start()
            
    def SMI(self) -> None:
        if self.window.selected_path == None:
            self.window.selected_path = Path(filedialog.askdirectory())
            self.window.select_image.update_roots(
                name= 'select_image_treeview', 
                path= self.window.selected_path
            )
        
        self.window.cargo = load_cargo(
            input_path= self.window.selected_path,
            output_path= self.window.selected_path.parent.absolute(),
        )
        self.window.select_image.update_roots(
            name= 'current_image_treeview', 
            path= self.window.cargo.output_path,
        )
        self.parent.show_frame('SecondPanel')
        self.window.loading_screen.hide()
        
    def All(self) -> None:
        input_path = filedialog.askdirectory()
        self.window.select_image.update_roots(
            name= 'select_image_treeview',
            path= Path(input_path),
        )
        
        self.parent.show_frame('PreprocessPanel')
        self.window.loading_screen.hide()
        
    def RESET(self) -> None:
        
        self.window.select_image.update_roots(name= 'select_image_treeview')
        self.window.select_image.update_roots(name= 'current_image_treeview')
        self.window.image_display.canvas.delete(self.window.image_display.image_id)
        
        self.window.loading_screen.hide()
        
class SecondPanel(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        window: tk.Tk,
        frame_background: str = '#333333',
        label_font: str = 'Arial 12',
        label_background: str = '#333333',
        label_foreground: str = '#FFFFFF',
        button_background: str = '#454545',
        button_foreground: str = '#FFFFFF',
        active_background: str = '#3C3B3B',
        active_foreground: str = '#FFFFFF',
        *args,
        **kwargs,
    ) -> None:
        super().__init__(master=parent, bg=frame_background, *args, **kwargs)
        
        self.parent: tk.Widget = parent
        self.window: tk.Tk = window
        
        # Progress Label
        progress_label = tk.Label(
            master=self,
            text='Progress 2 of 3', 
            bg='#292929',
            fg='#FFFFFF',
            font='Arial 12 bold',
            width=25,
            anchor='center',
        )
        progress_label.pack(side=tk.TOP, fill=tk.X, ipady=5)
        
        # Parameter Frame
        entry_frame = tk.Frame(
            master=self,
            bg='#333333',
        )
        entry_frame.pack(expand=True)
        
        # HER2 Model Label
        HER2_image_label = tk.Label(
            master=entry_frame,
            text='HER2 MODEL',
            font=label_font,
            bg=label_background,
            fg=label_foreground,
            width=25,
            anchor='center',
        )
        HER2_image_label.pack(pady=(40, 10))
        
        # HER2 Model Option Menu
        her2_classifier_path = r'.\classifier\HER2'
        self.her2_classifier_dict: Dict[str, str] = {
            os.path.basename(path): os.path.join(her2_classifier_path, path)
            for path in os.listdir(her2_classifier_path)
            if path.endswith('.joblib')
        }
        self.her2_model_path = tk.StringVar()
        options = [name.center(15) for name in self.her2_classifier_dict]
        HER2_model_menu = ttk.OptionMenu(
            entry_frame,
            self.her2_model_path,
            options[0],
            *options,
        )
        HER2_model_menu.pack()
        
        # CHR17 Model Label
        CHR17_options_label = tk.Label(
            master=entry_frame,
            text='CHR17 MODEL',
            font=label_font,
            bg=label_background,
            fg=label_foreground,
            width=25,
            anchor='center',
        )
        CHR17_options_label.pack(pady=(40, 10))
        
        # CHR17 Model Option Menu
        chr17_classifier_path = r'.\classifier\CHR17'
        self.chr17_classifier_dict: Dict[str, str] = {
            os.path.basename(path): os.path.join(chr17_classifier_path, path)
            for path in os.listdir(chr17_classifier_path)
            if path.endswith('.joblib')
        }
        self.chr17_model_path = tk.StringVar()
        options = [name.center(15) for name in self.chr17_classifier_dict]
        CHR17_model_menu = ttk.OptionMenu(
            entry_frame,
            self.chr17_model_path,
            options[0],
            *options,
        )
        CHR17_model_menu.pack()
        
        # Model Type Label
        model_type_label = tk.Label(
            master=entry_frame,
            text='MODEL TYPE',
            font=label_font,
            bg=label_background,
            fg=label_foreground,
            width=22,
            anchor='center',
        )
        model_type_label.pack(pady=(40, 10))
        
        # Model Type Option Menu
        self.model_type = tk.StringVar()
        options = ["StarDist".center(15), "Cellpose".center(15)]
        model_type_menu = ttk.OptionMenu(
            entry_frame,
            self.model_type,
            options[0],
            *options,
        )
        model_type_menu.pack()
        
        # Step Button
        previous_step_button = tk.Button(
            master=self,
            text='Previous Step',
            bg=button_background,
            fg=button_foreground,
            activebackground=active_background,
            activeforeground=active_foreground,
            borderwidth=0, 
            highlightthickness=0,
            command=self._show_previous,
        )
        previous_step_button.pack(side=tk.BOTTOM, fill=tk.X)
        next_step_button = tk.Button(
            master=self,
            text='Next Step',
            bg=button_background,
            fg=button_foreground,
            activebackground=active_background,
            activeforeground=active_foreground,
            borderwidth=0, 
            highlightthickness=0,
            command=self._show_next,
        )
        next_step_button.pack(side=tk.BOTTOM, fill=tk.X, pady=2)
    
    def _show_next(self) -> None:
        self.window.loading_screen.show()
        threading.Thread(target=self._process).start()
    
    def _process(self) -> None:
        process_parallel(
            cargo = self.window.cargo,
            her2_classifier_path = self.her2_classifier_dict[self.her2_model_path.get().strip()], 
            chr17_classifier_path = self.chr17_classifier_dict[self.chr17_model_path.get().strip()],
            model_type= self.model_type.get().strip(),
        )
        
        if len(self.window.cargo.final_cell_score) > 1: 
            for cell_name, _, _ in self.window.cargo.final_cell_score:
                for name, id, ratio, her2, chr17, _ in self.window.cargo.all_cell_score:
                    current_cell_name = f'{name}_Cell-{str(id).zfill(3)}'
                    if cell_name == current_cell_name:
                        self.window.cell_treeview.insert('', 'end', text=f'{name}_Cell-{str(id).zfill(3)}', values=[name, id, ratio, her2, chr17])
        
        for name, id, ratio, her2, chr17, _ in self.window.cargo.all_cell_score[:50]:
            self.window.cell_treeview.insert('', 'end', text=f'{name}_Cell-{str(id).zfill(3)}', values=[name, id, ratio, her2, chr17])
                
        first_item = self.window.cell_treeview.get_children()[0]
        self.window.cell_treeview.selection_set(first_item)
        self.window.cell_treeview.see(first_item)
        
        self.parent.show_frame('ThirdPanel')
        self.window.loading_screen.hide()
        
    def _show_previous(self) -> None:
        self.parent.show_frame('FirstPanel')
        
    
class ThirdPanel(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        window: tk.Tk,
        label_background: str = '#333333',
        label_foreground: str = '#FFFFFF',
        button_background: str = '#454545',
        button_foreground: str = '#FFFFFF',
        active_background: str = '#3C3B3B',
        active_foreground: str = '#FFFFFF',
        *args,
        **kwargs,
    ) -> None:
        super().__init__(parent, bg='#333333', *args, **kwargs)
        self.parent = parent
        self.window = window
        
        self.required_cell = 20
        self.last_cell = 50
        self.previous_progress = 0
        self.final_cell_score = {}
        self.final_cell_image = {}
        
        # Progress Label
        progress_label = tk.Label(master= self, text= 'Progress 3 of 3',  bg= '#292929', fg= '#FFFFFF', font= 'Arial 12 bold', width= 25, anchor= 'center',)
        progress_label.pack(side=tk.TOP, fill=tk.X, ipady=5)
        
        #Cell Status Label
        cell_frame = tk.Frame(master = self,bg = '#333333')
        cell_frame.pack(side=tk.TOP, expand= True)
        
        cell_label = tk.Label(master= cell_frame, text= 'Cell Status', bg= '#303030', fg= '#FFFFFF', font= 'Arial 12 bold', width= 40,anchor= 'center')
        cell_label.grid(row=1, column=0, columnspan=6, sticky='ew', ipady= 5)
        
        cell_her2 = ttk.Label(master = cell_frame,text = 'Current HER2:', background = label_background, foreground = label_foreground)
        cell_her2.grid(row=2, column=0, pady=(8,3), sticky='e')
        self.window.cell_her2 = ttk.Entry(master = cell_frame, width = 5)
        self.window.cell_her2.insert(0, '0')
        self.window.cell_her2.grid(row=2, column=1, pady=(8,3), sticky='w')
        
        cell_chr17 = ttk.Label(master = cell_frame, text = 'Current Chr17:', background = label_background, foreground = label_foreground)
        cell_chr17.grid(row=3, column=0, pady=3, sticky='e')
        self.window.cell_chr17 = ttk.Entry(master = cell_frame, width=5)
        self.window.cell_chr17.insert(0, '0')
        self.window.cell_chr17.grid(row=3, column=1, pady=3, sticky='w')
        
        cell_ratio = ttk.Label(master = cell_frame, text='Current Ratio:', background = label_background, foreground = label_foreground)
        cell_ratio.grid(row=4, column=0, pady=3, sticky='e')
        self.window.cell_ratio = ttk.Entry(master = cell_frame, width=5)
        self.window.cell_ratio.insert(0, '0')
        self.window.cell_ratio.grid(row=4, column=1, pady=3, sticky='w')
        
        selected_her2 = ttk.Label(master = cell_frame, text='Total HER2:', background = label_background, foreground = label_foreground)
        selected_her2.grid(row=2, column=2, pady=(8,3), sticky='e')
        self.selected_her2 = ttk.Entry(master = cell_frame, width=5)
        self.selected_her2.insert(0, '0')
        self.selected_her2.grid(row=2, column=3, pady=(8,3), sticky='w')
        
        selected_chr17 = ttk.Label(master = cell_frame, text='Total Chr17:', background = label_background, foreground = label_foreground)
        selected_chr17.grid(row=3, column=2, pady=3, sticky='e')
        self.selected_chr17 = ttk.Entry(master = cell_frame, width=5)
        self.selected_chr17.insert(0, '0')
        self.selected_chr17.grid(row=3, column=3, pady=3, sticky='w')
        
        selected_cell = ttk.Label(master = cell_frame, text='Total Cell:', background = label_background, foreground = label_foreground)
        selected_cell.grid(row=4, column=2, pady=3, sticky='e')
        self.selected_cell = ttk.Entry(master = cell_frame, width=5)
        self.selected_cell.insert(0, '0')
        self.selected_cell.grid(row=4, column=3, pady=3, sticky='w')
        
        avg_her2 = ttk.Label(master = cell_frame, text='Avg HER2:', background = label_background, foreground = label_foreground)
        avg_her2.grid(row=2, column=4, pady=(8,3), sticky='e')
        self.avg_her2 = ttk.Entry(master = cell_frame, width=5)
        self.avg_her2.insert(0, '0')
        self.avg_her2.grid(row=2, column=5, pady=(8,3), sticky='w')
        
        avg_chr17 = ttk.Label(master = cell_frame, text='Avg Chr17:', background = label_background, foreground = label_foreground)
        avg_chr17.grid(row=3, column=4, pady=3, sticky='e')
        self.avg_chr17 = ttk.Entry(master = cell_frame, width=5)
        self.avg_chr17.insert(0, '0')
        self.avg_chr17.grid(row=3, column=5, pady=3, sticky='w')
        
        avg_ratio = ttk.Label(master = cell_frame, text='HER2/Chr17:', background = label_background, foreground = label_foreground,)
        avg_ratio.grid(row=4, column=4, pady=3, sticky='e')
        self.avg_ratio = ttk.Entry(master = cell_frame, width=5)
        self.avg_ratio.insert(0, '0')
        self.avg_ratio.grid(row=4, column=5, pady=3, sticky='w')
        
        # Operation Buttons
        button_add = tk.Button(master = cell_frame, text = 'Add', font= 'Arial 10', width = 35, bg = button_background, fg = button_foreground, activebackground = active_background, activeforeground = active_foreground, borderwidth=0, highlightthickness=0, command = lambda: self._add_cell())
        button_add.grid(row=5, column=0, columnspan=6, padx=2, pady=(5,2))
        button_next = tk.Button(master = cell_frame, text = 'Next', font = 'Arial 10', width = 35, bg = button_background, fg = button_foreground, activebackground = active_background, activeforeground = active_foreground, borderwidth=0,  highlightthickness=0, command= lambda: self._next_cell())
        button_next.grid(row=6, column=0, columnspan=6, padx=2, pady=2)
        bttton_delete = tk.Button(master =  cell_frame, text = 'Delete', font = 'Arial 10', width = 35,  bg= button_background, fg= button_foreground, activebackground= active_background, activeforeground= active_foreground, borderwidth=0,  highlightthickness=0, command= lambda: self._delete_cell())
        bttton_delete.grid(row=7, column=0, columnspan=6, padx=2, pady=(2,7))
        
        # Cell List
        cell_label = tk.Label(master= cell_frame,  text= 'Cell List',  bg= '#303030',fg= '#FFFFFF', font= 'Arial 12 bold',anchor= 'center')
        cell_label.grid(row=8, column=0, columnspan=6, ipady=5, sticky='ew')
        cell_treeview = ttk.Treeview(
            master= cell_frame, height = 15, selectmode = "browse",
            columns = ('id', 'image', 'ratio', 'her2', 'chr17'),
            displaycolumns = ('ratio', 'her2', 'chr17'),
        )
        cell_treeview.grid(row=9, column=0, columnspan=6, sticky='ew')
        
        cell_treeview.bind(sequence= "<<TreeviewSelect>>", func= self._treeview_select)
        cell_treeview.heading(column="#0", text='Cell ID', anchor='center')
        cell_treeview.heading(column='ratio', text='Ratio', anchor='center')
        cell_treeview.heading(column='her2', text='HER2', anchor='center')
        cell_treeview.heading(column='chr17', text='Chr17', anchor='center')
        cell_treeview.column(column='#0', width=200, stretch=tk.NO)
        cell_treeview.column(column='ratio', width=70, stretch=tk.NO)
        cell_treeview.column(column='her2', width=70, stretch=tk.NO)
        cell_treeview.column(column='chr17', width=70, stretch=tk.NO)
        
        self.window.cell_treeview = cell_treeview
        
        # Step Button
        previous_step_button = tk.Button( master= self, text= 'Previous Step', bg= button_background, fg= button_foreground, activebackground= active_background, activeforeground= active_foreground, borderwidth=0, highlightthickness=0,command= lambda: self._show_previous(),)
        previous_step_button.pack(side=tk.BOTTOM, fill=tk.X)
        next_step_button = tk.Button( master= self, text= 'Next Step', bg= button_background, fg= button_foreground, activebackground= active_background, activeforeground= active_foreground, borderwidth=0, highlightthickness=0, command= lambda: self._show_next(),)
        next_step_button.pack(side=tk.BOTTOM, fill=tk.X, pady=2)
        
    def _treeview_select(self, event):
        tree = event.widget
        selected_item = tree.selection()
        if selected_item:
            name, cell_id, ratio, her2, chr17 = tree.item(selected_item[0])['values']
            self.window.image_display.input_image_cell(cell_id, name)
            self._update_number(ratio, her2, chr17)
            
        if len(self.window.cargo.final_cell_score) > 20:
            self.required_cell = 40
                    
        if self.previous_progress < len(self.window.cargo.final_cell_score):
            self.previous_progress += 1
            self._add_cell()
            
    def _update_number(self, ratio = 0, her2 = 0, chr17 = 0) -> None:
        self.window.cell_her2.delete(0, tk.END)
        self.window.cell_her2.insert(0, str(int(float(her2))))
        
        self.window.cell_chr17.delete(0, tk.END)
        self.window.cell_chr17.insert(0, str(int(float(chr17))))
        
        self.window.cell_ratio.delete(0, tk.END)
        self.window.cell_ratio.insert(0, str(float(ratio)))
    
    def _update_total(self) -> None:
        total_her2, total_chr17, total_cell = 0, 0, 0
        for her2, chr17 in self.final_cell_score.values():
            total_her2 += her2
            total_chr17 += chr17
            total_cell += 1
        
        self.selected_her2.delete(0, tk.END)
        self.selected_her2.insert(0, str(total_her2))
        
        self.selected_chr17.delete(0, tk.END)
        self.selected_chr17.insert(0, str(total_chr17))
        
        self.selected_cell.delete(0, tk.END)
        self.selected_cell.insert(0, str(total_cell))
        
        self.avg_her2.delete(0, tk.END)
        avg_her2 = round(total_her2 / total_cell, 3) if total_cell != 0 else float(0)
        self.avg_her2.insert(0, str(avg_her2))
        
        self.avg_chr17.delete(0, tk.END)
        avg_chr17 = round(total_chr17 / total_cell, 3) if total_cell != 0 else float(0)
        self.avg_chr17.insert(0, str(avg_chr17))
        
        self.avg_ratio.delete(0, tk.END)
        avg_ratio = round(total_her2 / total_chr17, 3) if total_chr17 != 0 else float(0)
        self.avg_ratio.insert(0, str(avg_ratio))
            
    def _next_cell(self):
        selected_items = self.window.cell_treeview.selection()
        
        current_item = selected_items[0] if selected_items else None
        next_item = self.window.cell_treeview.next(current_item) if current_item else self.window.cell_treeview.get_children()[0]
        
        while next_item:
            cell_name = self.window.cell_treeview.item(next_item)['text']
            
            if cell_name in self.final_cell_score:
                next_item = self.window.cell_treeview.next(next_item)
            else:
                if current_item:
                    self.window.cell_treeview.selection_remove(current_item)
                self.window.cell_treeview.selection_set(next_item)
                self.window.cell_treeview.see(next_item)
                
                if self.last_cell >= len(self.window.cargo.all_cell_score):
                    break
                
                name, id, ratio, her2, chr17, _ = self.window.cargo.all_cell_score[self.last_cell]
                self.window.cell_treeview.insert('', 'end', text=f'{name}_Cell-{str(id).zfill(3)}', values=[name, id, ratio, her2, chr17])
                self.last_cell += 1
                
                break
            
    def _add_cell(self):
        selected_item = self.window.cell_treeview.selection()
        cell_name = self.window.cell_treeview.item(selected_item[0])['text']
        
        if len(self.final_cell_score) >= self.required_cell:
            return messagebox.showwarning('Warning', f'Already select {self.required_cell} cells.')
        elif cell_name in self.final_cell_score:
            return messagebox.showwarning('Warning', f'{cell_name} was already selected.')
        else:
            raw_img, overlay_img = self.window.image_display.get_cropped_cell()
            self.final_cell_score[cell_name] = [int(self.window.cell_her2.get()), int(self.window.cell_chr17.get())]
            self.final_cell_image[cell_name] = [raw_img, overlay_img]
            self.window.selected_cell_panel.add_button(raw_img, cell_name)
            
            self._update_total()
            self._next_cell()
            
    def _delete_cell(self):
        selected_item = self.window.cell_treeview.selection()
        cell_name = self.window.cell_treeview.item(selected_item[0])['text']
        
        if cell_name not in self.final_cell_score:
            messagebox.showwarning('Warning', f'{cell_name} was not selected.')
        else:
            self.final_cell_score.pop(cell_name)
            self.final_cell_image.pop(cell_name)
            self.window.selected_cell_panel.remove_button(cell_name)
            
            self._update_total()
            self._next_cell()
        
    def _show_next(self) -> None:
        if len(self.final_cell_score) < self.required_cell:
            messagebox.showwarning(
                'Warning', 
                f'Only {len(self.final_cell_score)} cells are selected.'
            )
        
        elif 1.8 <= float(self.avg_ratio.get()) <= 2.2:
            response = messagebox.askquestion(
                "Question", 
                f"HER2 / Chr17: {float(self.avg_ratio.get())} is between 2.2 and 1.8.\nDo you wish to conduct a secondary analysis?."
            )
            if response == 'yes': self.required_cell = 40
                
        else:
            create_report(
                image_dict= self.final_cell_image,
                cell_dict= self.final_cell_score,
                report_output_path= self.window.cargo.report_path,
                excel_output_path= self.window.cargo.report_excel_path,
            )
            self.window.select_image.update_roots(
                name= 'current_image_treeview', 
                path= Path(self.window.cargo.output_path),
            )
            self.parent.show_frame('FourthPanel')
            
            cargo = self.window.cargo
            cargo.all_cell_score = []
            cargo.final_cell_score = []
            
            self.final_cell_score = {}
            self.final_cell_image = {}
            self.required_cell = 20
            self.last_cell = 50
            self.previous_progress = 0
            
            self._update_total()
            
            for item in self.window.cell_treeview.get_children():
                self.window.cell_treeview.delete(item)
    
    def _show_previous(self) -> None:
        response = messagebox.askquestion("Question", "Current progress will be discarded.\n\nDo you want to proceed?")
        if response == 'no': return
        
        cargo = self.window.cargo
        cargo.all_cell_score = []
        cargo.final_cell_score = []
        for key in cargo.get_container_keys():
            container = cargo.get_container(key)
            container.delete('her2')
            container.delete('chr17')
            container.delete('cell')
            container.delete('dug')
            container.delete('overlay')
            
        self.final_cell_score = {}
        self.final_cell_image = {}
        self.required_cell = 20
        self.last_cell = 50
        self.previous_progress = 0
            
        self.window.selected_cell_panel.remove_all_buttons()
        self._update_total()
        
        for item in self.window.cell_treeview.get_children():
            self.window.cell_treeview.delete(item)
            
        self.parent.show_frame('SecondPanel')

        
class FourthPanel(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        window: tk.Tk,
        label_background: str = '#333333',
        label_foreground: str = '#FFFFFF',
        button_background: str = '#454545',
        button_foreground: str = '#FFFFFF',
        active_background: str = '#3C3B3B',
        active_foreground: str = '#FFFFFF',
        *args,
        **kwargs,
    ) -> None:
        super().__init__(parent, bg='#333333', *args, **kwargs)
        self.parent = parent
        self.window = window
        
        # Progress Label
        progress_label = tk.Label(master= self, text= 'Completed', bg= '#292929', fg= '#FFFFFF', font= 'Arial 12 bold', width= 25, anchor= 'center')
        progress_label.pack(side=tk.TOP, fill=tk.X, ipady=5)
        
        # Result Frame
        result_frame = tk.Frame(master = self,bg = '#333333')
        result_frame.pack(expand= True)
        
        # Patient Label
        patient_label = tk.Label(master= result_frame, text='Patient Label', bg= label_background, fg= label_foreground, font= 'Arial 12', width= 25, anchor= 'center')
        patient_label.pack(pady= 20)
        
        self.patient_label_entry = ttk.Entry(master = result_frame, width = 15)
        self.patient_label_entry.pack()
        
        # Primary Analyzer Label
        primary_analyzer_label = tk.Label(master= result_frame, text='Primary Analyzer', bg= label_background, fg= label_foreground, font= 'Arial 12', width= 25, anchor= 'center')
        primary_analyzer_label.pack(pady= 20)
        
        self.primary_analyzer_entry = ttk.Entry(master = result_frame, width = 15)
        self.primary_analyzer_entry.pack()
        
        # Secondary Analyzer Label
        secondary_analyzer_label = tk.Label(master= result_frame, text='Secondary Analyzer', bg= label_background, fg= label_foreground, font= 'Arial 12', width= 25, anchor= 'center')
        secondary_analyzer_label.pack(pady= 20)
        
        self.secondary_analyzer_entry = ttk.Entry(master = result_frame, width = 15)
        self.secondary_analyzer_entry.pack()
        
        # Step Button
        next_step_button = tk.Button(master = self, text = 'Next Step', bg = button_background, fg = button_foreground, activebackground = active_background, activeforeground = active_foreground, borderwidth = 0, highlightthickness = 0, command= lambda: self._show_next())
        next_step_button.pack(side=tk.BOTTOM, fill= tk.X, ipady= 5)
        
    def _show_next(self) -> None:
        font = ImageFont.truetype('times.ttf', 24)
        
        report = Image.open(self.window.cargo.report_path)
        report_draw = ImageDraw.Draw(report)
        report_draw.text((250, 180), text=str(self.patient_label_entry.get()), fill='black', font=font)
        report_draw.text((250, 740), text=str(self.primary_analyzer_entry.get()), fill='black', font=font)
        report_draw.text((250, 810), text=str(self.secondary_analyzer_entry.get()), fill='black', font=font)
        report.save(self.window.cargo.report_path)
        
        self.window.selected_cell_panel.remove_all_buttons()
        
        self.window.image_display.input_image_path(str(self.window.cargo.report_path))
        self.window.image_display._update_keybind('drag')
        del self.window.cargo
        
        self.parent.show_frame('FirstPanel')
        
class PreprocessPanel(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        window: tk.Tk,
        label_background: str = '#292929',
        label_foreground: str = '#FFFFFF',
        button_background: str = '#454545',
        button_foreground: str = '#FFFFFF',
        active_background: str = '#3C3B3B',
        active_foreground: str = '#FFFFFF',
        *args,
        **kwargs,
    ) -> None:
        super().__init__(parent, bg='#333333', *args, **kwargs)
        self.parent = parent
        self.window = window
        self.run_list = []
        
        # Pre-run Analysis Label
        top_label = tk.Label(master= self, text= 'Pre-run Analysis',  bg= label_background, fg= label_foreground, font= 'Arial 12 bold', width= 25, anchor= 'center',)
        top_label.pack(side=tk.TOP, fill=tk.X, ipady=5)
        
        # Operation Buttons
        button_add = tk.Button(master = self, text = 'Add Path', font= 'Arial 10', width = 35, bg = button_background, fg = button_foreground, activebackground = active_background, activeforeground = active_foreground, borderwidth=0, highlightthickness=0, command = lambda: self._add_path())
        button_add.pack(side=tk.TOP, ipady=8, ipadx=50, pady= (10,5))
        button_delete = tk.Button(master = self, text = 'Delete Path', font = 'Arial 10', width = 35, bg = button_background, fg = button_foreground, activebackground = active_background, activeforeground = active_foreground, borderwidth=0,  highlightthickness=0, command= lambda: self._delete_path())
        button_delete.pack(side=tk.TOP, ipady=8, ipadx=50, pady= 5)
        button_auto = tk.Button(master = self, text = 'Auto Path', font = 'Arial 10', width = 35, bg = button_background, fg = button_foreground, activebackground = active_background, activeforeground = active_foreground, borderwidth=0,  highlightthickness=0, command= lambda: self._auto_path())
        button_auto.pack(side=tk.TOP, ipady=8, ipadx=50, pady= (5,10))
        
        self.prep_treeview = ttk.Treeview(master= self, height = 20, selectmode = "browse",columns = ('path'),displaycolumns = ('path'),)
        self.prep_treeview.pack(side=tk.TOP, fill=tk.BOTH)
        
        # cell_treeview.bind(sequence= "<<TreeviewSelect>>", func= self._treeview_select)
        self.prep_treeview.heading(column="#0", text='Index', anchor='center')
        self.prep_treeview.heading(column='path', text='Path', anchor='center')
        self.prep_treeview.column(column='#0', width=70, stretch=tk.NO)
        self.prep_treeview.column(column='path', width=200, stretch=tk.YES)
        
        # Step Button
        previous_step_button = tk.Button( master= self, text= 'Previous Step', bg= button_background, fg= button_foreground, activebackground= active_background, activeforeground= active_foreground, borderwidth=0, highlightthickness=0,command= lambda: self._show_previous(),)
        previous_step_button.pack(side=tk.BOTTOM, fill=tk.X)
        next_step_button = tk.Button( master= self, text= 'Next Step', bg= button_background, fg= button_foreground, activebackground= active_background, activeforeground= active_foreground, borderwidth=0, highlightthickness=0, command= lambda: self._show_next(),)
        next_step_button.pack(side=tk.BOTTOM, fill=tk.X, pady=2)
        
    def _add_path(self) -> None:
        path = Path(filedialog.askdirectory())
        id = len(self.prep_treeview.get_children())
        self.prep_treeview.insert('', 'end', text=f'{id}', values=[path])
        
    def _delete_path(self) -> None:
        selected_item = self.prep_treeview.selection()
        next_item = self.prep_treeview.next(selected_item)
        self.prep_treeview.selection_set(next_item)
        self.prep_treeview.delete(selected_item)
        
    def _auto_path(self) -> None:
        path = Path(filedialog.askdirectory())
        for root, dirs, files in os.walk(path):
            if dirs:
                continue
            if not files:
                continue
            if 'output' in root:
                continue
            
            root_path = Path(root)
            
            all_allowed = True
            for file_name in files:
                file_path = root_path / file_name
                
                if file_path.suffix.lower() not in {'.tiff', '.tif', '.jpg', '.png'}:
                    all_allowed = False
                    break
            
            if all_allowed:
                id = len(self.prep_treeview.get_children())
                self.prep_treeview.insert('', 'end', text=f'{id}', values=[root_path])
        
    def _show_next(self) -> None:
        self.window.loading_screen.show()
        threading.Thread(target=self._process).start()
    
    def _process(self) -> None:
        import openpyxl
        workbook = openpyxl.Workbook()
        sheet = workbook.active
            
        for item in self.prep_treeview.get_children():
            input_path = Path(self.prep_treeview.item(item)['values'][0])
            output_path = input_path.parent.absolute()
            
            self.window.loading_screen.set_status(f"Building Cargo for case: {input_path}")
            
            cargo = load_cargo(
                input_path = input_path,
                output_path= output_path,
            )
            
            self.window.loading_screen.set_status(f"Segementing Signals for case: {input_path}")
            
            process_parallel(
                cargo = cargo,
                her2_classifier_path = r'.\classifier\HER2\HER2-0.joblib', 
                chr17_classifier_path = r'.\classifier\Chr17\Chr17-0.joblib', 
                model_type= 'Cellpose',
            )
            
            self.window.loading_screen.set_status(f"Calculating for case: {input_path}")
            
            if self.window.status == 'ALL':
                needed_cell = 20
                final_cell_score = {}
                final_cell_image = {}
                
                sher2, schr17, scell = 0, 0, 0
                for _, _, _, her2, chr17, _ in cargo.all_cell_score[:needed_cell]:
                    sher2 += int(her2)
                    schr17 += int(chr17)
                    scell += 1
                
                if 1.8 <= float(round(sher2 / schr17, 3)) <= 2.2:
                    needed_cell = 40
                                    
                for name, cell_label, _, her2, chr17, _ in cargo.all_cell_score[:needed_cell]:
                    container = cargo.get_container(name=name)
                    raw_image = container.get(label= 'raw')
                    her2_mask = cv2.cvtColor(container.get('her2').astype(np.uint8), cv2.COLOR_GRAY2BGR)
                    her2_mask[np.where((her2_mask == [255, 255, 255]).all(axis=2))] = [0, 255, 0]
                    chr17_mask = cv2.cvtColor(container.get('chr17').astype(np.uint8), cv2.COLOR_GRAY2BGR)
                    chr17_mask[np.where((chr17_mask == [255, 255, 255]).all(axis=2))] = [0, 200, 255]
                    cells_mask = container.get(label= 'cell')
                    
                    cell_mask = np.where(cells_mask == int(cell_label), 255, 0).astype(np.uint8)
                    contours, _ = cv2.findContours(cell_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    boundary_image = raw_image.copy()
                    boundary_image = cv2.drawContours(boundary_image, contours, 0, (255, 255, 0), 1)
                    
                    x1, y1, x2, y2, _, _ = cropping_region(
                        input_cell_mask= cells_mask,
                        id_value= int(cell_label),
                        extend= 10,
                    )
                    
                    sraw_img = boundary_image[y1:y2, x1:x2]
                    sher2_mask = her2_mask[y1:y2, x1:x2]
                    schr17_mask = chr17_mask[y1:y2, x1:x2]
                    
                    overlay_img = cv2.addWeighted(sraw_img.copy(), 1, sher2_mask, 0.5, 0)
                    overlay_img = cv2.addWeighted(overlay_img, 1, schr17_mask, 0.5, 0)
                    
                    sraw_img = Image.fromarray(sraw_img).convert('RGB')
                    overlay_img = Image.fromarray(overlay_img).convert('RGB')
                    
                    cell_name = f'{name}_Cell-{str(cell_label).zfill(3)}'
                    final_cell_score[cell_name] = [int(her2), int(chr17)]
                    final_cell_image[cell_name] = [sraw_img, overlay_img]
                
                self.window.loading_screen.set_status(f"Creating report for case: {input_path}")
                
                create_report(
                    image_dict= final_cell_image,
                    cell_dict= final_cell_score,
                    report_output_path= cargo.report_path,
                    # excel_output_path= cargo.report_excel_path,
                )
                
                sheet.append([cargo.input_path.stem, sher2, schr17, scell])
                
            del cargo
            
        if workbook:
            workbook.save(r'F:\Lab\Her2DISH\calculate_numbers_accuracy\results.xlsx')
        
        for item in self.prep_treeview.get_children():
            self.prep_treeview.delete(item)
        
        messagebox.showinfo('Info', 'Completed!!')
        self.parent.show_frame('FirstPanel')
        self.window.loading_screen.hide()
        
    def _show_previous(self) -> None:
        for item in self.prep_treeview.get_children():
            self.prep_treeview.delete(item)
        self.parent.show_frame('FirstPanel')