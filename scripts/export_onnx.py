import argparse
import shutil
from pathlib import Path
from ultralytics import YOLO

def main():
    parser = argparse.ArgumentParser(description="Export YOLOv8 .pt model to ONNX format.")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the input PyTorch .pt model file"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to save the output ONNX model file"
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Image size for the model input (default: 640)"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: Input model not found at {input_path}")
        return

    print(f"Loading PyTorch model from {input_path}...")
    model = YOLO(str(input_path))

    print(f"Exporting model to ONNX with imgsz={args.imgsz} and simplify=True...")
    # model.export returns the path of the exported file
    exported_path_str = model.export(format="onnx", imgsz=args.imgsz, simplify=True)
    exported_path = Path(exported_path_str)

    if not exported_path.exists():
        print(f"Error: Export failed, output file not found at {exported_path}")
        return

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Moving exported model from {exported_path} to {output_path}...")
    shutil.move(str(exported_path), str(output_path))
    print(f"Successfully exported and saved ONNX model to {output_path}!")

if __name__ == "__main__":
    main()
