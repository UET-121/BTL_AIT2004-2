import asyncio
import logging
import multiprocessing
import signal

from streaming.ai_consumer import start_ai_consumer, ACTIVE_WORKERS
from streaming.rpc_worker import rpc_worker_main

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | [*] %(message)s"
)
logger = logging.getLogger("AI_WORKER_MAIN")


async def graceful_shutdown(signal_name, loop):

    logger.warning(
        f"Nhận được tín hiệu {signal_name}! Đang bắt đầu dọn dẹp hệ thống..."
    )

    if ACTIVE_WORKERS:
        logger.info(f"Đang dừng {len(ACTIVE_WORKERS)} luồng camera đang hoạt động...")
        for camera_id, process in list(ACTIVE_WORKERS.items()):
            try:
                process.terminate()
                process.join(timeout=2)
                logger.info(f" - Đã tắt luồng camera {camera_id} (PID: {process.pid})")
            except Exception as e:
                logger.error(f"Lỗi khi tắt luồng camera {camera_id}: {e}")
    else:
        logger.info("Không có luồng camera nào đang chạy.")

    logger.info("Đang ngắt kết nối RabbitMQ...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)

    loop.stop()
    logger.info("=== HỆ THỐNG ĐÃ TẮT AN TOÀN ===")


def main():
    multiprocessing.set_start_method("spawn", force=True)

    logger.info("=== KHỞI ĐỘNG HỆ THỐNG AI WORKER (DAEMON) ===")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(graceful_shutdown(s.name, loop))
        )

    try:
        loop.run_until_complete(asyncio.gather(start_ai_consumer(), rpc_worker_main()))
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Lỗi sập AI Worker: {e}", exc_info=True)
    finally:
        loop.close()


if __name__ == "__main__":
    main()
