import os
import subprocess
import shlex


def run_command(command):
    print(f"Running Command: {''.join(command)}")
    result = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True
    )

    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        exit(1)

    return result.stdout, result.stderr


def source_venv(venv_path, command):
    return f". {venv_path}/bin/activate && {command}"


# Set your project path and virtual environment path
project_path = os.getcwd()
venv_path = os.path.expanduser("~/logger_env")

# 1. Create and Activate Virtual Environment
commands = [
    f"python3 -m venv {venv_path}",
    f". {venv_path}/bin/activate",
]

for cmd in commands:
    stdout, stderr = run_command(cmd)
    print(stdout)

# 2. Install and Upgrade Python Modules
commands = [
    "pip install --upgrade pip",
    "pip install pycampbellcr1000 pandas ndjson",
    "pip install --upgrade google-cloud-storage",
    "pip install --upgrade google-cloud-bigquery",
]

for cmd in commands:
    stdout, stderr = run_command(cmd)
    print(stdout)

# 3.1 Create main_query.service
service_content = f"""[Unit]
Description=Run main_query.py after an Internet connection is established
Wants=network-online.target main_query.timer

[Service]
Type=simple
User=pi
ExecStart={venv_path}/bin/python {project_path}/run_on_connection.sh
Restart=on-failure
"""

with open("main_query.service", "w") as f:
    f.write(service_content)

# 3.2 Create main_query.timer
timer_content = f"""[Unit]
Description=Run main_query.service every hour

[Timer]
OnBootSec=5min
OnUnitActiveSec=1h
Unit=main_query.service

[Install]
WantedBy=timers.target
"""

with open("main_query.timer", "w") as f:
    f.write(timer_content)

# 3.3 Create run_on_connection.sh
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

with open("run_on_connection.sh", "w") as f:
    f.write(run_on_connection_content)

# Make the script executable
run_command("chmod +x run_on_connection.sh")

# Copy the systemd service and timer files
run_command("sudo cp main_query.service /etc/systemd/system/main_query.service")
run_command("sudo cp main_query.timer /etc/systemd/system/main_query.timer")

# Enable the systemd service and timer
run_command("sudo systemctl enable main_query.service")
run_command("sudo systemctl enable main_query.timer")

# Start the systemd service and timer
run_command("sudo systemctl start main_query.service")
