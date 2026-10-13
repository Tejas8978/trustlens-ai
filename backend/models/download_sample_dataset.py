"""
TrustLens AI — Dataset Generator for Deepfake & GenAI Training
Generates diverse Real and AI-synthetic training samples.
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def generate_starter_dataset(target_dir: str = "./data", train_samples: int = 120, val_samples: int = 30):
    os.makedirs(os.path.join(target_dir, "train", "REAL"), exist_ok=True)
    os.makedirs(os.path.join(target_dir, "train", "FAKE"), exist_ok=True)
    os.makedirs(os.path.join(target_dir, "val", "REAL"), exist_ok=True)
    os.makedirs(os.path.join(target_dir, "val", "FAKE"), exist_ok=True)

    print(f"[TrustLens] Generating dataset in '{target_dir}'...")
    print(f"  - Training samples:   {train_samples} REAL, {train_samples} FAKE")
    print(f"  - Validation samples: {val_samples} REAL, {val_samples} FAKE")

    for split, count in [("train", train_samples), ("val", val_samples)]:
        for i in range(count):
            seed = i + (1000 if split == "val" else 0)
            rng = np.random.RandomState(seed)

            # -------------------------------------------------------------
            # 1. REAL SAMPLES (Organic optical features)
            # -------------------------------------------------------------
            # Natural scenery / portrait palette
            base_r = int(rng.randint(60, 220))
            base_g = int(rng.randint(60, 200))
            base_b = int(rng.randint(50, 180))
            img_real = Image.new("RGB", (256, 256), color=(base_r, base_g, base_b))
            draw = ImageDraw.Draw(img_real)

            # Natural organic shapes & layered light gradients
            for _ in range(rng.randint(4, 9)):
                x0 = int(rng.randint(10, 220))
                y0 = int(rng.randint(10, 220))
                x1 = x0 + int(rng.randint(20, 80))
                y1 = y0 + int(rng.randint(20, 80))
                color = (int(rng.randint(40, 255)), int(rng.randint(40, 255)), int(rng.randint(40, 255)))
                draw.ellipse([x0, y0, x1, y1], fill=color)

            # Natural optical blur gradient
            img_real = img_real.filter(ImageFilter.GaussianBlur(radius=rng.uniform(0.5, 1.8)))

            # Physical camera sensor noise (PRNU + read noise)
            arr_r = np.array(img_real, dtype=np.float32)
            noise_std = rng.uniform(3.0, 7.5)
            sensor_noise = rng.normal(0, noise_std, arr_r.shape).astype(np.float32)
            arr_r = np.clip(arr_r + sensor_noise, 0, 255).astype(np.uint8)
            img_real = Image.fromarray(arr_r)

            real_path = os.path.join(target_dir, split, "REAL", f"real_{i:04d}.jpg")
            img_real.save(real_path, "JPEG", quality=int(rng.randint(80, 95)))

            # -------------------------------------------------------------
            # 2. FAKE SAMPLES (Generative AI synthetic artifacts)
            # -------------------------------------------------------------
            arr_f = np.zeros((256, 256, 3), dtype=np.float32)
            # Synthetic plastic skin / digital render base
            synth_r = float(rng.randint(160, 230))
            synth_g = float(rng.randint(130, 200))
            synth_b = float(rng.randint(110, 180))
            arr_f[:, :, 0] = synth_r
            arr_f[:, :, 1] = synth_g
            arr_f[:, :, 2] = synth_b

            # Add geometric CGI shapes with artificial sharp edges
            img_fake = Image.fromarray(arr_f.astype(np.uint8))
            draw_f = ImageDraw.Draw(img_fake)
            for _ in range(rng.randint(2, 5)):
                x0 = int(rng.randint(30, 200))
                y0 = int(rng.randint(30, 200))
                x1 = x0 + int(rng.randint(30, 90))
                y1 = y0 + int(rng.randint(30, 90))
                draw_f.rectangle([x0, y0, x1, y1], fill=(int(rng.randint(100, 250)), int(rng.randint(100, 250)), int(rng.randint(100, 250))))

            # Synthetic smoothing (plastic face filter)
            img_fake = img_fake.filter(ImageFilter.SMOOTH_MORE)
            arr_f = np.array(img_fake, dtype=np.float32)

            # Inject transposed convolution checkerboard frequency footprint (AI generator signature)
            period = float(rng.choice([3.0, 4.0, 6.0]))
            y, x = np.ogrid[:256, :256]
            strength = float(rng.uniform(8.0, 16.0))
            checker = np.sin(x * np.pi / period) * np.sin(y * np.pi / period) * strength
            for c in range(3):
                arr_f[:, :, c] = np.clip(arr_f[:, :, c] + checker, 0, 255)

            img_fake = Image.fromarray(arr_f.astype(np.uint8))
            fake_path = os.path.join(target_dir, split, "FAKE", f"fake_{i:04d}.jpg")
            img_fake.save(fake_path, "JPEG", quality=int(rng.randint(80, 95)))

    print("[TrustLens] Dataset generation complete.")


if __name__ == "__main__":
    generate_starter_dataset("./data", train_samples=120, val_samples=30)
