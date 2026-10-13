"""
TrustLens AI — Model Training & Fine-Tuning Pipeline
Trains the Dual-Stream GenAI/Deepfake Detector on Real vs AI-Generated image datasets.
Outputs a TorchScript checkpoint directly to backend/models/deepfake_detector.pt.

Usage:
  python train.py --data_dir ./data --epochs 10 --batch_size 32 --lr 1e-4

Dataset Folder Structure:
  data/
    train/
      REAL/   (authentic photos)
      FAKE/   (Midjourney, Stable Diffusion, DALL-E, deepfakes)
    val/
      REAL/
      FAKE/
"""
import argparse
import io
import os
import random
import sys
import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

# Import the model architecture from setup_model.py
try:
    from setup_model import GenerativeArtifactDiscriminator
except ImportError:
    from .setup_model import GenerativeArtifactDiscriminator

# Import starter dataset generator if needed
try:
    from download_sample_dataset import generate_starter_dataset
except ImportError:
    from .download_sample_dataset import generate_starter_dataset


class RandomJPEGCompression:
    """
    Simulates real-world social media lossy recompression (e.g. WhatsApp, Instagram, Telegram).
    Crucial for training deepfake models to ignore harmless compression artifacts.
    """
    def __init__(self, quality_min=45, quality_max=90, p=0.5):
        self.quality_min = quality_min
        self.quality_max = quality_max
        self.p = p

    def __call__(self, img: Image.Image) -> Image.Image:
        if random.random() < self.p:
            quality = random.randint(self.quality_min, self.quality_max)
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality)
            buffer.seek(0)
            return Image.open(buffer).convert("RGB")
        return img


def get_data_transforms():
    """
    Augmentations tailored for Deepfake & GenAI detection.
    Combines JPEG compression, Gaussian blur, and color jitter to build invariant representations.
    """
    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=10),
        transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15),
        RandomJPEGCompression(quality_min=45, quality_max=88, p=0.5),
        transforms.GaussianBlur(kernel_size=(3, 3), sigma=(0.1, 1.5)),
        transforms.ToTensor(),
    ])

    val_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
    ])

    return train_transform, val_transform


def train(data_dir: str, epochs: int = 10, batch_size: int = 32, lr: float = 1e-4, save_path: str = None):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[TrustLens] Training on device: {device}")

    if save_path is None:
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deepfake_detector.pt")

    train_dir = os.path.join(data_dir, "train")
    val_dir = os.path.join(data_dir, "val")

    # If dataset doesn't exist, auto-generate starter dataset
    if not os.path.exists(train_dir):
        print(f"[TrustLens] Training directory '{train_dir}' not found. Generating starter dataset...")
        generate_starter_dataset(data_dir, samples_per_class=40)

    train_tf, val_tf = get_data_transforms()
    train_dataset = datasets.ImageFolder(train_dir, transform=train_tf)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0, pin_memory=torch.cuda.is_available())

    val_loader = None
    if os.path.exists(val_dir):
        val_dataset = datasets.ImageFolder(val_dir, transform=val_tf)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
        print(f"[TrustLens] Loaded {len(train_dataset)} training and {len(val_dataset)} validation samples.")
    else:
        print(f"[TrustLens] Loaded {len(train_dataset)} training samples.")

    # Initialize model
    model = GenerativeArtifactDiscriminator().to(device)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    fake_idx = train_dataset.class_to_idx.get("FAKE", 0)
    print(f"[TrustLens] Class mapping: FAKE -> 1.0 (idx={fake_idx}), REAL -> 0.0")

    best_val_f1 = -1.0

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        correct = 0
        total = 0

        for images, labels in train_loader:
            images = images.to(device)
            # FAKE = 1.0, REAL = 0.0
            targets = (labels == fake_idx).float().unsqueeze(1).to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * images.size(0)
            preds = (torch.sigmoid(outputs) >= 0.5).float()
            correct += (preds == targets).sum().item()
            total += targets.size(0)

        train_acc = (correct / total) * 100.0 if total > 0 else 0.0
        train_loss = total_loss / max(total, 1)
        scheduler.step()

        # Validation step
        val_summary = "N/A"
        if val_loader:
            model.eval()
            tp = fp = fn = tn = 0
            with torch.no_grad():
                for v_images, v_labels in val_loader:
                    v_images = v_images.to(device)
                    v_targets = (v_labels == fake_idx).float().unsqueeze(1).to(device)
                    v_outputs = model(v_images)
                    v_preds = (torch.sigmoid(v_outputs) >= 0.5).float()

                    tp += ((v_preds == 1) & (v_targets == 1)).sum().item()
                    fp += ((v_preds == 1) & (v_targets == 0)).sum().item()
                    fn += ((v_preds == 0) & (v_targets == 1)).sum().item()
                    tn += ((v_preds == 0) & (v_targets == 0)).sum().item()

            v_total = tp + fp + fn + tn
            val_acc = ((tp + tn) / v_total) * 100.0 if v_total > 0 else 0.0
            precision = (tp / (tp + fp)) * 100.0 if (tp + fp) > 0 else 0.0
            recall = (tp / (tp + fn)) * 100.0 if (tp + fn) > 0 else 0.0
            f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            val_summary = f"Acc: {val_acc:.1f}% | Prec: {precision:.1f}% | Rec: {recall:.1f}% | F1: {f1:.1f}%"

            if f1 > best_val_f1 or epoch == epochs:
                best_val_f1 = f1
                # Export best checkpoint as TorchScript
                model.eval()
                example_input = torch.randn(1, 3, 256, 256).to(device)
                traced = torch.jit.trace(model, example_input)
                traced.save(save_path)
                print(f" -> Best Checkpoint saved to: {save_path}")

        print(f"Epoch [{epoch:02d}/{epochs:02d}] - Loss: {train_loss:.4f} | Train Acc: {train_acc:.1f}% | Val: [{val_summary}]")

    # If no validation set was provided, save the final trained model
    if not val_loader:
        model.eval()
        example_input = torch.randn(1, 3, 256, 256).to(device)
        traced = torch.jit.trace(model, example_input)
        traced.save(save_path)
        print(f"[TrustLens] Saved final model checkpoint to: {save_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train TrustLens AI Deepfake Detector")
    parser.add_argument("--data_dir", type=str, default="./data", help="Path to dataset root folder")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size for training")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--save_path", type=str, default=None, help="Where to save the .pt model")
    args = parser.parse_args()

    train(args.data_dir, args.epochs, args.batch_size, args.lr, args.save_path)
