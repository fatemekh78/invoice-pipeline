import random

import numpy as np
import pytest
from PIL import Image

from src.ocr.noise import NOISE_LEVELS, degrade_image


def make_test_image():
    return Image.new("RGB", (200, 100), (255, 255, 255))


def test_clean_level_changes_nothing():
    image = make_test_image()

    result = degrade_image(image, "clean", random.Random(1))

    assert np.array_equal(np.asarray(result), np.asarray(image))


@pytest.mark.parametrize("level", ["mild", "heavy", "severe"])
def test_noisy_levels_change_the_image(level):
    image = make_test_image()

    result = degrade_image(image, level, random.Random(1))

    assert result.mode == "RGB"
    assert not np.array_equal(np.asarray(result), np.asarray(image))


@pytest.mark.parametrize("level", ["mild", "heavy", "severe"])
def test_same_seed_gives_same_noise(level):
    first = degrade_image(make_test_image(), level, random.Random(7))
    second = degrade_image(make_test_image(), level, random.Random(7))

    assert np.array_equal(np.asarray(first), np.asarray(second))


def test_unknown_level_is_rejected():
    with pytest.raises(ValueError):
        degrade_image(make_test_image(), "extreme", random.Random(1))