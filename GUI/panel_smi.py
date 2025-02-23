import tkinter as tk
import threading
import os

from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Dict

from process import load_cargo, process_parallel
from tools import create_report
        
        
class FirstPanel(tk.Frame):
    def __init__(
        self, window: tk.Tk, parent: tk.Widget,
        button_width: int = 30, button_height: int = 3,
        button_font: str = 'Arial 12 bold',
        button_background: str = '#454545', button_foreground: str = '#FFFFFF',
        active_background: str = '#3C3B3B', active_foreground: str = '#FFFFFF',
        *args, **kwargs,
    ) -> None:
        super().__init__(master=parent, bg='#333333', *args, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        
        # Progress Label
        progress_label = tk.Label(
            master=self,
            text='Progress 1 of 3', font='Arial 12 bold',
            bg='#292929', fg='#FFFFFF',
            width=25, anchor='center',
        )
        progress_label.pack(side=tk.TOP, fill=tk.X, ipady=5)
        
        # Process Button
        button_frame = tk.Frame(master=self, bg='#333333',)
        button_frame.pack(expand=True)
        
        # Semi-Auto Button
        smei_button = tk.Button(
            master=button_frame,
            text='Semi-Auto Quantification', font=button_font,
            bg=button_background, fg=button_foreground,
            activebackground=active_background, activeforeground=active_foreground,
            width=button_width, height=button_height,
            borderwidth=0, highlightthickness=0,
            command=lambda args='SMI': self.process(args, window),
        )
        smei_button.grid(row=1, column=0, pady=20)

        # Auto All Button
        auto_all_button = tk.Button(
            master=button_frame,
            text='Auto All Quantification', font=button_font,
            bg=button_background, fg=button_foreground,
            activebackground=active_background, activeforeground=active_foreground,
            width=button_width, height=button_height,
            borderwidth=0, highlightthickness=0,
            command=lambda args='ALL': self.process(args, window),
        )
        auto_all_button.grid(row=2, column=0, pady=20)
        
        # Anaylsis Preperation
        preperation_button = tk.Button(
            master=button_frame, 
            text='Pre-run Analysis', font=button_font,
            bg=button_background, fg=button_foreground,
            activebackground=active_background, activeforeground=active_foreground,
            width=button_width, height=button_height,
            borderwidth=0,  highlightthickness=0,
            command=lambda args='PREP': self.process(args, window),
        )
        preperation_button.grid(row=3, column=0, pady=20)
        
        # Train Classifier
        train_classifier_button = tk.Button(
            master=button_frame,
            text='Train Classifier', font=button_font,
            bg=button_background, fg=button_foreground,
            activebackground=active_background, activeforeground=active_foreground,
            width=button_width, height=button_height,
            borderwidth=0,  highlightthickness=0,
            command=lambda args='TRAIN': self.process(args, window),
        )
        train_classifier_button.grid(row=4, column=0, pady=20)
        
        # Anaylsis Preperation
        reset_button = tk.Button(
            master=button_frame,
            text='Reset Analysis', font=button_font,
            bg=button_background, fg=button_foreground,
            activebackground=active_background, activeforeground=active_foreground,
            width=button_width, height=button_height,
            borderwidth=0, highlightthickness=0,
            command=lambda args='RESET': self.process(args, window),
        )
        reset_button.grid(row=5, column=0, pady=20)
        
    def process(self, name: str, window: tk.Tk) -> None: 
        match name:
            case 'SMI':
                window.load_start()
                threading.Thread(target=lambda: self.SMI(window)).start()
            
            case 'ALL':
                window.status = name
                threading.Thread(target=lambda: self.All(window)).start()
            
            case 'PREP':
                window.status = name
                threading.Thread(target=lambda: self.All(window)).start()
            
            case 'TRAIN':
                threading.Thread(target=lambda: self.TRAIN(window)).start()
            
            case 'RESET':
                threading.Thread(target=lambda: self.RESET(window)).start()
            
    def SMI(self, window: tk.Tk) -> None:
        try: 
            window.root_path = Path(window.root_path)
        except: 
            window.root_path = Path(filedialog.askdirectory())
            window.select_panel.update_roots(name= 'select_image_treeview', path= window.root_path)
        
        window.log_info(message= 'Starting Analysis')
        window.cargo = load_cargo(
            input_path= window.root_path,
            output_path= window.root_path.parent.absolute(),
        )
        window.select_panel.update_roots(
            name= 'current_image_treeview', 
            path= window.cargo.output_path,
        )
        window.show_frame('SecondPanel')
        window.load_end()
        
    def All(self, window: tk.Tk) -> None:
        input_path = filedialog.askdirectory()
        window.select_panel.update_roots(
            name= 'select_image_treeview',
            path= Path(input_path),
        )
        window.show_frame('ProcessAllPanel')
        
    def TRAIN(self, window: tk.Tk) -> None:
        input_image_path = Path(filedialog.askopenfilename())
        if not input_image_path.is_file(): return
        if input_image_path.suffix in ('.tif', '.tiff', '.jpg', '.png'):
            window.train_display.input_image_path(input_image_path)
        
        window.show_frame('TrainDisplayPanel')
        window.show_frame('TrainPanel')
        
    def RESET(self, window: tk.Tk) -> None:
        del window.root_path
        window.select_panel.update_roots(name= 'select_image_treeview')
        window.select_panel.update_roots(name= 'current_image_treeview')
        
        window.image_display.canvas.delete(window.image_display.image_id)
        window.image_display.image_id = None
        
class SecondPanel(tk.Frame):
    def __init__(
        self, window: tk.Tk, parent: tk.Widget,
        label_background: str = '#333333', label_foreground: str = '#FFFFFF',
        button_background: str = '#454545', button_foreground: str = '#FFFFFF',
        active_background: str = '#3C3B3B', active_foreground: str = '#FFFFFF',
        *args, **kwargs,
    ) -> None:
        super().__init__(master=parent, bg='#333333', *args, **kwargs)
        
        # Progress Label
        progress_label = tk.Label(
            master=self,
            text='Progress 2 of 3', font='Arial 12 bold',
            bg='#292929', fg='#FFFFFF',
            width=25, anchor='center',
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
            text='HER2 MODEL', font='Arial 14',
            bg=label_background, fg=label_foreground,
            width=25, anchor='center',
        )
        HER2_image_label.pack(pady=(40, 10))
        # HER2 Model Option Menu
        her2_classifier_path = r'.\classifier\HER2'
        self.her2_classifier_dict: Dict[str, str] = {
            os.path.basename(path): os.path.join(her2_classifier_path, path)
            for path in os.listdir(her2_classifier_path)
            if path.endswith('.joblib')}
        self.her2_model_path = tk.StringVar()
        options = [name.center(15) for name in self.her2_classifier_dict]
        HER2_model_menu = ttk.OptionMenu(entry_frame, self.her2_model_path, options[0], *options,)
        HER2_model_menu.pack()
        
        
        # CHR17 Model Label
        CHR17_options_label = tk.Label(
            master=entry_frame,
            text='CHR17 MODEL', font='Arial 14',
            bg=label_background, fg=label_foreground,
            width=25, anchor='center',
        )
        CHR17_options_label.pack(pady=(40, 10))
        # CHR17 Model Option Menu
        chr17_classifier_path = r'.\classifier\CHR17'
        self.chr17_classifier_dict: Dict[str, str] = {
            os.path.basename(path): os.path.join(chr17_classifier_path, path)
            for path in os.listdir(chr17_classifier_path)
            if path.endswith('.joblib')}
        self.chr17_model_path = tk.StringVar()
        options = [name.center(15) for name in self.chr17_classifier_dict]
        CHR17_model_menu = ttk.OptionMenu(entry_frame, self.chr17_model_path, options[0], *options,)
        CHR17_model_menu.pack()
        
        
        # Model Type Label
        model_type_label = tk.Label(
            master=entry_frame,
            text='MODEL TYPE', font='Arial 14',
            bg=label_background, fg=label_foreground,
            width=22, anchor='center',
        )
        model_type_label.pack(pady=(40, 10))
        
        # Model Type Option Menu
        self.model_type = tk.StringVar()
        options = ["StarDist".center(15), "Cellpose".center(15)]
        model_type_menu = ttk.OptionMenu(entry_frame, self.model_type, options[0], *options,)
        model_type_menu.pack()
        
        # Step Button
        previous_step_button = tk.Button(
            master=self,
            text='Previous Step', font='Arial 12',
            bg=button_background, fg=button_foreground,
            activebackground=active_background, activeforeground=active_foreground,
            borderwidth=0, highlightthickness=0,
            command= lambda: self._show_previous(window),
        )
        previous_step_button.pack(side=tk.BOTTOM, fill=tk.X)
        next_step_button = tk.Button(
            master=self,
            text='Next Step', font='Arial 12',
            bg=button_background, fg=button_foreground,
            activebackground=active_background, activeforeground=active_foreground,
            borderwidth=0,  highlightthickness=0,
            command= lambda: self._show_next(window),
        )
        next_step_button.pack(side=tk.BOTTOM, fill=tk.X, pady=2, ipady=2)
    
    def _show_next(self, window: tk.Tk) -> None:
        window.load_start()
        threading.Thread(target= lambda: self._process(window)).start()
    
    def _process(self, window: tk.Tk) -> None:
        window.log_info(message= 'Segmenting HER2 and Chr17 signals')
        process_parallel(
            cargo = window.cargo,
            her2_classifier_path = self.her2_classifier_dict[self.her2_model_path.get().strip()], 
            chr17_classifier_path = self.chr17_classifier_dict[self.chr17_model_path.get().strip()],
            model_type= self.model_type.get().strip(),
        )
        
        window.log_info(message= 'Importing existing progress.')
        if len(window.cargo.temp_cell_score) > 1: 
            response = messagebox.askquestion("Question", f"Found existing progress.\n\nDo you wish to load and continue ?")
            if response == 'yes':
                for cell_name, her2, chr17 in window.cargo.temp_cell_score:
                    name, id = cell_name.split('_Cell-')
                    window.cell_treeview.insert('', 'end', text=f'{name}_Cell-{id}', values=[name, int(id), round(float(her2 / chr17), 4), her2, chr17])
        
        
        window.log_info(message= 'Importing cell score.')
        for name, id, ratio, her2, chr17, _ in window.cargo.all_cell_score[:50]:
            window.cell_treeview.insert('', 'end', text=f'{name}_Cell-{str(id).zfill(3)}', values=[name, id, ratio, her2, chr17])
        
        first_item = window.cell_treeview.get_children()[0]
        window.cell_treeview.selection_set(first_item)
        window.cell_treeview.see(first_item)
        
        window.show_frame('ThirdPanel')
        window.load_end()
        
    def _show_previous(self, window: tk.Tk) -> None:
        window.show_frame('FirstPanel')
        
        
class ThirdPanel(tk.Frame):
    def __init__(
        self, window: tk.Tk, parent: tk.Widget,
        label_background: str = '#333333', label_foreground: str = '#FFFFFF',
        button_background: str = '#454545', button_foreground: str = '#FFFFFF',
        active_background: str = '#3C3B3B', active_foreground: str = '#FFFFFF',
        *args, **kwargs,
    ) -> None:
        super().__init__(parent, bg='#333333', *args, **kwargs)
        
        self.required_cell = 20
        self.last_cell = 50
        self.previous_progress = 0
        
        # Progress Label
        progress_label = tk.Label(master= self, text= 'Progress 3 of 3',  bg= '#292929', fg= '#FFFFFF', font= 'Arial 12 bold', width= 25, anchor= 'center',)
        progress_label.pack(side=tk.TOP, fill=tk.X, ipady=5)
        
        #Cell Status Label
        cell_frame = tk.Frame(master = self,bg = '#333333')
        cell_frame.pack(side=tk.TOP, expand= True)
        
        cell_label = tk.Label(master= cell_frame, text= 'Cell Status', bg= '#303030', fg= '#FFFFFF', font= 'Arial 12', width= 40, anchor= 'center')
        cell_label.grid(row=1, column=0, columnspan=6, sticky='ew', ipady= 5)
        
        cell_her2 = ttk.Label(master = cell_frame,text = 'Current HER2:', background = label_background, foreground = label_foreground)
        cell_her2.grid(row=2, column=0, pady=(8,3), sticky='e')
        self.cell_her2 = ttk.Entry(master = cell_frame, width = 5)
        self.cell_her2.insert(0, '0')
        self.cell_her2.grid(row=2, column=1, pady=(8,3), sticky='w')
        
        cell_chr17 = ttk.Label(master = cell_frame, text = 'Current Chr17:', background = label_background, foreground = label_foreground)
        cell_chr17.grid(row=3, column=0, pady=3, sticky='e')
        self.cell_chr17 = ttk.Entry(master = cell_frame, width=5)
        self.cell_chr17.insert(0, '0')
        self.cell_chr17.grid(row=3, column=1, pady=3, sticky='w')
        
        cell_ratio = ttk.Label(master = cell_frame, text='Current Ratio:', background = label_background, foreground = label_foreground)
        cell_ratio.grid(row=4, column=0, pady=3, sticky='e')
        self.cell_ratio = ttk.Entry(master = cell_frame, width=5)
        self.cell_ratio.insert(0, '0')
        self.cell_ratio.grid(row=4, column=1, pady=3, sticky='w')
        
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
        button_add = tk.Button(master = cell_frame, text = 'Add', font= 'Arial 10', width = 35, bg = button_background, fg = button_foreground, activebackground = active_background, activeforeground = active_foreground, borderwidth=0, highlightthickness=0, command = lambda: self._add_cell(window))
        button_add.grid(row=5, column=0, columnspan=6, padx=2, pady=(5,2))
        button_next = tk.Button(master = cell_frame, text = 'Next', font = 'Arial 10', width = 35, bg = button_background, fg = button_foreground, activebackground = active_background, activeforeground = active_foreground, borderwidth=0,  highlightthickness=0, command= lambda: self._next_cell(window))
        button_next.grid(row=6, column=0, columnspan=6, padx=2, pady=2)
        bttton_delete = tk.Button(master =  cell_frame, text = 'Delete', font = 'Arial 10', width = 35,  bg= button_background, fg= button_foreground, activebackground= active_background, activeforeground= active_foreground, borderwidth=0,  highlightthickness=0, command= lambda: self._delete_cell(window))
        bttton_delete.grid(row=7, column=0, columnspan=6, padx=2, pady=(2,7))
        
        # Cell List
        cell_label = tk.Label(master= cell_frame,  text= 'Cell List',  bg= '#303030',fg= '#FFFFFF', font= 'Arial 12',anchor= 'center')
        cell_label.grid(row=8, column=0, columnspan=6, ipady=5, sticky='ew')
        cell_treeview = ttk.Treeview(master= cell_frame, height = 15, selectmode = "browse", columns = ('id', 'image', 'ratio', 'her2', 'chr17'), displaycolumns = ('ratio', 'her2', 'chr17'))
        cell_treeview.grid(row=9, column=0, columnspan=6, sticky='ew')
        
        cell_treeview.bind(sequence= "<<TreeviewSelect>>", func= lambda event: self._treeview_select(window, event))
        cell_treeview.heading(column="#0", text='Cell ID', anchor='center')
        cell_treeview.heading(column='ratio', text='Ratio', anchor='center')
        cell_treeview.heading(column='her2', text='HER2', anchor='center')
        cell_treeview.heading(column='chr17', text='Chr17', anchor='center')
        cell_treeview.column(column='#0', width=200, stretch=tk.NO)
        cell_treeview.column(column='ratio', width=70, stretch=tk.NO)
        cell_treeview.column(column='her2', width=70, stretch=tk.NO)
        cell_treeview.column(column='chr17', width=70, stretch=tk.NO)
        
        window.cell_treeview = cell_treeview
        window.third_panel = self
        
        # Step Button
        previous_step_button = tk.Button(
            master= self, 
            text= 'Previous Step', font= 'Arial 12',
            bg= button_background, fg= button_foreground, 
            activebackground= active_background, activeforeground= active_foreground, 
            borderwidth=0, highlightthickness=0,
            command= lambda: self._show_previous(window)
        )
        previous_step_button.pack(side=tk.BOTTOM, fill=tk.X)
        next_step_button = tk.Button(
            master= self, 
            text= 'Next Step', font= 'Arial 12', 
            bg= button_background, fg= button_foreground, 
            activebackground= active_background, activeforeground= active_foreground, 
            borderwidth=0, highlightthickness=0, 
            command= lambda: self._show_next(window)
        )
        next_step_button.pack(side=tk.BOTTOM, fill=tk.X, pady=2, ipady=2)
        
    def _treeview_select(self, window: tk.Tk, event):
        tree = event.widget
        selected_item = tree.selection()
        if selected_item:
            name, cell_id, ratio, her2, chr17 = tree.item(selected_item[0])['values']
            window.show_frame('CellDisplayPanel')
            window.cell_display.input_image_cell(cell_id, name)
            self.update_number(ratio, her2, chr17)
            
        if len(window.cargo.temp_cell_score) > 20:
            self.required_cell = 40
            
        if self.previous_progress < len(window.cargo.temp_cell_score):
            self.previous_progress += 1
            self._add_cell(window)
            
    def update_number(self, ratio = 0, her2 = 0, chr17 = 0) -> None:
        self.cell_her2.delete(0, tk.END)
        self.cell_her2.insert(0, str(int(float(her2))))
        
        self.cell_chr17.delete(0, tk.END)
        self.cell_chr17.insert(0, str(int(float(chr17))))
        
        self.cell_ratio.delete(0, tk.END)
        self.cell_ratio.insert(0, str(float(ratio)))
    
    def _update_total(self, window:tk.Tk) -> None:
        total_her2, total_chr17, total_cell = 0, 0, 0
        for her2, chr17 in window.cargo.final_cell_score.values():
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
            
    def _next_cell(self, window: tk.Tk):
        selected_items = window.cell_treeview.selection()
        
        current_item = selected_items[0] if selected_items else None
        next_item = window.cell_treeview.next(current_item) if current_item else window.cell_treeview.get_children()[0]
        
        while next_item:
            cell_name = window.cell_treeview.item(next_item)['text']
            
            if cell_name in window.cargo.final_cell_score:
                next_item = window.cell_treeview.next(next_item)
            else:
                if current_item:
                    window.cell_treeview.selection_remove(current_item)
                window.cell_treeview.selection_set(next_item)
                window.cell_treeview.see(next_item)
                
                if self.last_cell >= len(window.cargo.all_cell_score):
                    break
                
                name, id, ratio, her2, chr17, _ = window.cargo.all_cell_score[self.last_cell]
                window.cell_treeview.insert('', 'end', text=f'{name}_Cell-{str(id).zfill(3)}', values=[name, id, ratio, her2, chr17])
                self.last_cell += 1
                
                break
            
    def _add_cell(self, window: tk.Tk):
        selected_item = window.cell_treeview.selection()
        cell_name = window.cell_treeview.item(selected_item[0])['text']
        
        if len(window.cargo.final_cell_score) >= self.required_cell:
            return messagebox.showwarning('Warning', f'Already select {self.required_cell} cells.')
        elif cell_name in window.cargo.final_cell_score:
            return messagebox.showwarning('Warning', f'{cell_name} was already selected.')
        else:
            raw_img, overlay_img = window.cell_display.get_cropped_cell()
            window.cargo.final_cell_score[cell_name] = [int(self.cell_her2.get()), int(self.cell_chr17.get())]
            window.cargo.final_cell_image[cell_name] = [raw_img, overlay_img]
            window.selected_cell_panel.add_button(raw_img, cell_name)
            
            self._update_total(window)
            self._next_cell(window)
            
    def _delete_cell(self, window: tk.Tk):
        selected_item = window.cell_treeview.selection()
        cell_name = window.cell_treeview.item(selected_item[0])['text']
        
        if cell_name not in window.cargo.final_cell_score:
            messagebox.showwarning('Warning', f'{cell_name} was not selected.')
        else:
            window.cargo.final_cell_score.pop(cell_name)
            window.cargo.final_cell_image.pop(cell_name)
            window.selected_cell_panel.remove_button(cell_name)
            
            self._update_total(window)
            self._next_cell(window)
        
    def _show_next(self, window: tk.Tk) -> None:
        if len(window.cargo.final_cell_score) < self.required_cell:
            messagebox.showwarning(
                'Warning', 
                f'Only {len(window.cargo.final_cell_score)} cells are selected.'
            )
        
        elif 1.8 <= float(self.avg_ratio.get()) <= 2.2:
            response = messagebox.askquestion(
                "Question", 
                f"HER2 / Chr17: {float(self.avg_ratio.get())} is between 2.2 and 1.8.\nDo you wish to conduct a secondary analysis?."
            )
            if response == 'yes': self.required_cell = 40
                
        else:
            create_report(
                image_dict= window.cargo.final_cell_image,
                cell_dict= window.cargo.final_cell_score,
                report_output_path= window.cargo.report_path,
                excel_output_path= window.cargo.report_excel_path,
            )
            window.select_panel.update_roots(
                name= 'current_image_treeview', 
                path= Path(window.cargo.output_path),
            )
            window.show_frame('FourthPanel')
            
            cargo = window.cargo
            cargo.all_cell_score = []
            cargo.final_cell_score = {}
            cargo.final_cell_image = {}
            
            self.required_cell = 20
            self.last_cell = 50
            self.previous_progress = 0
            
            self._update_total(window)
            
            for item in window.cell_treeview.get_children():
                window.cell_treeview.delete(item)
    
    def _show_previous(self, window: tk.Tk) -> None:
        response = messagebox.askquestion("Question", "Current progress will be discarded.\n\nDo you want to proceed?")
        if response == 'no': return
        
        cargo = window.cargo
        cargo.all_cell_score = []
        cargo.final_cell_score = {}
        cargo.final_cell_image = {}
        
        self.required_cell = 20
        self.last_cell = 50
        self.previous_progress = 0
        
        for key in cargo.get_container_keys():
            container = cargo.get_container(key)
            container.delete('her2')
            container.delete('chr17')
            container.delete('cell')
            container.delete('dug')
            container.delete('overlay')
            
        window.selected_cell_panel.remove_all_buttons()
        self._update_total()
        
        for item in window.cell_treeview.get_children():
            window.cell_treeview.delete(item)
            
        window.show_frame('SecondPanel')

        
class FourthPanel(tk.Frame):
    def __init__(
        self, parent: tk.Widget, window: tk.Tk,
        label_background: str = '#333333', label_foreground: str = '#FFFFFF',
        button_background: str = '#454545', button_foreground: str = '#FFFFFF',
        active_background: str = '#3C3B3B', active_foreground: str = '#FFFFFF',
        *args, **kwargs,
    ) -> None:
        super().__init__(parent, bg='#333333', *args, **kwargs)
        
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
        next_step_button = tk.Button(
            master = self, 
            text = 'Next Step', font= 'Arial 12',
            bg = button_background, fg = button_foreground, 
            activebackground = active_background, activeforeground = active_foreground, 
            borderwidth = 0, highlightthickness = 0, 
            command= lambda: self._show_next(window)
        )
        next_step_button.pack(side=tk.BOTTOM, fill= tk.X, ipady=2)
        
    def _show_next(self, window: tk.Tk) -> None:
        from PIL import Image, ImageDraw, ImageFont
        font = ImageFont.truetype('times.ttf', 24)
        
        report = Image.open(window.cargo.report_path)
        report_draw = ImageDraw.Draw(report)
        report_draw.text((250, 180), text=str(self.patient_label_entry.get()), fill='black', font=font)
        report_draw.text((250, 740), text=str(self.primary_analyzer_entry.get()), fill='black', font=font)
        report_draw.text((250, 810), text=str(self.secondary_analyzer_entry.get()), fill='black', font=font)
        report.save(window.cargo.report_path)
        
        window.selected_cell_panel.remove_all_buttons()
        
        window.image_display.input_image_path(str(window.cargo.report_path))
        window.image_display._update_keybind('drag')
        del window.cargo
        
        window.show_frame('FirstPanel')