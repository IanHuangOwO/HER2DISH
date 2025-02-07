import numpy as np

class Classifier:
    """
    A classifier for image segmentation using pre-trained models and multiscale features.
    """

    def __init__(
        self,
        resize_scale: float = 1,
        advanced_features: bool = True,
        intensity: bool = True,
        edges: bool = False,
        texture: bool = True,
        sigma_min: int = 1,
        sigma_max: int = 8,
        channel_axis: int = -1,
    ) -> None:
        """
        Initialize the classifier with given parameters.

        Parameters:
        - advanced_features (bool): Whether to use advanced multiscale features.
        - intensity (bool): Include intensity features in multiscale features.
        - edges (bool): Include edge features in multiscale features.
        - texture (bool): Include texture features in multiscale features.
        - sigma_min (int): Minimum sigma for Gaussian blur in multiscale features.
        - sigma_max (int): Maximum sigma for Gaussian blur in multiscale features.
        - channel_axis (int): The axis corresponding to color channels in the image.
        """
        self.resize_scale = resize_scale
        self.advanced_features = advanced_features
        self.intensity = intensity
        self.edges = edges
        self.texture = texture
        self.sigma_min = sigma_min
        self.sigma_max = sigma_max
        self.channel_axis = channel_axis

    def run(
        self,
        input_img: np.ndarray,
        classifier_path: str,
        output_dtype: np.dtype = np.uint16,
    ) -> np.ndarray:
        """
        Run the classifier on the given image and generate a segmentation mask.

        Parameters:
        - input_img (np.ndarray): The input image array.
        - classifier_path (str): Path to the pre-trained classifier file.
        - output_dtype (np.dtype): Desired data type of the output mask.

        Returns:
        - np.ndarray: Segmentation mask with values mapped according to the desired dtype.
        """
        # Load the pre-trained classifier from the given path
        import joblib
        
        from skimage import feature, future
        from functools import partial
        
        try:
            classifier = joblib.load(classifier_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Classifier file not found at '{classifier_path}'.")
        except Exception as e:
            raise RuntimeError(f"An error occurred while loading the classifier: {e}")

        # Create a partial function for multiscale feature extraction with predefined parameters
        extract_features = partial(
            feature.multiscale_basic_features,
            intensity=self.intensity,
            edges=self.edges,
            texture=self.texture,
            sigma_min=self.sigma_min,
            sigma_max=self.sigma_max,
            channel_axis=self.channel_axis,
        )
        
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
        
        # Extract features if advanced_features is True, else use the original image
        if self.advanced_features:
            features = extract_features(img_resized)
            # Predict segmentation using the extracted features
            mask = future.predict_segmenter(features, classifier)
        else:
            # Predict segmentation directly on the image
            mask = future.predict_segmenter(img_resized, classifier)

        # Resize the segmentation mask back to the original image dimensions
        mask_resized = resize(mask, (old_width, old_height), interpolation=INTER_NEAREST)

        # Convert the mask to the specified output_dtype
        mask_resized = mask_resized.astype(output_dtype)

        # Get the highest value for the output dtype (e.g., 255 for uint8, 65535 for uint16)
        max_value = np.iinfo(output_dtype).max if np.issubdtype(output_dtype, np.integer) else 1.0

        # Map the mask values: 1 -> 0, 2 -> max_value
        mask_resized = np.where(mask_resized == 1, 0, mask_resized)
        mask_resized = np.where(mask_resized == 2, max_value, mask_resized)
        
        return mask_resized
    

def run_classifier(img, classifier_path):
    """
    Runs the classifier on the given image and classifier path.

    Parameters:
    - img (np.ndarray): The input image array.
    - classifier_path (str): Path to the classifier model.

    Returns:
    - np.ndarray: The resulting mask from the classifier.
    """
    classifier = Classifier()
    
    result = classifier.run(
        input_img=img,
        classifier_path=classifier_path,
    )
    return result