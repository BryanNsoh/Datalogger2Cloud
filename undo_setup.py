import os
import subprocess
import shutil
from pathlib import Path
import logging
import json

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    handlers=[logging.FileHandler("undo_debug.log"), logging.StreamHandler()],
)

logger = logging.getLogger()

# Load configuration from config.json
with open("./config.json", "r") as config_file:
    config = json.load(config_file)


def check_permissions():
    if os.geteuid() != 0:
        logger.error(
            "This script requires root privileges to manage systemd services and timers. Please run with sudo."
        )
        exit(1)


def run_command(command, continue_on_error=False):
    logger.debug(f"Running Command: {command}")
    result = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True
    )

    if result.returncode != 0:
        logger.error(f"Error: {result.stderr}")
        if not continue_on_error:
            exit(1)

    return result.stdout, result.stderr


def disable_and_stop_systemd(unit_name):
    logger.debug(f"Disabling and stopping systemd unit: {unit_name}")
    run_command(f"sudo systemctl disable {unit_name}", continue_on_error=True)
    run_command(f"sudo systemctl stop {unit_name}", continue_on_error=True)


check_permissions()

logger.debug("Undo script started")

# Set your project path
project_path = os.getcwd()

# Disable and stop the systemd units
units = config["units"]

for unit in units:
    service_file = f"{unit['name']}.service"
    timer_file = f"{unit['name']}.timer"

    disable_and_stop_systemd(service_file)
    run_command(f"sudo rm /etc/systemd/system/{service_file}", continue_on_error=True)

    if "timer" in unit:
        disable_and_stop_systemd(timer_file)
        run_command(f"sudo rm /etc/systemd/system/{timer_file}", continue_on_error=True)

# Remove systemd_reports directory if empty
systemd_reports_path = os.path.join(project_path, "systemd_reports")

try:
    os.rmdir(systemd_reports_path)
    logger.debug(f"Removed empty directory: {systemd_reports_path}")
except OSError as e:
    logger.warning(f"Directory not removed: {systemd_reports_path}. Reason: {e}")

logger.debug("Undo script finished")
