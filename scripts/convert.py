import os
from PIL import Image
import pillow_heif

# 1. Enable HEIC support globally
pillow_heif.register_heif_opener()

def batch_process_images(input_folder, output_folder, target_format="JPEG"):
    """
    Finds all supported images (including HEIC) and converts them.
    """
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output directory: {output_folder}")

    # Define common extensions to search for (case-insensitive)
    valid_extensions = ('.heic', '.heif', '.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff')

    # Count processed files
    count = 0

    print("Starting batch processing...")
    
    for filename in os.listdir(input_folder):
        # Check if the file is a supported image type
        if filename.lower().endswith(valid_extensions):
            input_path = os.path.join(input_folder, filename)
            
            # Create a clean output filename with the new extension
            base_name = os.path.splitext(filename)[0]
            output_ext = "jpg" if target_format.upper() == "JPEG" else target_format.lower()
            output_path = os.path.join(output_folder, f"{base_name}.{output_ext}")

            try:
                # Pillow opens HEIC or standard formats automatically now
                with Image.open(input_path) as img:
                    # Convert transparent images (PNG) to RGB if saving as JPEG
                    if img.mode in ('RGBA', 'LA') and target_format.upper() == "JPEG":
                        img = img.convert('RGB')
                    
                    # Save to the new format
                    img.save(output_path, format=target_format)
                    print(f"Success: {filename} -> {target_format}")
                    count += 1
                    
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    print(f"\nDone! Successfully processed {count} images.")

# --- How to Run It ---
if __name__ == "__main__":
    # Replace these paths with your actual folders
    SOURCE_DIR = "./../photos"
    DEST_DIR = "./../converted_photos"
    
    # Run the script (Converts everything to JPEG)
    batch_process_images(SOURCE_DIR, DEST_DIR, target_format="JPEG")
