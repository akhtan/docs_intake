import logging

# ==========================================
# 1. LOGGING SETUP
# ==========================================
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log_format = '%(asctime)s - %(levelname)s - %(message)s'
# Create a handler for writing to a text file
file_handler = logging.FileHandler("ingestion_logs.txt", mode="a", encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(log_format))

# Create a handler for printing to your local PC terminal console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(log_format))

# Get the root logger and attach both handlers
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# This logger instance will now write to both destinations
logger = logging.getLogger(__name__)