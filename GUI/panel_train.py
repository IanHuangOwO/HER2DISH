import tkinter as tk

class TrainPanel(tk.Frame):
    def __init__(
        self, window: tk.Tk, parent: tk.Widget,
        button_width: int = 30, button_height: int = 3,
        button_font: str = 'Arial 12 bold',
        button_background: str = '#454545',button_foreground: str = '#FFFFFF',
        active_background: str = '#3C3B3B', active_foreground: str = '#FFFFFF',
        *args, **kwargs,
    ) -> None:
        super().__init__(parent, bg='#333333', *args, **kwargs)
        
        # Pre-run Analysis Label
        top_label = tk.Label(
            master= self, 
            text= 'Train Classifier', font= 'Arial 12 bold',
            bg= '#292929', fg= '#FFFFFF',
            width= 25, anchor= 'center',
        )
        top_label.pack(side=tk.TOP, fill=tk.X, ipady=5)
        
        # Process Button
        button_frame = tk.Frame(master=self, bg='#333333',)
        button_frame.pack(expand=True)
        
        # Train Button
        train_button = tk.Button(
            master=button_frame,
            text='Train Classifier', font=button_font,
            bg=button_background, fg=button_foreground,
            activebackground=active_background, activeforeground=active_foreground,
            width=button_width, height=button_height,
            borderwidth=0, highlightthickness=0,
            command=lambda: self._train(window),
        )
        train_button.grid(row=1, column=0, pady=20)
        
        # Train Button
        save_button = tk.Button(
            master=button_frame,
            text='Save Classifier', font=button_font,
            bg=button_background, fg=button_foreground,
            activebackground=active_background, activeforeground=active_foreground,
            width=button_width, height=button_height,
            borderwidth=0, highlightthickness=0,
            command=lambda: self._save(),
        )
        save_button.grid(row=2, column=0, pady=20)
        
        # Step Button
        previous_step_button = tk.Button(
            master= self, 
            text= 'Back', font= 'Arial 12',
            bg= button_background, fg= button_foreground, 
            activebackground= active_background, activeforeground= active_foreground, 
            borderwidth=0, highlightthickness=0,
            command= lambda: self._show_previous(window)
        )
        previous_step_button.pack(side=tk.BOTTOM, fill=tk.X)
        
    def _train(self, window: tk.Tk) -> None:
        import cv2
        import numpy as np
        from functools import partial
        from sklearn.ensemble import RandomForestClassifier
        from skimage import feature, future

        # Load images
        train_display = window.train_display
        raw_image = train_display.display_img.copy()
        foreground_mask = cv2.cvtColor(train_display.foreground_mask, cv2.COLOR_BGR2GRAY)
        background_mask = cv2.cvtColor(train_display.background_mask, cv2.COLOR_BGR2GRAY)

        # Assign class labels: Foreground (2), Background (1)
        foreground_mask[foreground_mask != 0] = 2
        background_mask[background_mask != 0] = 1
        combined_mask = foreground_mask + background_mask

        # Feature extraction function
        features_func = partial(
            feature.multiscale_basic_features,
            intensity=True,
            edges=False,
            texture=True,
            sigma_min=1,
            sigma_max=8,
            channel_axis=-1,
        )
        features = features_func(raw_image)

        # Train and predict segmentation using RandomForest
        self.clf = RandomForestClassifier()
        self.clf = future.fit_segmenter(combined_mask, features, self.clf)
        resulting_mask = future.predict_segmenter(features, self.clf)

        # Define color mappings
        HER2_COLOR = [0, 255, 0]   # Green for HER2
        CHR17_COLOR = [0, 200, 255] # Orange for Chr17

        # Update masks based on predictions
        foreground_mask[resulting_mask == 2] = 255
        background_mask[resulting_mask == 1] = 255

        # Convert to color and apply HER2 & Chr17 overlays
        foreground_mask = cv2.cvtColor(foreground_mask.astype(np.uint8), cv2.COLOR_GRAY2BGR)
        foreground_mask[np.all(foreground_mask == [255, 255, 255], axis=-1)] = HER2_COLOR

        background_mask = cv2.cvtColor(background_mask.astype(np.uint8), cv2.COLOR_GRAY2BGR)
        background_mask[np.all(background_mask == [255, 255, 255], axis=-1)] = CHR17_COLOR

        # Store result
        train_display.resulting_mask = foreground_mask + background_mask

        # Update keybinds
        train_display._update_keybind('all')
    
    def _save(self) -> None:
        import os
        import joblib
        from tkinter import simpledialog, messagebox
        
        model_type = simpledialog.askstring("Model Selection", "Enter the model type (HER2 or Chr17):").lower()
        if model_type == 'her2':
            base_path = r'.\classifier\HER2'
        elif model_type == 'chr17':
            base_path = r'.\classifier\CHR17'
        else:
            messagebox.showwarning('Invalid option', 'Please enter a valid option')
        
        model_name = simpledialog.askstring("Model Name", "Please enter the model name:")
        
        save_path = os.path.join(base_path, f'{model_name}.joblib')
        
        joblib.dump(self.clf, save_path)
        
    def _show_previous(self, window: tk.Tk) -> None:
        window.show_frame('FirstPanel')