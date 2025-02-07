import numpy as np
from scipy.ndimage import label, center_of_mass, gaussian_filter
from skimage.measure import regionprops
from typing import List, Dict, Tuple

def calculate_all_score(
    name: str,
    cell_mask: np.ndarray,
    her2_mask: np.ndarray,
    chr17_mask: np.ndarray,
) -> list:
    """
    Calculates HER2/Chr17 ratios for cells and compiles results.

    Parameters:
    - cell_mask (np.ndarray): Labeled mask of cells.
    - her2_mask (np.ndarray): Binary mask of HER2 signals.
    - chr17_mask (np.ndarray): Binary mask of Chr17 signals.

    Returns:
    - Dictionary mapping cell label to ratio data.
    """
    
    her2_mask = heatmap_mask(her2_mask, 50, 0.5)
    
    her2_center = get_center(her2_mask)
    chr17_center = get_center(chr17_mask)
    
    # Calculate signals and scores for cells
    cell_signal = calculate_cell_signal(
        cell_mask=cell_mask,
        her2_center=her2_center,
        chr17_center=chr17_center,
    )
    
    cell_score = calculate_score(
        name= name,
        cell_mask= cell_mask,
        cell_signal= cell_signal,
    )
    
    return cell_score

def calculate_cell_score(
    cell_mask: np.ndarray,
    her2_mask: np.ndarray,
    chr17_mask: np.ndarray,
) -> Dict[int, np.ndarray]:
    """
    Calculates HER2/Chr17 ratios for cells and compiles results.

    Parameters:
    - cell_mask (np.ndarray): Labeled mask of cells.
    - her2_mask (np.ndarray): Binary mask of HER2 signals.
    - chr17_mask (np.ndarray): Binary mask of Chr17 signals.

    Returns:
    - Dictionary mapping cell label to ratio data.
    """
    
    her2_center = get_center(her2_mask)
    chr17_center = get_center(chr17_mask)
    
    # Calculate signals and scores for cells
    cell_signal = calculate_cell_signal(
        cell_mask=cell_mask,
        her2_center=her2_center,
        chr17_center=chr17_center,
    )
    
    return cell_signal
    
    
def heatmap_mask(
    mask: np.ndarray, 
    sigma: int = 50, 
    threshold: float = 0.5,
) -> np.ndarray:
    """
    Applies a Gaussian filter to the mask and thresholds the result to create a heatmap.

    Parameters:
    - mask (np.ndarray): Input binary mask.
    - sigma (float): Standard deviation for Gaussian kernel.
    - threshold (float): Threshold value to filter the heatmap.

    Returns:
    - np.ndarray: Masked heatmap where values above the threshold are retained.
    """
    heatmap = gaussian_filter(mask.astype(float), sigma=sigma)  # Smooth the mask
    heatmap_filtered = np.where(heatmap > threshold, heatmap, 0)  # Apply threshold
    masked_heatmap = np.where(heatmap_filtered > 0, mask, 0)  # Retain original mask values above threshold

    return masked_heatmap


def get_center(
    mask: np.ndarray,
) -> List[Tuple[float, float]]:
    """
    Computes the centers of mass for labeled regions in the mask.

    Parameters:
    - mask (np.ndarray): Binary mask with features.

    Returns:
    - List[Tuple[float, float]]: List of (row, column) coordinates for each region's center of mass.
    """
    labeled_mask, _ = label(mask)  # Label connected components
    labels = np.unique(labeled_mask)  # Get unique labels
    labels = labels[labels != 0]  # Exclude background label (0)
    return center_of_mass(mask, labeled_mask, labels)  # Compute centers of mass


def calculate_cell_signal(
    cell_mask: np.ndarray,
    her2_center: List[Tuple[float, float]],
    chr17_center: List[Tuple[float, float]],
) -> Dict[int, np.ndarray]:
    """
    Calculates signal counts for HER2 and Chr17 within each cell.

    Parameters:
    - cell_mask (np.ndarray): Labeled mask of cells.
    - her2_center (List[Tuple[float, float]]): Centers of HER2 signals.
    - chr17_center (List[Tuple[float, float]]): Centers of Chr17 signals.

    Returns:
    - cell_signal (Dict[int, np.ndarray]): Mapping of cell label to [HER2 count, Chr17 count].
    """
    cell_signal = {}  # Initialize dictionary to store signals per cell

    # Count HER2 signals per cell
    for x, y in her2_center:
        current_label = int(cell_mask[int(x), int(y)])  # Get cell label at signal position
        if current_label == 0:
            
            continue  # Skip if not within a cell
        if current_label in cell_signal:
            cell_signal[current_label][0] += 1  # Increment HER2 count
        else:
            cell_signal[current_label] = np.array([1, 0])  # Initialize counts

    # Count Chr17 signals per cell
    for x, y in chr17_center:
        current_label = int(cell_mask[int(x), int(y)])
        if current_label == 0:
            continue
        if current_label in cell_signal:
            cell_signal[current_label][1] += 1  # Increment Chr17 count
        else:
            cell_signal[current_label] = np.array([0, 1])
    
    return cell_signal


