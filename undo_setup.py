import os
import subprocess
import shutil
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    handlers=[logging.FileHandler("debug_undo.log"), logging.StreamHandler()],
)

logger = logging.getLogger()


def check_permissions():
    if os.geteuid() != 0:
        logger.error(
            "This script requires root privileges to manage systemd services and timers. Please run with sudo."
        )
        exit(1)


def run_command(command, continue_on_error=False):
    logger.debug(f"Running Command: {''.join(command)}")
    result = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True
    )

    if result.returncode != 0:
        logger.error(f"Error: {result.stderr}")
        if not continue_on_error:
            exit(1)

    return result.stdout, result.stderr


def disable_and_stop_systemd(unit_name):
    run_command(f"sudo systemctl stop {unit_name}", continue_on_error=True)
    run_command(f"sudo systemctl disable {unit_name}", continue_on_error=True)
    run_command(f"sudo rm /etc/systemd/system/{unit_name}", continue_on_error=True)


check_permissions()

logger.debug("Undo script started")

# Set your project path and virtual environment path
project_path = os.getcwd()
username = os.environ.get("USER")
venv_path = f"home/{username}/logger_env"

# Delete virtual environment
shutil.rmtree(venv_path, ignore_errors=True)

# Disable and stop systemd units
unit_names = [
    "main_query.service",
    "main_query.timer",
    "shutdown.service",
    "shutdown.timer",
    "rtcwake.service",
    "rtcwake.timer",
    "disable_sleep.service",
]

for unit_name in unit_names:
    disable_and_stop_systemd(unit_name)

# Remove run_on_connection.sh script
os.remove("run_on_connection.sh")

logger.debug("Undo script finished")
