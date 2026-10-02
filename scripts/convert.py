import argparse
from pathlib import Path
from PIL import Image
import pillow_heif

PROJECT_DIR = Path(__file__).resolve().parents[1]

# 1. Enable HEIC support globally
pillow_heif.register_heif_opener()

def batch_process_images(input_folder, output_folder, target_format="JPEG"):
    """
    Finds all supported images (including HEIC) and converts them.
    """
    # Create the output folder if it doesn't exist
    input_folder = Path(input_folder)
    output_folder = Path(output_folder)
    if not input_folder.is_dir():
        raise FileNotFoundError(f"Input directory not found: {input_folder}")
    if not output_folder.exists():
        output_folder.mkdir(parents=True)
        print(f"Created output directory: {output_folder}")

    # Define common extensions to search for (case-insensitive)
    valid_extensions = ('.heic', '.heif', '.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff')

    # Count processed files
    count = 0

    print("Starting batch processing...")
    
    for filename in sorted(input_folder.iterdir()):
        # Check if the file is a supported image type
        if filename.is_file() and filename.suffix.lower() in valid_extensions:
            # Create a clean output filename with the new extension
            base_name = filename.stem
            output_ext = "jpg" if target_format.upper() == "JPEG" else target_format.lower()
            output_path = output_folder / f"{base_name}.{output_ext}"

            try:
                # Pillow opens HEIC or standard formats automatically now
                with Image.open(filename) as img:
                    # Convert transparent images (PNG) to RGB if saving as JPEG
                    if img.mode in ('RGBA', 'LA') and target_format.upper() == "JPEG":
                        img = img.convert('RGB')
                    
                    # Save to the new format
                    img.save(output_path, format=target_format)
                    print(f"Success: {filename.name} -> {output_path.name}")
                    count += 1
                    
            except Exception as e:
                print(f"Error processing {filename.name}: {e}")

    print(f"\nDone! Successfully processed {count} images.")

# --- How to Run It ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert source images to a model-compatible format")
    parser.add_argument("--input-dir", type=Path, default=PROJECT_DIR / "photos")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_DIR / "converted_photos")
    parser.add_argument("--format", default="JPEG", choices=("JPEG", "PNG", "WEBP"))
    args = parser.parse_args()
    batch_process_images(args.input_dir, args.output_dir, target_format=args.format)
