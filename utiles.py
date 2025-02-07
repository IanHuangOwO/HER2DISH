import numpy as np
import pandas as pd

from pathlib import Path
from typing import Dict, List, Union
from PIL import Image

class ImageContainer:
    def __init__(self, image_path: str, output_path: str) -> None:
        """
        Initialize the container with an image path and output path.
        If any additional images (her2, chr17, dug, etc.) exist in the output path, they will be loaded.

        Args:
            image_path (str): Path to the raw image.
            output_path (str): Path to the output directory where images will be saved.

        Attributes:
            images (Dict[str, np.ndarray]): Dictionary storing image arrays.
            labels (List[str]): List of possible image labels.
            output_path (Path): Path object for the output directory.
            name (str): Base name of the image.
            extension (str): Extension of the image file.
        """
        self.images: Dict[str, np.ndarray] = {}
        self.cell_score: Dict[str, np.ndarray] = {}
        self.labels: List[str] = ['raw', 'her2', 'chr17', 'dug', 'cell', 'overlay']
        self.output_path: Path = Path(output_path)
        self.name: Union[str, None] = None
        self.extension: Union[str, None] = None
        
        # Load the raw image and check for the existence of other images
        self._load_raw_image(image_path)
        self._check_and_load_images()

    def _load_raw_image(self, image_path: str) -> None:
        """Load the raw image from the given file path."""
        self.path = Path(image_path)
        self.name = self.path.stem
        self.extension = self.path.suffix.lower()

        if self.extension not in ['.tiff', '.tif', '.jpg', '.jpeg', '.png']:
            raise ValueError(f"Unsupported file extension for raw image: {self.extension}")

        # Use the _input_path function to load the 'raw' image
        self._input_path('raw', image_path)
        # Save the 'raw' image after loading
        self._save('raw')
    
    def _check_and_load_images(self) -> None:
        """Check if additional images (her2, chr17, dug, etc.) exist in the output path and load them."""
        for label in self.labels[1:]:  # Skip the 'raw' label
            potential_image_path = self.output_path / f'{self.name}_{label}.tif'
            if potential_image_path.exists():
                self._input_path(label, potential_image_path)

    def add_image(self, label: str, data: Union[str, np.ndarray]) -> None:
        """
        Add an image to the container.
        
        Args:
            label (str): The label for the image (e.g., 'her2', 'chr17').
            data (str or np.ndarray): Either a path to the image or the NumPy array of the image.
        """
        if label not in self.labels:
            raise ValueError(f"Invalid label: {label}. Expected one of {self.labels}.")

        if isinstance(data, str):
            self._input_path(label, data)  # Load from path
        elif isinstance(data, np.ndarray):
            self._input_array(label, data)  # Load from NumPy array
        else:
            raise ValueError(f"Unsupported input type for {label}. Expected a file path (str) or a NumPy array.")

        # Automatically save after adding the image
        self._save(label)
        
    def _input_path(self, label: str, input_path: Path) -> None:
        """Load an image from the given file path and add it to the container."""
        try:
            with Image.open(input_path) as img:
                img_array = np.array(img)
                self.images[label] = img_array
                
        except Exception as e:
            print(f"Error loading image for {label} at {input_path}: {e}")

    def _input_array(self, label: str, input_array: np.ndarray) -> None:
        """Add an image directly from a NumPy array."""
        if label in ['her2', 'chr17', 'cell']:
            # Ensure these are grayscale 16-bit images
            if input_array.ndim != 2 or input_array.dtype != np.uint16:
                raise ValueError(f"{label} must be a grayscale 16-bit image.")
        elif label in ['dug', 'overlay']:
            # Ensure dug is RGB
            if input_array.ndim != 3 or input_array.shape[2] != 3:
                raise ValueError(f"{label} must be an RGB image.")
        
        self.images[label] = input_array
        
    def _save(self, label: str) -> None:
        """Save the specified image using the stored output path with the format."""
        try:
            img = self.images[label]
            output_file_path = self.output_path / f'{self.name}_{label}.tif'
            img_pil = Image.fromarray(img)
            img_pil.save(output_file_path)
        except Exception as e:
            raise RuntimeError(f"Error saving image {label} to {output_file_path}: {e}")
        
    def get(self, label: str) -> np.ndarray:
        """Return a copy of the image array for the specified label."""
        return np.copy(self.images[label])
    
    def delete(self, label: str):
        """Delete the image array for the specified label."""
        if label in self.images:
            self.images.pop(label)
        
