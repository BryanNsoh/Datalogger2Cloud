import serial.tools.list_ports


def get_connected_devices():
    connected_devices = []

    for port in serial.tools.list_ports.comports():
        device = {
            "name": port.device,
            "description": port.description,
            "hwid": port.hwid,
            "vid": port.vid,
            "pid": port.pid,
            "serial_number": port.serial_number,
        }
        connected_devices.append(device)

    return connected_devices


def print_devices(devices):
    for device in devices:
        print(f"Name: {device['name']}")
        print(f"Description: {device['description']}")
        print(f"HWID: {device['hwid']}")
        print(f"VID: {device['vid']}")
        print(f"PID: {device['pid']}")
        print(f"Serial Number: {device['serial_number']}")
        print("----------------------")


if __name__ == "__main__":
    devices = get_connected_devices()
    print_devices(devices)
