import os
import subprocess
import shutil
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    handlers=[logging.FileHandler("debug.log"), logging.StreamHandler()],
)

logger = logging.getLogger()


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
commands = [
    "pip install --upgrade pip",
    "pip install pycampbellcr1000 pandas ndjson",
    "pip install --upgrade google-cloud-storage",
    "pip install --upgrade google-cloud-bigquery",
]

for cmd in commands:
    stdout, stderr = run_command(cmd, continue_on_error=True)
    logger.debug(stdout)

sudo_path = shutil.which("sudo")

# Create and Configure Systemd Services and Timers
units = [
    {
        "name": "main_query",
        "timer": f"""[Unit]
Description=Run main_query.service every hour and after booting

[Timer]
OnBootSec=5min
OnCalendar=*-*-* *:*:10
Unit=main_query.service

[Install]
WantedBy=timers.target
""",
        "service": f"""[Unit]
Description=Run main_query.py after an Internet connection is established
Wants= main_query.timer
Conflicts=shutdown.service

[Service]
Type=simple
User=root
ExecStart=python {project_path}/main_query.py
Restart=on-failure
StandardOutput=file:{systemd_reports_path}/main_query.stdout
StandardError=file:{systemd_reports_path}/main_query.stderr
""",
    },
    {
        "name": "disable_sleep",
        "service": f"""[Unit]
Description=Disable sleep and power management features

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'echo 0 > /sys/devices/platform/soc/3f980000.usb/buspower; echo 0 > /sys/devices/platform/soc/3f980000.usb/power/control; setterm -blank 0 -powersave off -powerdown 0'
StandardOutput=file:{systemd_reports_path}/disable_sleep.stdout
StandardError=file:{systemd_reports_path}/disable_sleep.stderr
""",
    },
]

# Create, enable, and start the systemd units
for unit in units:
    service_file = create_file(f"{unit['name']}.service", unit["service"])
    run_command(
        f"sudo cp {service_file} /etc/systemd/system/{service_file}",
        continue_on_error=True,
    )
    enable_and_start_systemd(service_file)

    if "timer" in unit:
        timer_file = create_file(f"{unit['name']}.timer", unit["timer"])
        run_command(
            f"sudo cp {timer_file} /etc/systemd/system/{timer_file}",
            continue_on_error=True,
        )
        enable_and_start_systemd(timer_file)

logger.debug("Script finished")
