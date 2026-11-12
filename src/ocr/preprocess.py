from PIL import Image, ImageFilter, ImageOps


def preprocess_image(image: Image.Image, upscale: float = 1.5, median_size: int = 3) -> Image.Image:
    gray = ImageOps.grayscale(image)
    gray = gray.filter(ImageFilter.MedianFilter(size=median_size))

    width, height = gray.size
    return gray.resize((int(width * upscale), int(height * upscale)), Image.LANCZOS)