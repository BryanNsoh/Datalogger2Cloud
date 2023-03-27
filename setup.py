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
    logger.debug(f"Running Command: {''.join(command)}")
    result = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True
    )

    if result.returncode != 0:
        logger.error(f"Error: {result.stderr}")
        if not continue_on_error:
            exit(1)

    return result.stdout, result.stderr


def source_venv(venv_path, command):
    return f". {venv_path}/bin/activate && {command}"


def create_file(file_name, content):
    with open(file_name, "w") as f:
        f.write(content)
    return file_name


def enable_and_start_systemd(unit_name):
    run_command(f"sudo systemctl enable {unit_name}", continue_on_error=True)
    run_command(f"sudo systemctl start {unit_name}", continue_on_error=True)


check_permissions()

logger.debug("Script started")

# Set your project path and virtual environment path
project_path = os.getcwd()
venv_path = f"{project_path}/logger_env"

# 1. Create and Activate Virtual Environment
commands = [
    f"python3 -m venv {venv_path}",
    f". {venv_path}/bin/activate",
]

for cmd in commands:
    stdout, stderr = run_command(cmd, continue_on_error=True)
    logger.debug(stdout)

# 2. Install and Upgrade Python Modules
commands = [
    "pip install --upgrade pip --user",
    "pip install pycampbellcr1000 pandas ndjson --user",
    "pip install --upgrade google-cloud-storage --user",
    "pip install --upgrade google-cloud-bigquery --user",
]

for cmd in commands:
    stdout, stderr = run_command(cmd, continue_on_error=True)
    logger.debug(stdout)

shutdown_path = shutil.which("shutdown")
rtcwake_path = shutil.which("rtcwake")
sudo_path = shutil.which("sudo")

# 3. Create and Configure Systemd Services and Timers
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
User=pi
ExecStart={venv_path}/bin/python {project_path}/run_on_connection.sh
Restart=on-failure
""",
    },
    {
        "name": "rtcwake",
        "timer": f"""[Unit]
Description=Run rtcwake.service 1min before shutdown.service

[Timer]
OnCalendar=*-*-* 20:59:00
Unit=rtcwake.service

[Install]
WantedBy=timers.target
""",
        "service": f"""[Unit]
Description=Power on the computer 8 hours after shutdown

[Service]
Type=oneshot
ExecStart={sudo_path} {rtcwake_path} -m no -s 28800
""",
    },
    {
        "name": "disable_sleep",
        "service": f"""[Unit]
Description=Disable sleep and power management features

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'echo 0 > /sys/devices/platform/soc/3f980000.usb/buspower; echo 0 > /sys/devices/platform/soc/3f980000.usb/power/control; setterm -blank 0 -powersave off -powerdown 0'
""",
    },
    {
        "name": "shutdown",
        "timer": f"""[Unit]
Description=Run shutdown.service at 9 PM every day

[Timer]
OnCalendar=*-*-* 21:00:00
Unit=shutdown.service

[Install]
WantedBy=timers.target
""",
        "service": f"""[Unit]
Description=Shut down the computer at 9 PM every day

[Service]
Type=oneshot
ExecStart={sudo_path} {shutdown_path} -h now
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


run_on_connection_content = f"""#!/bin/bash
set -x

log_file="run_on_conn_log.txt"
# Redirect both stdout and stderr to the log file
exec > >(tee -a "$log_file") 2>&1

echo "Starting script"

# Wait for an internet connection
echo "Checking for internet connection"
while ! ping -c 1 -W 1 8.8.8.8; do
  sleep 1
done
echo "Internet connection established"

# Update the system time
echo "Updating system time"
sudo chronyc -a makestep

# Run the Python script
echo "Running main_query.py"
{venv_path}/bin/python {project_path}/main_query.py

echo "Script finished"
"""

create_file("run_on_connection.sh", run_on_connection_content)

# Make the script executable
run_command("chmod +x run_on_connection.sh", continue_on_error=True)

logger.debug("Script finished")
