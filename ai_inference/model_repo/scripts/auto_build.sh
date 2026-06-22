#!/bin/bash
cd /app
echo "--- BẮT ĐẦU QUÁ TRÌNH AUTO BUILD ---"

if [ ! -f "./src_models/license_plate_detection/yolov8.onnx" ]; then
    echo "[FATAL LỖI] Thiếu file yolov8.onnx trong src_models/license_plate_detection/"
    echo "Hệ thống dừng quá trình build!"
    exit 1
fi

if [ ! -f "./src_models/license_plate_recognition/arcface.onnx" ]; then
    echo "[FATAL LỖI] Thiếu file arcface.onnx trong src_models/license_plate_recognition/"
    exit 1
fi

build_model() {
    local MODEL_PATH=$1
    local MODEL_NAME=$2
    local OUTPUT_DIR=$3

    if [ -f "$MODEL_PATH" ]; then
        echo ">> Đang xử lý $MODEL_NAME..."
        mkdir -p "$OUTPUT_DIR/1"

        SHAPE_STR=$(python scripts/generate_config.py \
            --onnx_path "$MODEL_PATH" \
            --model_name "$MODEL_NAME" \
            --output_dir "$OUTPUT_DIR" \
            --max_batch 8 \
            --pref_batches 4 8 | grep "SHAPES=")

        if [ -z "$SHAPE_STR" ]; then
            echo "[LỖI] Không thể phân tích shape từ ONNX cho $MODEL_NAME!"
            return 1
        fi

        SHAPE_STR=${SHAPE_STR#"SHAPES="}

        IFS=';' read -r -a SHAPE_ARRAY <<< "$SHAPE_STR"
        MIN_SHAPES="${SHAPE_ARRAY[0]}"
        OPT_SHAPES="${SHAPE_ARRAY[1]}"
        MAX_SHAPES="${SHAPE_ARRAY[2]}"

        echo "   Đã tìm thấy Input Shapes: Min($MIN_SHAPES), Opt($OPT_SHAPES), Max($MAX_SHAPES)"

        trtexec --onnx="$MODEL_PATH" \
                --saveEngine="$OUTPUT_DIR/1/model.plan" \
                --fp16 \
                --minShapes="$MIN_SHAPES" \
                --optShapes="$OPT_SHAPES" \
                --maxShapes="$MAX_SHAPES"

        echo "[V] Hoàn tất $MODEL_NAME!"
    else
        echo "   [Bỏ qua] Không tìm thấy $MODEL_PATH"
    fi
}

build_model "./src_models/license_plate_detection/yolov8.onnx" "license_plate_detection" "./license_plate_detection"
build_model "./src_models/license_plate_recognition/arcface.onnx" "license_plate_recognition" "./license_plate_recognition"
