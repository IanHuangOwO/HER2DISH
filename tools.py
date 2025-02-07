import cv2
import numpy as np

from typing import Dict, Tuple, List
from PIL import Image, ImageDraw, ImageFont

def overlay_signal(
    image: np.ndarray,
    mask: np.ndarray,
    color: list,
    transparent: float,
) -> np.ndarray:
    # Make copies of the image and mask to avoid altering original data
    image_copy = image.copy()
    mask_copy = mask.copy()

    # Process mask for overlay visualization
    mask_colored = cv2.cvtColor(mask_copy.astype(np.uint8), cv2.COLOR_GRAY2BGR)
    mask_colored[np.where((mask_colored == [255, 255, 255]).all(axis=2))] = color
    
    # Create overlay image by combining raw image with masks
    overlay_img = cv2.addWeighted(image_copy, 1, mask_colored, transparent, 0)
    
    return overlay_img

def cropping_region(
    input_cell_mask: np.ndarray,
    id_value: int,
    extend: int
) -> Tuple[int, int, int, int, np.ndarray, List[np.ndarray]]:
    """
    Isolates a specific cell in the mask and calculates cropping coordinates.

    Parameters:
    - cell_mask (np.ndarray): The input mask image where each cell has a unique ID.
    - id_value (int): The ID of the cell to isolate.
    - extend (int): Number of pixels to extend the cropping region beyond the cell's bounding box.

    Returns:
    - x1, y1, x2, y2 (int): Cropping coordinates.
    - cell_mask (np.ndarray): The processed mask with only the target cell highlighted.
    - contours (List[np.ndarray]): List of contours found in the processed mask.
    """

    # Isolate the specific cell by setting all other IDs to 0 (background)
    cell_mask = np.where(input_cell_mask == id_value, 255, 0).astype(np.uint8)
    
    # Find contours in the binary mask
    contours, _ = cv2.findContours(
        cell_mask,
        cv2.RETR_EXTERNAL,      # Retrieve only the external contours
        cv2.CHAIN_APPROX_SIMPLE # Compress horizontal, vertical, and diagonal segments
    )

    # Check if any contours were found
    if not contours:
        raise ValueError(f"No contours found for id_value {id_value}")

    # Get the bounding rectangle of the first contour (assuming one cell)
    x, y, w, h = cv2.boundingRect(contours[0])

    # Calculate extended cropping coordinates, ensuring they are within image bounds
    x1 = max(x - extend, 0)
    y1 = max(y - extend, 0)
    x2 = min(x + w + extend, cell_mask.shape[1])
    y2 = min(y + h + extend, cell_mask.shape[0])

    return x1, y1, x2, y2, cell_mask, contours

