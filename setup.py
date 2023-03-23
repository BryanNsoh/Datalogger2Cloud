import os
import subprocess


def run_command(command):
    process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()
    return stdout, stderr


# Set your project path and virtual environment path
project_path = os.getcwd()
venv_path = os.path.expanduser("~/logger_env")

# 1. Create and Activate Virtual Environment
commands = [
    f"python3 -m venv {venv_path}",
    f"source {venv_path}/bin/activate",
]

for cmd in commands:
    stdout, stderr = run_command(cmd)
    print(stdout.decode())

# Update environment variables to use the virtual environment
os.environ["PATH"] = f"{venv_path}/bin:" + os.environ["PATH"]
os.environ["VIRTUAL_ENV"] = venv_path

# 2. Install and Upgrade Python Modules
commands = [
    "pip install --upgrade pip",
    "pip install pycampbellcr1000 pandas ndjson",
    "pip install --upgrade google-cloud-storage",
    "pip install --upgrade google-cloud-bigquery",
    "sudo apt-get install chrony",
]

for cmd in commands:
    stdout, stderr = run_command(cmd)
    print(stdout.decode())

# 3.1 Create first_start_flag.txt
with open("first_start_flag.txt", "w") as f:
    f.write("0")

# 3.2 Create main_query.service
service_content = f"""[Unit]
Description=Run main_query.py after an Internet connection is established
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=pi
ExecStart={venv_path}/bin/python {project_path}/run_on_connection.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
"""

with open("main_query.service", "w") as f:
    f.write(service_content)

# 3.3 Create run_on_connection.sh
run_on_connection_content = f"""#!/bin/bash
while true; do
  # Wait for an internet connection
  while ! ping -c 1 -W 1 8.8.8.8; do
    sleep 1
  done

  # Update the system time
  sudo chronyc -a makestep

  # Run the Python script
  {venv_path}/bin/python {project_path}/main_query.py

  # Sleep for an hour
  sleep 3600
done
"""

with open("run_on_connection.sh", "w") as f:
    f.write(run_on_connection_content)

# Make the script executable
run_command("chmod +x run_on_connection.sh")

# Copy the systemd service file
run_command(f"sudo cp main_query.service /etc/systemd/system/main_query.service")

# Enable the systemd service
run_command("sudo systemctl enable main_query.service")

# Start the systemd service
run_command("sudo systemctl start main_query.service")

print("Setup complete!")
