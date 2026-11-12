import numpy as np
from PIL import Image

from src.ocr.preprocess import preprocess_image


def test_preprocess_returns_grayscale_and_upscaled_image():
    image = Image.new("RGB", (200, 100), (255, 255, 255))

    result = preprocess_image(image, upscale=2.0)

    assert result.mode == "L"
    assert result.size == (400, 200)


def test_preprocess_reduces_grain():
    grain = np.random.default_rng(0).normal(128, 30, (100, 100)).clip(0, 255).astype(np.uint8)
    image = Image.fromarray(grain).convert("RGB")

    result = preprocess_image(image, upscale=1.0)

    assert np.asarray(result).std() < np.asarray(image.convert("L")).std()