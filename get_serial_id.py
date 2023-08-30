import serial.tools.list_ports


def list_ports_with_details():
    # Get list of all connected ports
    ports = serial.tools.list_ports.comports()

    # Create an empty list to hold the port info
    port_info_list = []

    # Loop over each port and get its details
    for port in ports:
        port_info = {
            "device": port.device,
            "name": port.name,
            "description": port.description,
            "hwid": port.hwid,
            "vid": port.vid,
            "pid": port.pid,
            "serial_number": port.serial_number,
            "location": port.location,
            "manufacturer": port.manufacturer,
            "product": port.product,
            "interface": port.interface,
        }
        port_info_list.append(port_info)

    # Return the list of port info
    return port_info_list


# Now we call the function and print out the info
ports = list_ports_with_details()
for port in ports:
    print(port)
