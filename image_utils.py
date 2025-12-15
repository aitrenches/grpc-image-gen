import os
import base64
import hashlib
import time
from pathlib import Path


def save_base64_image(base64_data: str, images_dir: str = "images") -> str:
    """
    Decode base64 image data, detect format, and save to images directory.
    
    Args:
        base64_data: Base64 encoded image data (with or without data URI prefix)
        images_dir: Directory to save images (default: "images")
    
    Returns:
        str: The filename of the saved image (e.g., "1704115200_a3f5b2.png")
    
    Raises:
        ValueError: If base64 data is invalid or image format cannot be detected
    """
    # Create images directory if it doesn't exist
    Path(images_dir).mkdir(parents=True, exist_ok=True)
    
    # Remove data URI prefix if present (e.g., "data:image/png;base64,...")
    if base64_data.startswith("data:"):
        base64_data = base64_data.split(",", 1)[1]
    
    try:
        # Decode base64 data
        image_bytes = base64.b64decode(base64_data)
    except Exception as e:
        raise ValueError(f"Invalid base64 data: {str(e)}")
    
    # Detect image format from magic bytes
    image_format = detect_image_format(image_bytes)
    if not image_format:
        raise ValueError("Unable to detect image format from data")
    
    # Generate filename: timestamp + short hash
    timestamp = int(time.time())
    hash_object = hashlib.md5(image_bytes[:100])  # Hash first 100 bytes for speed
    short_hash = hash_object.hexdigest()[:6]  # First 6 characters
    filename = f"{timestamp}_{short_hash}.{image_format}"
    filepath = os.path.join(images_dir, filename)
    
    # Save the image
    try:
        with open(filepath, "wb") as f:
            f.write(image_bytes)
    except Exception as e:
        raise IOError(f"Failed to save image to {filepath}: {str(e)}")
    
    return filename


def detect_image_format(image_bytes: bytes) -> str:
    """
    Detect image format from magic bytes.
    
    Args:
        image_bytes: Raw image bytes
    
    Returns:
        str: Image format extension (e.g., "png", "jpg", "webp") or None
    """
    if len(image_bytes) < 4:
        return None
    
    # PNG: 89 50 4E 47
    if image_bytes[:4] == b'\x89PNG':
        return "png"
    
    # JPEG: FF D8 FF
    if image_bytes[:3] == b'\xFF\xD8\xFF':
        return "jpg"
    
    # GIF: 47 49 46 38 (GIF8)
    if image_bytes[:4] == b'GIF8':
        return "gif"
    
    # WebP: RIFF...WEBP
    if image_bytes[:4] == b'RIFF' and len(image_bytes) > 12:
        if image_bytes[8:12] == b'WEBP':
            return "webp"
    
    # BMP: 42 4D
    if image_bytes[:2] == b'BM':
        return "bmp"
    
    return None

