import tkinter as tk
import threading
import os

from tkinter import ttk, messagebox, filedialog
from pathlib import Path

from process import *
from tools import *


class ProcessAllPanel(tk.Frame):
    def __init__(
        self, window: tk.Tk, parent: tk.Widget,
        label_font: str = 'Arial 12',
        label_background: str = '#292929', label_foreground: str = '#FFFFFF',
        button_background: str = '#454545', button_foreground: str = '#FFFFFF',
        active_background: str = '#3C3B3B', active_foreground: str = '#FFFFFF',
        *args, **kwargs,
    ) -> None:
        super().__init__(parent, bg='#333333', *args, **kwargs)
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
        previous_step_button = tk.Button(
            master= self, 
            text= 'Back', font= label_font,
            bg= button_background, fg= button_foreground, 
            activebackground= active_background, activeforeground= active_foreground, 
            borderwidth=0, highlightthickness=0, 
            command= lambda: self._show_previous(window)
        )
        previous_step_button.pack(side=tk.BOTTOM, fill=tk.X)
        next_step_button = tk.Button(
            master= self, 
            text= 'Next Step', font= label_font,
            bg= button_background, fg= button_foreground, 
            activebackground= active_background, activeforeground= active_foreground, 
            borderwidth=0, highlightthickness=0, 
            command= lambda: self._show_next(window)
        )
        next_step_button.pack(side=tk.BOTTOM, fill=tk.X, pady=2, ipady=2)
        
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
        
    def _show_next(self, window: tk.Tk) -> None:
        window.load_start()
        threading.Thread(target=lambda: self._process(window)).start()
    
    def _process(self, window: tk.Tk) -> None:
        # import openpyxl
        # workbook = openpyxl.Workbook()
        # sheet = workbook.active
            
        for item in self.prep_treeview.get_children():
            input_path = Path(self.prep_treeview.item(item)['values'][0])
            output_path = input_path.parent.absolute()
            
            window.log_info(message= f"Building Cargo for case: {input_path}")
            
            cargo = load_cargo(
                input_path = input_path,
                output_path= output_path,
            )
            
            window.log_info(message= f"Segementing Signals for case: {input_path}")
            
            process_parallel(
                cargo = cargo,
                her2_classifier_path = r'.\classifier\HER2\HER2-0.joblib', 
                chr17_classifier_path = r'.\classifier\Chr17\Chr17-0.joblib', 
                model_type= 'Cellpose',
            )
            
            window.log_info(message= f"Calculating for case: {input_path}")
            
            if window.status == 'ALL':
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
                
                window.log_info(message= f"Creating report for case: {input_path}")
                
                create_report(
                    image_dict= final_cell_image,
                    cell_dict= final_cell_score,
                    report_output_path= cargo.report_path,
                    # excel_output_path= cargo.report_excel_path,
                )
                
                # sheet.append([cargo.input_path.stem, sher2, schr17, scell])
                
            del cargo
            
        # if workbook:
        #     workbook.save(r'F:\Lab\Her2DISH\calculate_numbers_accuracy\results.xlsx')
        
        for item in self.prep_treeview.get_children():
            self.prep_treeview.delete(item)
        
        messagebox.showinfo('Info', 'Completed!!')
        window.show_frame('FirstPanel')
        window.load_end()
        
    def _show_previous(self, window: tk.Tk) -> None:
        for item in self.prep_treeview.get_children():
            self.prep_treeview.delete(item)
        window.show_frame('FirstPanel')