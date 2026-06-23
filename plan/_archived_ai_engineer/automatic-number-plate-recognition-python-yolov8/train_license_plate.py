import argparse
from pathlib import Path

from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(
        description="Train a YOLOv8 license plate detector."
    )
    parser.add_argument(
        "--data",
        type=Path,
        required=True,
        help="Path to the dataset YAML file in YOLO format.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="yolov8n.pt",
        help="Base YOLOv8 model weights file to start from.",
    )
    parser.add_argument(
        "--epochs", type=int, default=50, help="Number of training epochs."
    )
    parser.add_argument("--batch", type=int, default=16, help="Batch size.")
    parser.add_argument(
        "--imgsz", type=int, default=640, help="Image size for training."
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.data.exists():
        raise FileNotFoundError(f"Dataset YAML file not found: {args.data}")

    yolov8 = YOLO(args.model)
    yolov8.train(
        data=str(args.data),
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        project="runs/train",
        name="license_plate",
        exist_ok=True,
    )


if __name__ == "__main__":
    main()
