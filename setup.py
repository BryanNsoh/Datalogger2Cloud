import os
import subprocess
import shutil
from pathlib import Path


def check_permissions():
    if os.geteuid() != 0:
        print(
            "This script requires root privileges to manage systemd services and timers. Please run with sudo."
        )
        exit(1)


def run_command(command, continue_on_error=False):
    print(f"Running Command: {''.join(command)}")
    result = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True
    )

    if result.returncode != 0:
        print(f"Error: {result.stderr}")
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

# Set your project path and virtual environment path
project_path = os.getcwd()
venv_path = os.path.expanduser("~/logger_env")

# 1. Create and Activate Virtual Environment
commands = [
    f"python3 -m venv {venv_path}",
    f". {venv_path}/bin/activate",
]

for cmd in commands:
    stdout, stderr = run_command(cmd, continue_on_error=True)
    print(stdout)

# 2. Install and Upgrade Python Modules
commands = [
    "pip install --upgrade pip",
    "pip install pycampbellcr1000 pandas ndjson",
    "pip install --upgrade google-cloud-storage",
    "pip install --upgrade google-cloud-bigquery",
]

for cmd in commands:
    stdout, stderr = run_command(cmd, continue_on_error=True)
    print(stdout)

shutdown_path = shutil.which("shutdown")
rtcwake_path = shutil.which("rtcwake")
sudo_path = shutil.which("sudo")

# 3. Create and Configure Systemd Services and Timers
units = [
    # ...
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
]

# Create, enable, and start the systemd units
for unit in units:
    service_file = create_file(f"{unit['name']}.service", unit["service"])
    timer_file = create_file(f"{unit['name']}.timer", unit["timer"])
    run_command(
        f"sudo cp {service_file} /etc/systemd/system/{service_file}",
        continue_on_error=True,
    )
    run_command(
        f"sudo cp {timer_file} /etc/systemd/system/{timer_file}", continue_on_error=True
    )
    enable_and_start_systemd(service_file)


run_on_connection_content = f"""#!/bin/bash
# Wait for an internet connection
while ! ping -c 1 -W 1 8.8.8.8; do
  sleep 1
done

# Update the system time
sudo chronyc -a makestep

# Run the Python script
{venv_path}/bin/python {project_path}/main_query.py
"""

create_file("run_on_connection.sh", run_on_connection_content)

# Make the script executable
run_command("chmod +x run_on_connection.sh", continue_on_error=True)
