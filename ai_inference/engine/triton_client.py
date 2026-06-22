import tritonclient.grpc as grpcclient
import numpy as np
import time
import os

class TritonClient:
    def __init__(self, url=None):
        if url is None:
            url = os.getenv("TRITON_URL", "triton-server:8001")
        print(f"[*] Đang kết nối tới Triton Server tại {url}...")
        try:
            self.client = grpcclient.InferenceServerClient(url=url)
            if not self.client.is_server_ready():
                raise Exception("Server chưa sẵn sàng!")
            print("[V] Đã kết nối thành công tới Triton Server!")
        except Exception as e:
            print(f"[X] Lỗi kết nối Triton: {e}")
            raise e

        self.metadata_cache = {}
        self.url = url

    def _wait_for_server(self, timeout_sec=60):
        start_time = time.time()
        print(f"[*] Đang kết nối tới Triton Server tại {self.url}...")

        while time.time() - start_time < timeout_sec:
            try:
                if self.client.is_server_ready():
                    print("[V] Triton Server đã kết nối!")
                    return
            except Exception:
                pass
            print("   -> Đang chờ Triton Server khởi động... (thử lại sau 2s)")
            time.sleep(2)

        raise Exception("[FATAL] Triton Server không phản hồi sau 60 giây!")

    def check_models_ready(self, model_names=["license_plate_detection", "license_plate_recognition"]):
        for model in model_names:
            try:
                if not self.client.is_model_ready(model):
                    raise Exception(
                        f"Model '{model}' chưa sẵn sàng hoặc bị lỗi cấu hình!"
                    )
                print(f"[V] Model '{model}' đã nạp thành công vào VRAM!")
            except Exception as e:
                print(f"[FATAL LỖI] Vấn đề với model '{model}': {e}")
                exit(1)

    def _get_model_metadata(self, model_name):

        if model_name in self.metadata_cache:
            return self.metadata_cache[model_name]

        print(f"[*] Đang trích xuất Metadata tự động cho model: {model_name}...")
        try:
            metadata = self.client.get_model_metadata(model_name)

            input_names = [inp.name for inp in metadata.inputs]
            output_names = [out.name for out in metadata.outputs]

            self.metadata_cache[model_name] = {
                "inputs": input_names,
                "outputs": output_names,
            }

            print(f"   -> Inputs: {input_names}")
            print(f"   -> Outputs: {output_names}")

            return self.metadata_cache[model_name]

        except Exception as e:
            print(f"[X] Lỗi khi lấy metadata cho {model_name}: {e}")
            raise e

    def detect_license_plates(self, preprocessed_image: np.ndarray, model_name="license_plate_detection"):

        meta = self._get_model_metadata(model_name)

        input_name = meta["inputs"][0]
        output_name = meta["outputs"][0]
        preprocessed_image = preprocessed_image.astype(np.float32)
        inputs = [grpcclient.InferInput(input_name, preprocessed_image.shape, "FP32")]
        inputs[0].set_data_from_numpy(preprocessed_image)

        outputs = [grpcclient.InferRequestedOutput(output_name)]

        result = self.client.infer(
            model_name=model_name, inputs=inputs, outputs=outputs
        )

        return result.as_numpy(output_name)

    def recognize_license_plate(
        self, preprocessed_license_plate: np.ndarray, model_name="license_plate_recognition"
    ):
        meta = self._get_model_metadata(model_name)

        input_name = meta["inputs"][0]
        output_name = meta["outputs"][0]
        preprocessed_license_plate = preprocessed_license_plate.astype(np.float32)
        inputs = [grpcclient.InferInput(input_name, preprocessed_license_plate.shape, "FP32")]
        inputs[0].set_data_from_numpy(preprocessed_license_plate)

        outputs = [grpcclient.InferRequestedOutput(output_name)]

        result = self.client.infer(
            model_name=model_name, inputs=inputs, outputs=outputs
        )

        return result.as_numpy(output_name)
