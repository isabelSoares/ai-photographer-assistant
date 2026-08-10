from PIL import Image
import pillow_heif

def get_image_info(image_path: str):
    pillow_heif.register_heif_opener()

    image = Image.open(image_path)

    return {
        "width": image.width,
        "height": image.height,
        "format": image.format,
    }