def create_report(
    image_dict: Dict[str, Tuple[Image.Image, Image.Image]],
    cell_dict: Dict[str, Tuple[int, int]],
    report_width: int = 1920,
    report_height: int = 1080,
    text_color: str = 'black',
    report_output_path: str = None,
    excel_output_path: str = None,
    padding_color: tuple = (225, 225, 225),
) -> None:
    
    total_her2, total_chr17, total_cell = 0,0,0
    
    import openpyxl
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(['HER2-DISH Analysis Report'])
    
    font = ImageFont.truetype('times.ttf', 16)
    
    report_0 = Image.open(r'.\GUI\report-0.png')
    report_1 = Image.open(r'.\GUI\report-1.png')
    report_2 = Image.open(r'.\GUI\report-2.png')
    
    draw_0 = ImageDraw.Draw(report_0)
    draw_1 = ImageDraw.Draw(report_1)
    draw_2 = ImageDraw.Draw(report_2)
    
    max_width, max_height = _find_max_dimensions(image_dict)
    combined_width = max_width * 2
    
    x_spacing = (report_width - combined_width * 5) // 6
    y_spacing = (report_height - 100 - max_height * 4) // 4
    
    second_lane = 0
    sheet_row = [None] * 20
    for idx, (key, (raw_img, composit_img)) in enumerate(image_dict.items()):
        her2, chr17 = cell_dict[key]
        total_her2 += her2
        total_chr17 += chr17
        total_cell += 1
        
        if idx >= 20: 
            second_lane = 1
            idx -= 20
            sheet_row[idx] += [key, her2, chr17]
        else: 
            sheet_row[idx] = [key, her2, chr17]
            
        draw_0.text((650 + 640 * second_lane, int(247 + 42 * idx)), text= str(key), fill= text_color, font=font)
        draw_0.text((870 + 640 * second_lane, int(247 + 42 * idx)), text= str(her2), fill= text_color, font=font)
        draw_0.text((1090 + 640 * second_lane, int(247 + 42 * idx)), text= str(chr17), fill= text_color, font=font)

        row, col = divmod(idx, 5)
        
        raw_img_padded = _pad_image(raw_img, max_width, max_height)
        composit_img_padded = _pad_image(composit_img, max_width, max_height)
        
        x_offset = x_spacing + col * (combined_width + x_spacing)
        y_offset = 120 + row * (max_height + y_spacing)
        
        cell_label = f'Cell ID: {key}'
        her2_label = f'HER2: {her2}'
        chr17_label = f'Chr17: {chr17}'
        
        if second_lane == 0:
            report_1.paste(raw_img_padded, (x_offset, y_offset))
            report_1.paste(composit_img_padded, (x_offset + max_width, y_offset))
            draw_1.text((x_offset + combined_width * 0.1, y_offset + max_height * 1.1), cell_label, fill=text_color, font=font)
            draw_1.text((x_offset + combined_width * 0.1, y_offset + max_height * 1.3), her2_label, fill=text_color, font=font)
            draw_1.text((x_offset + combined_width * 0.1, y_offset + max_height * 1.5), chr17_label, fill=text_color, font=font)
        else:
            report_2.paste(raw_img_padded, (x_offset, y_offset))
            report_2.paste(composit_img_padded, (x_offset + max_width, y_offset))
            draw_2.text((x_offset + combined_width * 0.1, y_offset + max_height * 1.1), cell_label, fill=text_color, font=font)
            draw_2.text((x_offset + combined_width * 0.1, y_offset + max_height * 1.3), her2_label, fill=text_color, font=font)
            draw_2.text((x_offset + combined_width * 0.1, y_offset + max_height * 1.5), chr17_label, fill=text_color, font=font)
    
    if second_lane == 0:
        sheet.append(["Cell ID", "HER2", "Chr17"])
    else:
        sheet.append(["Cell ID", "HER2", "Chr17", "Cell ID", "HER2", "Chr17"])
    
    for element in sheet_row: sheet.append(element)
    
    sheet.append(['Total:', total_her2, total_chr17])
    sheet.append(['HER2 / Chr17:', round(total_her2 / total_chr17, 3)])
    sheet.append(['Her2 / 20:', round(total_her2 / total_cell, 3)])
    sheet.append(['Total HER2:', total_her2])
    sheet.append(['Total Chr17:', total_chr17])
       
    font = ImageFont.truetype('times.ttf', 24)
    from datetime import datetime
    draw_0.text((250, 250), text= datetime.today().strftime('%Y-%m-%d %H-%M'), fill= text_color, font=font)
    if round(total_her2 / total_chr17, 3) >= 2.0: 
        sheet.append(['Result :', 'Amplified'])
        draw_0.text((250, 320), text= 'Amplified', fill= text_color, font=font)
        
    else:
        sheet.append(['Result :', 'Non-Amplified'])
        draw_0.text((250, 320), text= 'Non-Amplified', fill= text_color, font=font)
    
    draw_0.text((250, 390), text= str(round(total_her2 / total_chr17, 3)), fill= text_color, font=font)
    draw_0.text((250, 460), text= str(round(total_her2 / total_cell, 3)), fill= text_color, font=font)
    draw_0.text((250, 530), text= str(round(total_chr17 / total_cell, 3)), fill= text_color, font=font)
    draw_0.text((250, 600), text= str(total_her2), fill= text_color, font=font)
    draw_0.text((250, 670), text= str(total_chr17), fill= text_color, font=font)
    
    if second_lane == 0:
        report = Image.new('RGB', (report_width, report_height * 2), padding_color)
        report.paste(report_0, (0,0))
        report.paste(report_1, (0,1080))
    else:
        report = Image.new('RGB', (report_width, report_height * 3), padding_color)
        report.paste(report_0, (0,0))
        report.paste(report_1, (0,1080))
        report.paste(report_2, (0,2160))
    
    if report_output_path is not None:
        report.save(report_output_path)
    
    if excel_output_path is not None:
        workbook.save(excel_output_path)
    

def _find_max_dimensions(image_dict: Dict[str, Tuple[Image.Image, Image.Image]]) -> Tuple[int, int]:
    """
    Finds the maximum width and height among all images in the dictionary.

    Parameters:
    - image_dict (Dict[str, Tuple[Image.Image, Image.Image]]): Dictionary of image pairs.

    Returns:
    - Tuple[int, int]: Maximum width and height.
    """
    max_width = max(
        max(raw_img.width, composit_img.width)
        for raw_img, composit_img in image_dict.values()
    )
    max_height = max(
        max(raw_img.height, composit_img.height)
        for raw_img, composit_img in image_dict.values()
    )
    return max_width, max_height

def _pad_image(
    image: Image.Image,
    target_width: int,
    target_height: int,
    padding_color: Tuple[int, int, int] = (230, 230, 230)
) -> Image.Image:
    """
    Pads the given image to the target dimensions with the specified padding color.

    Parameters:
    - image (Image.Image): The image to pad.
    - target_width (int): The desired width after padding.
    - target_height (int): The desired height after padding.
    - padding_color (Tuple[int, int, int]): RGB color for padding.

    Returns:
    - Image.Image: The padded image.
    """
    padded_image = Image.new('RGB', (target_width, target_height), padding_color)
    paste_x = (target_width - image.width) // 2
    paste_y = (target_height - image.height) // 2
    padded_image.paste(image, (paste_x, paste_y))
    return padded_image