def calculate_score(
    name: str,
    cell_mask: np.ndarray,
    cell_signal: Dict[int, np.ndarray],
) -> list:

    # Extract counts for statistical calculations
    her2_list = [value[0] for value in cell_signal.values()]  # HER2 counts
    # chr17_list = [value[1] for value in cell_signal.values()]  # Chr17 counts
    ratio_list = [value[0] / value[1] for value in cell_signal.values() if value[1] != 0]  # Ratios

    # Compute cell mask statistics
    _, counts = np.unique(cell_mask, return_counts=True)
    cell_std = np.std(counts)
    cell_avg = sum(counts) / len(counts)

    # Compute HER2 statistics
    her2_std = np.std(her2_list)
    her2_avg = sum(her2_list) / len(her2_list)

    # Compute Chr17 statistics
    # chr17_std = np.std(chr17_list)
    # chr17_avg = sum(chr17_list) / len(chr17_list)

    # Determine ratio range
    ratio_max = max(ratio_list)
    ratio_min = min(ratio_list)
    
    cell_score = []  # Initialize dictionary to store scores per cell
    
    # Calculate scores for each cell based on various factors
    for region in regionprops(cell_mask):
        cell_label = region.label
        try:
            her2, chr17 = cell_signal[cell_label]
        except KeyError:
            continue  # Skip if cell has no signals

        if her2 < 1 or chr17 < 1:
            continue
        
        # Calculate individual scores
        area_score = calculate_area_score(
            value=region.area,
            avg=cell_avg,
            std=cell_std,
        )

        her2_score = calculate_her2_score(
            value=her2,
            avg=her2_avg,
            std=her2_std,
        )

        chr17_score = calculate_chr17_score(
            value=chr17,
        )

        ratio_score = calculate_ratio_score(
            her2_value=her2,
            chr17_value=chr17,
            ratio_max=ratio_max,
            ratio_min=ratio_min,
        )
        
        sphericity_score = calculate_sphericity(
            region=region,
        )
        
        ratio = round(float(her2 / chr17), 4)

        score = round((
            1 * her2_score + 
            1 * chr17_score + 
            1 * ratio_score +
            1 * area_score + 
            1 * sphericity_score
        ), 6)
        
        
        # Aggregate scores with assigned weights
        insert_descending_by_score(
            cell_score, 
            [name, cell_label, ratio, her2, chr17, score]
        )
        
    return cell_score


def calculate_area_score(value, avg, std, alph=1, beta=4):
    """
    Calculates a score based on cell area.

    Parameters:
    - value: The area of the cell.
    - avg: The average cell area.
    - std: The standard deviation of cell areas.
    - alph: Scaling factor (default=1).
    - beta: Exponent factor (default=4).

    Returns:
    - Score representing how the cell's area compares to the average.
    """
    return 1 - ((value - avg) / (alph * std)) ** beta


def calculate_sphericity(region):
    """
    Calculates the sphericity (compactness) of a cell.

    Parameters:
    - region: Region properties of the cell.

    Returns:
    - Sphericity score ranging from 0 to 1.
    """
    area = region.area
    perimeter = region.perimeter
    if perimeter == 0:
        return 0
    sphericity = (4 * np.pi * area) / (perimeter ** 2)
    return sphericity


def calculate_her2_score(value, avg, std):
    """
    Calculates a score for HER2 signal count.

    Parameters:
    - value: HER2 count for the cell.
    - avg: Average HER2 count across cells.
    - std: Standard deviation of HER2 counts.

    Returns:
    - Score based on how the HER2 count deviates from the average.
    """
    if value > avg + 3*std:
        return 0.5
    elif value < avg - std:
        return 0
    else:
        return 1


def calculate_chr17_score(value):
    """
    Calculates a score for Chr17 signal count.

    Parameters:
    - value: Chr17 count for the cell.
    - avg: Average Chr17 count across cells.
    - std: Standard deviation of Chr17 counts.

    Returns:
    - Score indicating sufficiency of Chr17 signals.
    """
    if value < 2:
        return 0.5
    else:
        return 1
    

def calculate_ratio_score(her2_value, chr17_value, ratio_max, ratio_min):
    """
    Calculates a normalized score based on the HER2/Chr17 ratio.

    Parameters:
    - her2_value: HER2 count for the cell.
    - chr17_value: Chr17 count for the cell.
    - ratio_max: Maximum ratio observed across cells.
    - ratio_min: Minimum ratio observed across cells.

    Returns:
    - Normalized ratio score.
    """
    if chr17_value == 0:
        return float('inf')  # Avoid division by zero

    value = her2_value / chr17_value

    if ratio_max == ratio_min:
        return 0  # Cannot normalize if all ratios are the same

    return (value - ratio_min) / (ratio_max - ratio_min)

def insert_descending_by_score(cell_score, new_record):
    """
    Insert new_record into the cell_score list,
    maintaining descending order by the score (last element).
    """
    new_score = new_record[-1]  # The score is the last element in the record
    i = 0
    # Advance i while the existing element's score is >= new_score
    while i < len(cell_score) and cell_score[i][-1] >= new_score:
        i += 1
    
    # Insert at the found position
    cell_score.insert(i, new_record)
