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
    handlers=[logging.FileHandler("debug.log"), logging.StreamHandler()],
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


def create_file(file_name, content):
    with open(file_name, "w") as f:
        f.write(content)
    return file_name


def enable_and_start_systemd(unit_name):
    logger.debug(f"Enabling and starting systemd unit: {unit_name}")
    run_command(f"sudo systemctl enable {unit_name}", continue_on_error=True)
    run_command(f"sudo systemctl start {unit_name}", continue_on_error=True)


check_permissions()

logger.debug("Script started")

# Set your project path
project_path = os.getcwd()

# Create systemd_reports directory
systemd_reports_path = os.path.join(project_path, "systemd_reports")
os.makedirs(systemd_reports_path, exist_ok=True)

# Install and Upgrade Python Modules
commands = config["commands"]

for cmd in commands:
    stdout, stderr = run_command(cmd, continue_on_error=True)
    logger.debug(stdout)

sudo_path = shutil.which("sudo")

# Create and Configure Systemd Services and Timers
units = config["units"]

# Create, enable, and start the systemd units
for unit in units:
    logger.debug(f"Creating systemd unit: {unit['name']}.service")
    service_content = unit["service"].format(
        project_path=project_path, systemd_reports_path=systemd_reports_path
    )
    service_file = create_file(f"{unit['name']}.service", service_content)
    run_command(
        f"sudo cp {service_file} /etc/systemd/system/{service_file}",
        continue_on_error=True,
    )
    enable_and_start_systemd(service_file)

    if "timer" in unit:
        logger.debug(f"Creating systemd timer: {unit['name']}.timer")
        timer_file = create_file(f"{unit['name']}.timer", unit["timer"])
        run_command(
            f"sudo cp {timer_file} /etc/systemd/system/{timer_file}",
            continue_on_error=True,
        )
        enable_and_start_systemd(timer_file)

logger.debug("Script finished")
