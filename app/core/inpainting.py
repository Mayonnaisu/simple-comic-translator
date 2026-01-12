import os

from app.core.image_utils_pil import create_inpainting_mask

def inpaint_image_with_lama(inpainter: object, image: object, bbox: list[int], output_dir: str, number: int, log_level: str):
    '''
    Inpaint image with simple-lama-inpainting package & lama-big model
    '''

    simple_lama = inpainter

    # Create image mask. The mask must be a 1-channel binary image (pixels with 255 will be inpainted)
    mask_image = create_inpainting_mask(image, bbox)

    # Perform the inpainting
    result = simple_lama(image, mask_image)

    # # Save the result in debug mode
    # if log_level == "TRACE":
    #     save_path = f"{output_dir}/debug/inpaint"
    #     os.makedirs(save_path, exist_ok=True)
    #     result.save(f"{save_path}/inpainted_{number:02d}.jpg", quality=100)

    return result