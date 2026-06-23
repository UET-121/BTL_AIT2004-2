# automatic-number-plate-recognition-python-yolov8

<p align="center">
<a href="https://www.youtube.com/watch?v=fyJB1t0o0ms">
    <img width="600" src="https://utils-computervisiondeveloper.s3.amazonaws.com/thumbnails/with_play_button/anpr_yolo2.jpg" alt="Watch the video">
    </br>Watch on YouTube: Automatic number plate recognition with Python, Yolov8 and EasyOCR !
</a>
</p>

## data

The video I used in this tutorial can be downloaded [here](https://www.pexels.com/video/traffic-flow-in-the-highway-2103099/).

## models

A Yolov8 pretrained model was used to detect vehicles.

A licensed plate detector was used to detect license plates. The model was trained with Yolov8 using [this dataset](https://universe.roboflow.com/roboflow-universe-projects/license-plate-recognition-rxg4e/dataset/4) and following this [step by step tutorial on how to train an object detector with Yolov8 on your custom data](https://github.com/computervisioneng/train-yolov8-custom-dataset-step-by-step-guide). 

The trained model is available in my [Patreon](https://www.patreon.com/ComputerVisionEngineer).

## dependencies

The sort module needs to be downloaded from [this repository](https://github.com/abewley/sort) as mentioned in the [video](https://youtu.be/fyJB1t0o0ms?t=1120).

## run setup

1. Copy `yolov8n.pt` into this folder.
2. Put a custom license plate detector model at `models/license_plate_detector.pt`.
3. Place a sample video named `sample.mp4` in this folder.
4. Install the Python dependencies from `requirements.txt`.
5. Run with `python main.py`.

If you do not have `license_plate_detector.pt`, use a compatible YOLOv8 object detection model or train one for license plate detection.

## training your own license plate detector

1. Prepare your dataset in YOLO format with:
   - `images/train/` and `images/val/`
   - `labels/train/` and `labels/val/`
   - a YAML file `data.yaml` with `train`, `val`, `nc`, and `names`
2. Install dependencies:
   - `pip install -r requirements.txt`
   - `pip install ultralytics`
3. Run the training script:
   - `python train_license_plate.py --data data.yaml --model yolov8n.pt --epochs 50 --batch 16 --imgsz 640`
4. After training, copy the best weights to `models/license_plate_detector.pt`:
   - `cp runs/train/license_plate/weights/best.pt models/license_plate_detector.pt`

If you use Windows, replace `cp` with `copy` or use the File Explorer.
