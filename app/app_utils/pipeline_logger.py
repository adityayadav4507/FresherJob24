import logging
from threading import Lock

logger = logging.getLogger("job_finder.pipeline_logger")

class PipelineLogger:
    def __init__(self):
        self._logs = {
            "greenhouse": [],
            "lever": [],
            "linkedin": []
        }
        self._lock = Lock()

    def clear(self, pipeline: str):
        with self._lock:
            if pipeline in self._logs:
                self._logs[pipeline] = []

    def log(self, pipeline: str, message: str):
        with self._lock:
            if pipeline in self._logs:
                log_line = f"[{datetime_now_str()}] {message}"
                self._logs[pipeline].append(log_line)
                logger.info(f"[{pipeline.upper()}] {message}")

    def get_logs(self, pipeline: str) -> list[str]:
        with self._lock:
            return list(self._logs.get(pipeline, []))

def datetime_now_str() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%H:%M:%S")

# Global singleton
pipeline_logger = PipelineLogger()
