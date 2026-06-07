import logging
import os
import sys
import io
from datetime import datetime

# Create logs directory if it doesn't exist
LOGS_DIR = "logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Create log filename with timestamp
log_filename = os.path.join(
    LOGS_DIR,
    f"stock_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
)

# File handler with UTF-8 encoding
file_handler = logging.FileHandler(log_filename, encoding="utf-8")
file_handler.setLevel(logging.INFO)

# Stream handler that wraps stdout buffer with UTF-8 and replace errors
stream_buffer = getattr(sys.stdout, "buffer", None)
if stream_buffer is not None:
    stream = io.TextIOWrapper(stream_buffer, encoding="utf-8", errors="replace", line_buffering=True)
else:
    # Fallback if buffer is not available
    stream = sys.stdout

stream_handler = logging.StreamHandler(stream)
stream_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Configure root logger
root = logging.getLogger()
if not root.handlers:
    root.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(stream_handler)


def get_logger(name):
    return logging.getLogger(name)
