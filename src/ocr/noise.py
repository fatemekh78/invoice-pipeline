import random

import numpy as np
from PIL import Image, ImageFilter

# How badly to damage the image. "clean" changes nothing.
NOISE_LEVELS = {
    "clean": None,
    "mild": {"max_angle": 1.5, "blur": 0.6, "grain": 8, "scale": 0.8},
    "heavy": {"max_angle": 5.0, "blur": 1.2, "grain": 15, "scale": 0.6},
    "severe": {"max_angle": 5.0, "blur": 1.2, "grain": 20, "scale": 0.6},
}


def degrade_image(image: Image.Image, level: str, rng: random.Random) -> Image.Image:
    if level not in NOISE_LEVELS:
        raise ValueError(f"Unknown noise level: {level}")

    settings = NOISE_LEVELS[level]
    if settings is None:
        return image

    # 1. Tilt the page a little, like a crooked scan
    angle = rng.uniform(-settings["max_angle"], settings["max_angle"])
    image = image.rotate(angle, expand=True, fillcolor=(255, 255, 255),
                         resample=Image.BICUBIC)

    # 2. Lose resolution: shrink, then enlarge back
    width, height = image.size
    small = image.resize((int(width * settings["scale"]), int(height * settings["scale"])),
                         Image.BILINEAR)
    image = small.resize((width, height), Image.BILINEAR)

    # 3. Blur, like an out-of-focus camera
    image = image.filter(ImageFilter.GaussianBlur(settings["blur"]))

    # 4. Add random grain to every pixel
    pixels = np.asarray(image).astype(np.int16)
    generator = np.random.default_rng(rng.randint(0, 2**32 - 1))
    pixels = pixels + generator.normal(0, settings["grain"], pixels.shape)
    return Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8))