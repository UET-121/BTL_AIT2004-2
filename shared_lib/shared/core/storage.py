import boto3
import time
from botocore.exceptions import NoCredentialsError, ClientError, EndpointConnectionError

from ..config.config import config
from ..config.logger import log

MINIO_ENDPOINT = config.MINIO_ENDPOINT
ACCESS_KEY = config.MINIO_ACCESS_KEY
SECRET_KEY = config.MINIO_SECRET_KEY
BUCKET_NAME = config.MINIO_BUCKET_NAME

s3_client = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
)


def ensure_bucket_exists():
    """Kiểm tra, tự tạo bucket và chờ đợi nếu MinIO chưa khởi động xong"""
    retries = 5
    while retries > 0:
        try:
            try:
                s3_client.head_bucket(Bucket=BUCKET_NAME)
                print(f"[✓] MinIO Bucket '{BUCKET_NAME}' đã sẵn sàng.")
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code")
                if error_code == "404":
                    print(f"[*] Bucket '{BUCKET_NAME}' chưa tồn tại. Đang tạo mới...")
                    try:
                        s3_client.create_bucket(Bucket=BUCKET_NAME)
                        print(f"[✓] Đã tạo thành công bucket '{BUCKET_NAME}'.")
                    except Exception as create_error:
                        print(f"[X] Lỗi khi tạo bucket: {create_error}")
                        raise e
                else:
                    print(f"[X] Lỗi khi kiểm tra bucket từ MinIO: {e}")
                    raise e
            lifecycle_config = {
                "Rules": [
                    {
                        "ID": "Auto-Delete-Detection-3-Days",
                        "Filter": {"Prefix": "logs/detection/"},
                        "Status": "Enabled",
                        "Expiration": {"Days": 3},
                    },
                    {
                        "ID": "Auto-Delete-Recognition-30-Days",
                        "Filter": {"Prefix": "logs/recognition/"},
                        "Status": "Enabled",
                        "Expiration": {"Days": 30},
                    },
                ]
            }

            s3_client.put_bucket_lifecycle_configuration(
                Bucket=BUCKET_NAME, LifecycleConfiguration=lifecycle_config
            )
            log.info(
                f"[MinIO] Đã nạp thành công luật dọn rác tự động cho '{BUCKET_NAME}'."
            )
            return
        except EndpointConnectionError:
            print(f"[*] MinIO chưa sẵn sàng, chờ 5s... (Còn {retries} lần thử)")
            time.sleep(5)
            retries -= 1

        except Exception as e:
            print(f"[X] Lỗi mạng không xác định: {e}")
            time.sleep(5)
            retries -= 1

    print("[!] CẢNH BÁO: Không thể kết nối tới MinIO sau nhiều lần thử!")


ensure_bucket_exists()


def upload_file_to_minio(file_obj, object_name: str, extra_args):
    try:
        s3_client.upload_fileobj(
            file_obj, BUCKET_NAME, object_name, ExtraArgs=extra_args
        )
        final_url = f"{MINIO_ENDPOINT}/{BUCKET_NAME}/{object_name}"
        return final_url
    except FileNotFoundError:
        return None
    except NoCredentialsError:
        return None


def move_object_in_minio(src_object_name: str, dest_object_name: str) -> bool:
    try:
        s3_client.copy_object(
            Bucket=BUCKET_NAME,
            CopySource={"Bucket": BUCKET_NAME, "Key": src_object_name},
            Key=dest_object_name,
        )
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=src_object_name)
        log.info(f"[MinIO] Đã di chuyển: {src_object_name} -> {dest_object_name}")
        return True
    except ClientError as e:
        log.error(f"[MinIO] Lỗi khi di chuyển object: {e}")
        return False


def delete_images_from_minio(bucket_name: str, object_keys: list):

    if not object_keys:
        return

    objects_to_delete = [{"Key": key} for key in object_keys]

    try:
        response = s3_client.delete_objects(
            Bucket=bucket_name, Delete={"Objects": objects_to_delete}
        )
        log.info(f"[MinIO] Đã dọn dẹp {len(object_keys)} file rác mồ côi thành công.")
    except ClientError as e:
        log.error(f"[MinIO] Lỗi khi xóa file: {e}")
