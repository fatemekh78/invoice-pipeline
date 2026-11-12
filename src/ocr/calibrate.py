from pathlib import Path

from src.ocr import noise
from src.ocr.evaluate import evaluate_language

# Base = the "heavy" setting that scored 100%. Each candidate pushes ONE value hard.
CANDIDATES = {
    "grain_20": {"max_angle": 3.0, "blur": 0.9, "grain": 20, "scale": 0.65},
    "grain_25": {"max_angle": 3.0, "blur": 0.9, "grain": 25, "scale": 0.65},
    "combo_a": {"max_angle": 5.0, "blur": 1.2, "grain": 15, "scale": 0.6},
    "combo_b": {"max_angle": 5.0, "blur": 1.2, "grain": 20, "scale": 0.6},
}


def main() -> None:
    folder = Path("data/synthetic")
    for name, settings in CANDIDATES.items():
        noise.NOISE_LEVELS[name] = settings  # temporary, only while this script runs
        result = evaluate_language(folder, "fi", 10, name)
        rates = result["field_hit_rate"]
        print(
            f"{name:<11} CER={result['cer']:.4f}  supplier={rates['supplier']:.0%}  "
            f"vat={rates['vat_amount']:.0%}  total={rates['total']:.0%}"
        )


if __name__ == "__main__":
    main()