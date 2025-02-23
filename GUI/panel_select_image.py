import tkinter as tk

from tkinter import ttk, messagebox, filedialog
from pathlib import Path


class TopMenu(tk.Frame):
    def __init__(self, parent: tk.Widget, window: tk.Tk, *args, **kwargs) -> None:
        super().__init__(parent, bg='#505050', *args, **kwargs,)
        self.window = window
        self.dropdowns = {}
        
        # Define the main menu and submenus
        menus = {
            'File': ['Open Folder'],
            'Help': ['Tutorial']
        }

        # Bind a global click event to the root window to close dropdowns
        self.window.bind("<Button-1>", self._hide_all_dropdowns)

        # Create menu buttons with simulated dropdowns
        for name_main_menu, name_sub_menu_list in menus.items():
            self._create_menu_button(name_main_menu, name_sub_menu_list)

    def _create_menu_button(self, name_main_menu, name_sub_menu_list):
        """Create a Button for each main menu and attach a simulated dropdown."""
        # Add spaces to visually align text to the left
        button_text = name_main_menu
        menu_button = self._create_button(button_text)
        menu_button.pack(side=tk.LEFT)
        
        # Create a dropdown Frame for each menu button
        dropdown = self._create_dropdown(name_sub_menu_list)
        self.dropdowns[menu_button] = dropdown

    def _create_button(self, text):
        """Create a styled Button for the main menu with a fixed width and left-aligned text."""
        btn = tk.Button(
            master= self,
            text=f"{text:<15}", font='Arial 12',
            bg='#505050', fg='#FFFFFF',
            activebackground='#3C3B3B', activeforeground='#FFFFFF',
            width=15, anchor='w',
            borderwidth=0, highlightthickness=0,
            command= lambda: self._toggle_dropdown(text.strip())
        )
        return btn

    def _create_dropdown(self, items):
        """Create a simulated dropdown menu as a Frame with buttons."""
        dropdown = tk.Frame(self.window, bg='#505050')
        dropdown.place_forget()  # Initially hide the dropdown

        for item in items:
            btn = tk.Button(
                master= dropdown,
                text=f"{item:<30}", font='Arial 12',
                bg='#505050', fg='#FFFFFF',
                activebackground='#3C3B3B', activeforeground='#FFFFFF',
                width=20, anchor='w',
                borderwidth=0, highlightthickness=0,
                command=lambda : self._switch(item, )
            )
            btn.pack(fill="x", pady=2)

        return dropdown

    def _toggle_dropdown(self, menu_name):
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
            self._hide_all_dropdowns()
            
            # Calculate button's position and show dropdown below it
            x = menu_button.winfo_rootx() - self.window.winfo_rootx()
            y = menu_button.winfo_rooty() - self.window.winfo_rooty() + menu_button.winfo_height() + 1
            dropdown.place(x=x, y=y)
            dropdown.tkraise()

    def _hide_all_dropdowns(self, event=None):
        """Hide all dropdown menus only if the click is outside dropdowns and buttons."""
        clicked_widget = self.window.winfo_containing(event.x_root, event.y_root) if event else None

        # Check if clicked widget is part of any dropdown or menu button
        if not any(clicked_widget is widget or clicked_widget in widget.winfo_children() 
                for widget in self.dropdowns.keys() | self.dropdowns.values()):
            # Hide all dropdowns if clicked outside
            for dropdown in self.dropdowns.values():
                dropdown.place_forget()

    def _switch(self, name: str):
        """Handle actions for each menu item."""
        # Hide dropdowns after selecting a menu item
        self._hide_all_dropdowns()

        match name:
            case 'Open Folder':
                self.window.root_path = filedialog.askdirectory()
                self.window.select_panel.update_roots(
                    name= 'select_image_treeview', 
                    path= self.window.root_path,
                )
                
            case 'Tutorial':
                messagebox.showinfo("Tutorial", "This is a tutorial message.")


class ImageSelectPanel(tk.Frame):
    def __init__(
        self, parent, window,
        title_label_bg: str = '#303030', title_label_fg: str = '#FFFFFF',
        title_label_font: str = 'Arial 12 bold', 
        title_label_width: int = 25, current_image_tree_height: int = 15,
        *args, **kwargs,
    ) -> None:
        super().__init__(parent, *args, **kwargs)
        # Setup Self in window
        window.select_panel = self
        
        # Current Image Label
        current_image_label = tk.Label(
            master= self,
            text= 'CURRENT IMAGE', font= title_label_font,
            bg = title_label_bg, fg = title_label_fg,
            width= title_label_width, anchor= 'center',
        )
        current_image_label.pack(side=tk.TOP, fill=tk.X, ipady=5)
        
        # Current Image TreeView
        self.current_image_treeview = ttk.Treeview(
            master= self, 
            show= 'tree',
            columns=('fullpath', 'type'),
            displaycolumns=(),
            selectmode="extended",
            height= current_image_tree_height,
        )
        self.current_image_treeview.pack(side=tk.TOP, fill=tk.X)
        
        self.current_image_treeview.bind(sequence= "<<TreeviewSelect>>", func= lambda event: self._select_tree(window, event))
        self.current_image_treeview.bind(sequence= '<<TreeviewOpen>>', func= lambda event: self._update_tree(event))
        
        # Select Image Label
        select_image_label = tk.Label(
            master= self, 
            text= 'SELECT IMAGE', font= title_label_font, 
            bg = title_label_bg, fg = title_label_fg,
            width= title_label_width, anchor= 'center',
        )
        select_image_label.pack(side=tk.TOP, fill=tk.X, ipady=5)
        
        # Select Image TreeView
        self.select_image_treeview = ttk.Treeview(
            master= self, 
            show= 'tree',
            columns=('fullpath', 'type'),
            displaycolumns=(),
            selectmode="browse",
        )
        self.select_image_treeview.pack(side=tk.TOP, fill=tk.BOTH, expand=True,)
        
        self.select_image_treeview.bind(sequence= "<<TreeviewSelect>>", func= lambda event: self._select_tree(window, event))
        self.select_image_treeview.bind(sequence= '<<TreeviewOpen>>', func= lambda event: self._update_tree(event))
    
    def update_roots(self, name, path= None):
        """Populates the tree view with the root directory."""
        if name == 'select_image_treeview': tree = self.select_image_treeview
        elif name == 'current_image_treeview': tree = self.current_image_treeview
        else: return
            
        for item in tree.get_children():
            tree.delete(item)
        
        if path is None: return
        else: path = Path(path)

        tree.heading("#0", text=path.name, anchor='center')
        root_node = tree.insert('', 'end', text=path.name, values=[str(path), "directory"])
        self._populate_tree(tree, root_node)
        
    def _select_tree(self, window: tk.Tk, event):
        tree = event.widget
        file_path = Path(tree.set(tree.selection()[0], "fullpath"))
        if not file_path.is_file(): return
        if file_path.suffix in ('.tif', '.tiff', '.jpg', '.png'):
            window.show_frame('ImageDisplayPanel')
            window.image_display.input_image_path(str(file_path))
            window.image_display._update_keybind('drag')
        
    def _update_tree(self, event):
        """
        Populates the tree view with directories and files.
        """
        tree = event.widget
        node = tree.focus()
        self._populate_tree(tree, node)
        
    def _populate_tree(self, tree, node):
        """
        Populates the tree view with directories and files for a given node.
        """
        path = Path(tree.set(node, "fullpath"))
        tree.delete(*tree.get_children(node))  # Clear existing children

        if not path.is_dir(): return

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
            if tree.set(child, "fullpath") == path: return True
        return False