import numpy as np

class Segment:
    """
    A class for performing image segmentation using either the StarDist or Cellpose models.
    
    This class encapsulates the functionality required to segment images of cells or nuclei
    in microscopy data. It provides options to preprocess images by removing specific signals,
    resizing, and normalizing before feeding them into the segmentation models. The segmentation
    can be performed using either the StarDist or Cellpose models, based on the user's choice.
    
    Attributes:
        model_type (str): Type of the model to use ('StarDist' or 'Cellpose').
        remove_signal (bool): Whether to remove specific signals from the image.
        resize_scale (float): Scale factor for resizing the image.
        
        stardist_model_name (str): Name of the pretrained StarDist model to use.
        stardist_prob_thresh (float): Probability threshold for StarDist predictions.
        stardist_nms_thresh (float): Non-maximum suppression threshold for StarDist.
        
        cellpose_model_name (str): Name of the Cellpose model to use.
        cellpose_gpu (bool): Whether to use GPU acceleration for Cellpose.
        cellpose_diameter (int): Estimated diameter of objects for Cellpose.
        cellpose_channels (list): Channels to use for Cellpose ([0,0] for grayscale).
        flow_threshold (float): Flow threshold parameter for Cellpose.
        cellprob_threshold (float): Cell probability threshold for Cellpose.
        
        model: Loaded segmentation model instance (StarDist or Cellpose).
    """

    def __init__(
        self,
        model_type: str = 'StarDist',
        resize_scale: float = 1,
        
        stardist_model_name: str = '2D_versatile_he',
        stardist_prob_thresh: float = 0.375,
        stardist_nms_thresh: float = 0.0,
        
        cellpose_model_name: str = 'cyto3',
        cellpose_gpu: bool = False,
        cellpose_diameter: int = 50,
        cellpose_channels: list = [0, 0],
        cellpose_flow_threshold: float = 3,
        cellpose_cellprob_threshold: float = -2,
    ) -> None:
        '''
        Initializes the Segment class with specified parameters.
        
        Parameters:
            model_type (str): Type of the model to use ('StarDist' or 'Cellpose').
            remove_signal (bool): Whether to remove specific signals from the image.
            resize_scale (float): Scale factor for resizing the image.
            
            stardist_model_name (str): Name of the pretrained StarDist model to use.
            stardist_prob_thresh (float): Probability threshold for StarDist predictions.
            stardist_nms_thresh (float): Non-maximum suppression threshold for StarDist.
            
            cellpose_model_name (str): Name of the Cellpose model to use.
            cellpose_gpu (bool): Whether to use GPU acceleration for Cellpose.
            cellpose_diameter (int): Estimated diameter of objects for Cellpose.
            cellpose_channels (list): Channels to use for Cellpose ([0,0] for grayscale).
            cellpose_flow_threshold (float): Flow threshold parameter for Cellpose.
            cellprob_threshold (float): Cell probability threshold for Cellpose.
        '''
        # Store initialization parameters
        self.model_type = model_type
        self.resize_scale = resize_scale
        
        self.stardist_model_name = stardist_model_name
        self.stardist_prob_thresh = stardist_prob_thresh
        self.stardist_nms_thresh = stardist_nms_thresh
        
        self.cellpose_model_name = cellpose_model_name
        self.cellpose_gpu = cellpose_gpu
        self.cellpose_channels = cellpose_channels
        self.cellpose_diameter = cellpose_diameter
        self.flow_threshold = cellpose_flow_threshold
        self.cellprob_threshold = cellpose_cellprob_threshold
        
        from filelock import FileLock
        
        # Load the appropriate segmentation model based on model_type
        if self.model_type == 'StarDist':
            from stardist.models import StarDist2D
            # Use a file lock to prevent concurrent access to the model weights
            with FileLock("stardist_model.lock"):  # Lock file ensures only one process loads the model at a time
                # Load a pretrained StarDist2D model
                self.model = StarDist2D.from_pretrained(self.stardist_model_name)
        elif self.model_type == 'Cellpose':
            from cellpose import models
            with FileLock("cellpose_model.lock"):
                # Initialize a CellposeModel with specified parameters
                self.model = models.CellposeModel(
                    gpu=self.cellpose_gpu, 
                    model_type=self.cellpose_model_name,
                )
        else:
            # Raise an error if an unsupported model_type is provided
            raise ValueError(f"Unsupported model_type: {self.model_type}")

    def run(
        self,
        input_img: np.ndarray,
        output_dtype: str = np.uint16,
    ) -> np.ndarray:
        """
        Executes the segmentation pipeline on the input image.
        
        Parameters:
            img (np.ndarray): The input image to segment.
            her2_mask (np.ndarray): Mask for HER2 signal to remove.
            chr17_mask (np.ndarray): Mask for Chr17 signal to remove.
        
        Returns:
            Tuple[np.ndarray, np.ndarray]: A tuple containing the normalized image and the segmentation mask.
        """
        from cv2 import resize, INTER_AREA, INTER_NEAREST
        from csbdeep.utils import normalize
        
        # Store the original image dimensions
        old_width = int(input_img.shape[1])
        old_height = int(input_img.shape[0])
        
        # Calculate the new dimensions based on the resize scale
        new_width = int(input_img.shape[1] * self.resize_scale)
        new_height = int(input_img.shape[0] * self.resize_scale)
        
        # Resize the image to reduce computation time and memory usage
        img_resized = resize(input_img, (new_width, new_height), interpolation=INTER_AREA)
        
        # Normalize the resized image to enhance contrast for segmentation
        img_normalized = normalize(img_resized, 1, 99.8)

        # Perform segmentation using the selected model
        if self.model_type == 'StarDist':
            # Run the StarDist segmentation method
            mask = self.run_stardist(img_normalized)
        elif self.model_type == 'Cellpose':
            # Run the Cellpose segmentation method
            mask = self.run_cellpose(img_normalized)
        else:
            # Raise an error if an unsupported model_type is encountered
            raise ValueError(f"Unsupported model_type: {self.model_type}")

        # Resize the segmentation mask back to the original image dimensions
        mask_resized = resize(mask, (old_width, old_height), interpolation=INTER_NEAREST).astype(np.uint16)
        
        # Return the normalized image and the resized segmentation mask
        return mask_resized.astype(output_dtype)

    def run_stardist(self, img: np.ndarray) -> np.ndarray:
        """
        Performs segmentation using the StarDist model.
        
        Parameters:
            img (np.ndarray): The preprocessed and normalized image.
        
        Returns:
            np.ndarray: The segmentation mask produced by StarDist.
        """
        from skimage.segmentation import expand_labels
        
        # Predict instances using the StarDist model with specified thresholds
        mask, _ = self.model.predict_instances(
            img=img,
            prob_thresh=self.stardist_prob_thresh,
            nms_thresh=self.stardist_nms_thresh,
        )
        # Expand the labels in the mask to cover neighboring pixels
        mask = expand_labels(mask, distance=2)
        return mask

    def run_cellpose(self, img: np.ndarray) -> np.ndarray:
        """
        Performs segmentation using the Cellpose model.
        
        Parameters:
            img (np.ndarray): The preprocessed and normalized image.
        
        Returns:
            np.ndarray: The segmentation mask produced by Cellpose.
        """
        # Evaluate the image using the Cellpose model with specified parameters
        mask, _, _ = self.model.eval(
            x=img, 
            channels=self.cellpose_channels, 
            diameter=self.cellpose_diameter,
            flow_threshold=self.flow_threshold,
            cellprob_threshold=self.cellprob_threshold,
        )
        return mask