class CaseCargo:
    def __init__(self, input_path: str, output_path: str) -> None:
        """
        Initialize the CaseCargo class with input and output paths.
        The input_path contains raw images, and each raw image will create a new ImageContainer.
        All output folders for the containers will be stored within the base output directory.
        Containers are stored in a dictionary for easy access.

        Args:
            input_path (str): The path where the raw images are located.
            output_path (str): The base output directory where all the container folders will be saved.
        """
        self.input_path: Path = Path(input_path)
        self.output_path: Path = Path(output_path) / f'{self.input_path.stem}_output'
        self.report_path: Path = self.output_path / f'Final-Report_{self.input_path.stem}.png'
        self.all_cell_excel_path: Path = self.output_path / f'{self.input_path.stem}_all-cell-score.xlsx'
        self.report_excel_path: Path = self.output_path / f'Final-Report_{self.input_path.stem}.xlsx'
        self.all_cell_score: List = []
        self.final_cell_score: List = []
        # Ensure the input path exists
        if not self.input_path.exists():
            raise ValueError(f"Input path {self.input_path} does not exist.")

        # Ensure the base output folder exists or create it
        self.output_path.mkdir(parents=True, exist_ok=True)

        # Dictionary to store ImageContainers
        self.containers: Dict[str, ImageContainer] = {}
        
        # Create containers for each raw image
        self.create_containers()
        self._load_existing_excel()

    def list_images(self) -> List[Path]:
        """
        List all raw image files in the input path directory.
        
        Returns:
            List[Path]: A list of raw image file paths.
        """
        # Supported raw image extensions
        supported_extensions = ['.tiff', '.tif', '.jpg', '.jpeg', '.png']

        # Get list of raw image paths
        image_paths = [f for f in self.input_path.iterdir() if f.suffix.lower() in supported_extensions]
        return image_paths

    def create_containers(self) -> None:
        """
        Create a new ImageContainer for each raw image in the input path.
        Each container will be initialized with the raw image and output path,
        and will automatically check for the existence of additional images (her2, chr17, etc.).
        The output folders for all containers will be stored in the base output folder.
        Containers are stored in a dictionary for easy access.
        """
        image_paths = self.list_images()

        for image_path in image_paths:
            # Derive the container name from the raw image file name (without extension)
            container_name = image_path.stem

            # Create a unique output directory for this container inside the base output folder
            container_output_path = self.output_path / container_name
            container_output_path.mkdir(parents=True, exist_ok=True)

            # Create a new ImageContainer for this raw image
            image_container = ImageContainer(str(image_path), str(container_output_path))

            # Store the container in the dictionary with the container_name as the key
            self.containers[container_name] = image_container

    def get_container(self, name: str) -> ImageContainer:
        """
        Retrieve an ImageContainer by name from the dictionary.
        
        Args:
            name (str): The name of the container to retrieve (i.e., the raw image file name).
        
        Returns:
            ImageContainer: The corresponding ImageContainer.
        """
        return self.containers.get(name)

    def get_container_keys(self) -> List[str]:
        """
        Return the keys of the containers dictionary.
        
        Returns:
            List[str]: A list of keys in the containers dictionary.
        """
        return list(self.containers.keys())
        
    def _load_existing_excel(self) -> None:
        """
        Check if final_cell_score exist in the output path and load them.
        """
        if not self.report_excel_path.exists():
            return

        try:
            df = pd.read_excel(self.report_excel_path)
        except Exception as e:
            raise ValueError(f"Error loading Excel file: {e}")
        
        from tkinter import messagebox
        response = messagebox.askquestion(
            "Question", 
            f"Found existing progress.\n\nDo you wish to load and continue ?"
        )
        if response == 'no': return
        
        temp = df.values.tolist()[1:21]
        
        if len(temp[0]) > 3:
            self.final_cell_score = [None] * 40
            for idx, element in enumerate(temp):
                self.final_cell_score[idx] = element[:3]
                self.final_cell_score[idx + 20] = element[3:]
                
        else:
            self.final_cell_score = temp
            
        