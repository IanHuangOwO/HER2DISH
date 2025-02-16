import logging
import numpy as np

from utiles import CaseCargo, ImageContainer
from classify import Classifier
from segmentation import Segment
from anaylsis import calculate_all_score
from tools import overlay_signal

# Configure logging to show messages from each process
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

def load_cargo(input_path: str, output_path: str) -> CaseCargo:
    return CaseCargo(input_path=input_path, output_path=output_path)


def run_classifier(
    container: ImageContainer, 
    her2_classifier_path: str, 
    chr17_classifier_path: str,
) -> dict:
    """
    Classify HER2 and Chr17 signals for a single container and return the results.
    Returns a dictionary with the classified masks.
    """
    classifier = Classifier()
    
    container_key = container.name
    existing_images = container.images
    
    result = {}
    
    # Process HER2 signal if not already classified
    if 'her2' not in existing_images:
        logging.info(f"Running HER2 classifier for container '{container_key}'...")
        her2_mask = classifier.run(
            input_img=container.get('raw'),
            classifier_path=her2_classifier_path,
            output_dtype=np.uint16
        )
        result['her2'] = her2_mask
        logging.info(f"HER2 classification completed for container '{container_key}'.")
    else:
        logging.info(f"Skipping HER2 classification for container '{container_key}', already exists.")

    # Process Chr17 signal if not already classified
    if 'chr17' not in existing_images:
        logging.info(f"Running Chr17 classifier for container '{container_key}'...")
        chr17_mask = classifier.run(
            input_img=container.get('raw'),
            classifier_path=chr17_classifier_path,
            output_dtype=np.uint16
        )
        result['chr17'] = chr17_mask
        logging.info(f"Chr17 classification completed for container '{container_key}'.")
    else:
        logging.info(f"Skipping Chr17 classification for container '{container_key}', already exists.")
    
    # Remove signal
    if 'dug' not in existing_images:
        logging.info(f"Running signal removal for container '{container_key}'...")
        from skimage.segmentation import expand_labels
        try: her2_mask 
        except: her2_mask = existing_images['her2']
        try: chr17_mask
        except: chr17_mask = existing_images['chr17']
        
        both_mask = her2_mask + chr17_mask
        both_mask = expand_labels(both_mask, distance=3)
        
        raw_image = container.get('raw')
        temp_image = container.get('raw')
        mask = np.all(np.abs(temp_image - np.mean(raw_image, axis=(0, 1))) > 10, axis=-1)
        temp_image = temp_image[mask]
        
        raw_image[both_mask != 0] = np.mean(temp_image, axis=0)
        result['dug'] = raw_image
        logging.info(f"Signal removal completed for container '{container_key}'.")
    else:
        logging.info(f"Skipping signal removal for container '{container_key}', already exists.")
        
    return result


def run_segmentor(
    container: ImageContainer,
    model_type: str,
) -> dict:
    """
    Run the segmentation process on a given raw image for the specified container key.

    Args:
        container_key (str): Key identifying the container in which the image is stored.
        raw_image (np.ndarray): Raw image data to be segmented.
        model_type (str): Type of model to be used for segmentation ('StarDist', 'Cellpose').
        existing_images (dict): Dictionary of existing images in the container.
    
    Returns:
        dict: Contains the result of segmentation (e.g., cell mask) if it is computed.
    """
    result = {}
    
    container_key = container.name
    existing_images = container.images

    # Process Chr17 signal if it doesn't exist in the existing images
    if 'cell' not in existing_images:
        logging.info(f"Running border segmentation for container '{container_key}'...")
        segmenter = Segment(model_type=model_type, resize_scale=0.333)
        cell_mask = segmenter.run(
            input_img=container.get('dug'),
            output_dtype=np.uint16
        )
        result['cell'] = cell_mask
        logging.info(f"Border Segmentation completed for container '{container_key}'.")
    else:
        logging.info(f"Skipping border segmentation for container '{container_key}', already exists.")
    
    if 'overlay' not in existing_images:
        logging.info(f"Running Signal overlay for container '{container_key}'...")
        overlay_img = overlay_signal(
            image= container.get('raw'),
            mask= container.get('her2'),
            color= [0, 255, 0],
            transparent= 0.5,
        )
        overlay_img = overlay_signal(
            image= overlay_img,
            mask= container.get('chr17'),
            color= [0, 200, 255],
            transparent= 0.5,
        )
        result['overlay'] = overlay_img
        logging.info(f"Signal overlay completed for container '{container_key}'.")
    else:
        logging.info(f"Skipping signal overlay for container '{container_key}', already exists.")
    
    return result


def run_calculation(container: ImageContainer, name: str) -> list:
    """
    Run the score calculation for a single container.

    Args:
        container (ImageContainer): The container with masks for cell, HER2, and Chr17.
    
    Returns:
        None
    """
    
    logging.info(f"Calculating cell score for container '{container.name}'...")
    # Calculate the cell score
    cell_score = calculate_all_score(
        name= name,
        cell_mask=container.get('cell'),
        her2_mask=container.get('her2'),
        chr17_mask=container.get('chr17'),
    )
    logging.info(f"Cell score calculation completed for container '{container.name}'.")
    
    return cell_score

def process_parallel(
    cargo: CaseCargo,
    her2_classifier_path: str,
    chr17_classifier_path: str,
    model_type: str,
) -> None:
    
    container_keys = cargo.get_container_keys()
    
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor() as executor:
        # Submit each container classification task and return results
        classifier = {
            key: executor.submit(
                run_classifier,
                cargo.get_container(key), 
                her2_classifier_path, 
                chr17_classifier_path,
            )
            for key in container_keys
        }
        
        # Collect the results and update the cargo in the main process
        for key, future in classifier.items():
            result = future.result()
            container = cargo.get_container(key)
            if 'her2' in result:
                container.add_image('her2', result['her2'])
            if 'chr17' in result:
                container.add_image('chr17', result['chr17'])
            if 'dug' in result:
                container.add_image('dug', result['dug'])
        
        # Submit each container segmentation task and return results
        segmentor = {
            key: executor.submit(
                run_segmentor,
                cargo.get_container(key), 
                model_type,
            )
            for key in container_keys
        }
        
        # Collect the results and update the cargo in the main process
        for key, future in segmentor.items():
            result = future.result()
            container = cargo.get_container(key)
            if 'cell' in result:
                container.add_image('cell', result['cell'])
            if 'overlay' in result:
                container.add_image('overlay', result['overlay'])
        
        # Submit each container calculation task and return results  
        calculator = {
            key: executor.submit(
                run_calculation,
                cargo.get_container(key),
                key,
            )
            for key in container_keys
        }
        
        # Collect the results and update the cargo in the main process
        sorted_results = [future.result() for future in calculator.values()]
        
        import heapq

        # Perform a k-way merge using heapq.merge()
        sorted_temp = list(heapq.merge(*sorted_results, key=lambda x: -float(x[1])))

        # Convert back to a NumPy array if needed
        cargo.all_cell_score = np.array(sorted_temp)