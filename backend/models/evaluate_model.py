"""
TrustLens AI — Model Benchmark & Accuracy Evaluator
Evaluates the trained TorchScript model (deepfake_detector.pt) on a test folder.

Usage:
  python evaluate_model.py --data_dir ./data/val --model_path ./deepfake_detector.pt
"""
import argparse
import os
import sys
import time
import torch
import numpy as np
from PIL import Image
from torchvision import transforms


def evaluate(data_dir: str, model_path: str = None):
    if model_path is None:
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deepfake_detector.pt")

    if not os.path.exists(model_path):
        print(f"Error: Model file '{model_path}' not found. Please run setup_model.py or train.py first.")
        sys.exit(1)

    if not os.path.exists(data_dir):
        print(f"Error: Dataset directory '{data_dir}' not found.")
        sys.exit(1)

    print(f"[TrustLens] Loading model from: {model_path}")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = torch.jit.load(model_path, map_location=device)
    model.eval()

    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
    ])

    classes = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
    print(f"[TrustLens] Detected classes in test directory: {classes}")

    tp = fp = fn = tn = 0
    latencies = []

    for cls_name in classes:
        cls_dir = os.path.join(data_dir, cls_name)
        is_fake_ground_truth = "fake" in cls_name.lower() or "ai" in cls_name.lower()

        files = [f for f in os.listdir(cls_dir) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
        for f in files:
            img_path = os.path.join(cls_dir, f)
            try:
                img = Image.open(img_path).convert("RGB")
                tensor = transform(img).unsqueeze(0).to(device)

                t0 = time.perf_counter()
                with torch.no_grad():
                    logits = model(tensor)
                    prob = float(torch.sigmoid(logits).item())
                latencies.append((time.perf_counter() - t0) * 1000.0)

                pred_is_fake = prob >= 0.50

                if is_fake_ground_truth and pred_is_fake:
                    tp += 1
                elif not is_fake_ground_truth and pred_is_fake:
                    fp += 1
                elif is_fake_ground_truth and not pred_is_fake:
                    fn += 1
                else:
                    tn += 1
            except Exception as e:
                print(f"Skipping {f}: {e}")

    total = tp + fp + fn + tn
    if total == 0:
        print("No valid images evaluated.")
        return

    accuracy = ((tp + tn) / total) * 100.0
    precision = (tp / (tp + fp)) * 100.0 if (tp + fp) > 0 else 0.0
    recall = (tp / (tp + fn)) * 100.0 if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = (fp / (fp + tn)) * 100.0 if (fp + tn) > 0 else 0.0
    fnr = (fn / (fn + tp)) * 100.0 if (fn + tp) > 0 else 0.0
    avg_latency = float(np.mean(latencies)) if latencies else 0.0

    print("\n" + "=" * 55)
    print("        TRUSTLENS AI MODEL BENCHMARK REPORT       ")
    print("=" * 55)
    print(f" Total Evaluated Images  : {total}")
    print(f" Overall Accuracy        : {accuracy:.2f}%")
    print(f" Precision (Fake)        : {precision:.2f}%")
    print(f" Recall / Sensitivity    : {recall:.2f}%")
    print(f" F1 Score                : {f1:.2f}%")
    print(f" False Positive Rate(FPR): {fpr:.2f}% (Real misclassified as Fake)")
    print(f" False Negative Rate(FNR): {fnr:.2f}% (Fake misclassified as Real)")
    print(f" Avg Inference Latency   : {avg_latency:.2f} ms per image")
    print("-" * 55)
    print(f" Confusion Matrix:")
    print(f"   True Real (TN) : {tn:<6} | False Fake (FP): {fp:<6}")
    print(f"   False Real (FN): {fn:<6} | True Fake  (TP): {tp:<6}")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate TrustLens AI Deepfake Detector")
    parser.add_argument("--data_dir", type=str, default="./data/val", help="Path to evaluation dataset")
    parser.add_argument("--model_path", type=str, default=None, help="Path to TorchScript model")
    args = parser.parse_args()

    evaluate(args.data_dir, args.model_path)
