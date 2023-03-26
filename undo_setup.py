import os
import subprocess


def run_command(command):
    print(f"Running Command: {command}")
    result = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True
    )

    if result.returncode != 0:
        print(f"Error: {result.stderr}")

    return result.stdout, result.stderr


# Set your virtual environment path
venv_path = os.path.expanduser("~/logger_env")

# 1. Disable and stop the systemd service and timer
run_command("sudo systemctl disable main_query.service")
run_command("sudo systemctl disable main_query.timer")
run_command("sudo systemctl stop main_query.service")

# 2. Remove the systemd service and timer files
run_command("sudo rm /etc/systemd/system/main_query.service")
run_command("sudo rm /etc/systemd/system/main_query.timer")

# 3. Remove the created files
os.remove("run_on_connection.sh")
os.remove("main_query.timer")
os.remove("main_query.service")
os.remove("first_start_flag.txt")

print("Reversed actions successfully.")
