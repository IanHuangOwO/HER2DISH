import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ttkthemes import ThemedStyle

from GUI.panel_display import *
from GUI.panel_process import *

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
        
        # Setup Variable
        self.selected_path = None
        
        # Loading Frame
        self.loading_frame = tk.Frame(self, bg="#202020")
        
        self.loading_screen = LoadingScreen(
            parent = self.loading_frame,
            window = self,
        )
        self.loading_screen.pack(expand=True)
        
        self.loading_frame.grid(row=0, column=0, rowspan=3, columnspan=3, sticky="nsew")
        
        # Working Frame
        self.working_frame = tk.Frame(self, bg='#202020')
    
        path_menu = Topmenu(
            parent = self.working_frame,
            window = self,
        )
        path_menu.pack(side=tk.TOP, fill=tk.X)
        self.select_image = SelectImagePanel(
            parent = self.working_frame,
            window = self,
        )
        self.select_image.pack(side=tk.LEFT, fill=tk.Y)
        process_image = ProcessImagePanel(
            parent = self.working_frame,
            window = self,
        )
        process_image.pack(side=tk.RIGHT, fill=tk.Y)
        self.image_display = ImageDisplayPanel(
            parent = self.working_frame,
            window = self,
        )
        self.image_display.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.working_frame.grid(row=0, column=0, rowspan=3, columnspan=3, sticky="nsew")
        
    def _check_close(self):
        """Callback to handle the close event."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()
            raise SystemExit
        
class LoadingScreen(tk.Frame):
    def __init__(self, parent, window, *args, **kwargs) -> None:
        super().__init__(parent, bg="#202020", *args, **kwargs)
        self.window = window
        
        loading = tk.Label(self, text='Loading...', font='Arial 12', bg='#202020', fg='#FFFFFF')
        loading.pack(pady=10)
        
        self.gif_label = tk.Label(self, bg="#202020")
        self.gif_label.pack()
        
        self.text = tk.Label(self, text='', font='Arial 8', bg='#202020', fg='#FFFFFF')
        self.text.pack(pady=10)
        
        self.load_gif()
        self.current_frame = 0
        self.animate_gif()
        
    def load_gif(self) -> None:
        from PIL import Image, ImageTk, ImageSequence
        self.gif_image = Image.open(r".\GUI\loading.gif")
        self.gif_frames = [ImageTk.PhotoImage(frame) for frame in ImageSequence.Iterator(self.gif_image)]
        self.frame_durations = [frame.info['duration'] for frame in ImageSequence.Iterator(self.gif_image)]

    def animate_gif(self) -> None:
        self.gif_label.configure(image=self.gif_frames[self.current_frame])
        duration = self.frame_durations[self.current_frame]
        self.current_frame = (self.current_frame + 1) % len(self.gif_frames)
        self.after(duration, self.animate_gif)
    
    def set_status(self, message: str) -> None:
        """
        Updates the text label (self.text) to display the given message.
        """
        self.text.config(text=message)
        
    def show(self) -> None:
        self.window.loading_frame.tkraise()
        
    def hide(self) -> None:
        self.window.working_frame.tkraise()
        
        
class Topmenu(tk.Frame):
    def __init__(
        self, parent, window,
        *args, **kwargs,
    ) -> None:
        super().__init__(parent, bg='#505050', *args, **kwargs,)
        self.window = window
        self.dropdowns = {}
        
        # Define the main menu and submenus
        menus = {
            'File': ['Open Folder'],
            'Help': ['Tutorial']
        }

        # Bind a global click event to the root window to close dropdowns
        self.window.bind("<Button-1>", self.hide_all_dropdowns)

        # Create menu buttons with simulated dropdowns
        for name_main_menu, name_sub_menu_list in menus.items():
            self.create_menu_button(name_main_menu, name_sub_menu_list)

    def create_menu_button(self, name_main_menu, name_sub_menu_list):
        """Create a Button for each main menu and attach a simulated dropdown."""
        # Add spaces to visually align text to the left
        button_text = name_main_menu
        menu_button = self.create_button(button_text)
        menu_button.pack(side=tk.LEFT)
        
        # Create a dropdown Frame for each menu button
        dropdown = self.create_dropdown(name_sub_menu_list)
        self.dropdowns[menu_button] = dropdown

    def create_button(self, text):
        """Create a styled Button for the main menu with a fixed width and left-aligned text."""
        btn = tk.Button(
            self,
            text=f"{text:<15}",
            anchor='w',
            bg='#505050',
            fg='#FFFFFF',
            activebackground='#3C3B3B',
            activeforeground='#FFFFFF',
            font='Arial 12',
            width=15,
            borderwidth=0,
            highlightthickness=0,
            command=lambda name=text.strip(): self.toggle_dropdown(name.strip())
        )
        return btn

    def create_dropdown(self, items):
        """Create a simulated dropdown menu as a Frame with buttons."""
        dropdown = tk.Frame(self.window, bg='#505050')
        dropdown.place_forget()  # Initially hide the dropdown

        for item in items:
            btn = tk.Button(
                dropdown,
                text=f"{item:<30}",
                anchor='w',
                bg='#505050',
                fg='#FFFFFF',
                activebackground='#3C3B3B',
                activeforeground='#FFFFFF',
                font='Arial 12',
                width=20,
                borderwidth=0,
                highlightthickness=0,
                command=lambda arg=item: self.switch(arg)
            )
            btn.pack(fill="x", pady=2)

        return dropdown

    def toggle_dropdown(self, menu_name):
        """Toggle the visibility of a dropdown menu and position it below its button."""
        # Locate the corresponding dropdown using the button name
        menu_button = next(
            (btn for btn, _ in self.dropdowns.items() if btn['text'].strip() == menu_name), None
        )
        if menu_button is None:
            return

        dropdown = self.dropdowns[menu_button]

        # Hide the dropdown if it's already visible
        if dropdown.winfo_ismapped():
            dropdown.place_forget()
        else:
            # Hide any other open dropdowns
            self.hide_all_dropdowns()
            
            # Calculate button's position and show dropdown below it
            x = menu_button.winfo_rootx() - self.window.winfo_rootx()
            y = menu_button.winfo_rooty() - self.window.winfo_rooty() + menu_button.winfo_height() + 1
            dropdown.place(x=x, y=y)
            dropdown.tkraise()

    def hide_all_dropdowns(self, event=None):
        """Hide all dropdown menus only if the click is outside dropdowns and buttons."""
        clicked_widget = self.window.winfo_containing(event.x_root, event.y_root) if event else None

        # Check if clicked widget is part of any dropdown or menu button
        if not any(clicked_widget is widget or clicked_widget in widget.winfo_children() 
                for widget in self.dropdowns.keys() | self.dropdowns.values()):
            # Hide all dropdowns if clicked outside
            for dropdown in self.dropdowns.values():
                dropdown.place_forget()

    def switch(self, name: str):
        """Handle actions for each menu item."""
        # Hide dropdowns after selecting a menu item
        self.hide_all_dropdowns()

        match name:
            case 'Open Folder':
                self.window.selected_path = Path(filedialog.askdirectory())
                self.window.select_image.update_roots(
                    name= 'select_image_treeview', 
                    path= self.window.selected_path,
                )
                
            case 'Tutorial':
                messagebox.showinfo("Tutorial", "This is a tutorial message.")

class SelectImagePanel(tk.Frame):
    def __init__(
        self, parent, window,
        title_label_bg: str = '#303030',
        title_label_fg: str = '#FFFFFF',
        title_label_font: str = 'Arial 12 bold', 
        title_label_width: int = 25,
        current_image_tree_height: int = 15,
        *args, **kwargs,
    ) -> None:
        super().__init__(parent, *args, **kwargs)
        self.window = window
        
        # Current Image Label
        current_image_label = tk.Label(
            master= self,
            bg = title_label_bg,
            fg = title_label_fg,
            font= title_label_font,
            width= title_label_width,
            text= 'CURRENT IMAGE',
            anchor= 'center',
        )
        current_image_label.pack(
            side=tk.TOP, 
            fill=tk.X,
            ipady=5,
        )
        
        # Current Image TreeView
        self.current_image_treeview = ttk.Treeview(
            master= self, 
            show= 'tree',
            columns=('fullpath', 'type'),
            displaycolumns=(),
            selectmode="extended",
            height= current_image_tree_height,
        )
        self.current_image_treeview.pack(
            side=tk.TOP,
            fill=tk.X,
        )
        self.current_image_treeview.bind(
            sequence= "<<TreeviewSelect>>", 
            func= self.select_tree,
        )
        self.current_image_treeview.bind(
            sequence= '<<TreeviewOpen>>',
            func= self.update_tree,
        )
        
        # Select Image Label
        select_image_label = tk.Label(
            master= self, 
            bg = title_label_bg,
            fg = title_label_fg,
            font= title_label_font,
            width= title_label_width,
            text= 'SELECT IMAGE',
            anchor= 'center',
        )
        select_image_label.pack(
            side=tk.TOP, 
            fill=tk.X,
            ipady=5,
        )
        
        # Select Image TreeView
        self.select_image_treeview = ttk.Treeview(
            master= self, 
            show= 'tree',
            columns=('fullpath', 'type'),
            displaycolumns=(),
            selectmode="browse",
        )
        self.select_image_treeview.pack(
            side=tk.TOP,
            fill=tk.BOTH,
            expand= True,
        )
        self.select_image_treeview.bind(
            sequence= "<<TreeviewSelect>>", 
            func= self.select_tree,
        )
        self.select_image_treeview.bind(
            sequence= '<<TreeviewOpen>>',
            func= self.update_tree,
        )
        
    def select_tree(self, event):
        tree = event.widget
        file_path = Path(tree.set(tree.selection()[0], "fullpath"))
        if not file_path.is_file():
            return
        if file_path.suffix in ('.tif', '.tiff', '.jpg', '.png'):
            self.window.image_display.input_image_path(str(file_path))
    
    def update_tree(self, event):
        """
        Populates the tree view with directories and files.
        """
        tree = event.widget
        node = tree.focus()
        self._populate_tree(tree, node)

    def update_roots(self, name, path= None):
        """Populates the tree view with the root directory."""
        if name == 'select_image_treeview':
            tree = self.select_image_treeview
        elif name == 'current_image_treeview':
            tree = self.current_image_treeview
            
        for item in tree.get_children():
            tree.delete(item)
        
        if path is None:
            return
        if path.is_file():
            path = path.parent
        elif not path.is_dir():
            return

        tree.heading("#0", text=path.name, anchor='center')
        root_node = tree.insert('', 'end', text=path.name, values=[str(path), "directory"])
        self._populate_tree(tree, root_node)
            
    def _populate_tree(self, tree, node):
        """
        Populates the tree view with directories and files for a given node.
        """
        path = Path(tree.set(node, "fullpath"))
        tree.delete(*tree.get_children(node))  # Clear existing children

        if not path.is_dir():
            return

        for item in path.iterdir():
            if item.is_dir():
                # Add directories with a dummy child for expandability
                if not self._node_exists(tree, node, str(item)):
                    dir_id = tree.insert(node, "end", text=item.name, values=[str(item), "directory"])
                    tree.insert(dir_id, 0, text="dummy")  # Dummy child for lazy loading
            elif item.is_file():
                # Add files directly
                if not self._node_exists(tree, node, str(item)):
                    tree.insert(node, "end", text=item.name, values=[str(item), "file"])

        tree.item(node, open=True)  # Automatically expand the current node

    def _node_exists(self, tree, parent, path):
        """
        Checks if the given path already exists as a child of the parent node in the tree.
        """
        for child in tree.get_children(parent):
            if tree.set(child, "fullpath") == path:
                return True
        return False