import serial.tools.list_ports
import serial
import time
from datetime import datetime
import json

rev_date = "2018-12-03"
version = "1.0"

print("+-" * 40)
print("Simple SDI-12 Sensor Reader", version)
print(
    "Designed for Dr. Liu's family of SDI-12 USB adapters (standard,analog,GPS)\n\tDr. John Liu Saint Cloud MN USA",
    rev_date,
    "\n\t\tFree software GNU GPL V3.0",
)
print(
    "\nCompatible with PCs running Win 7/10, GNU/Linux, Mac OSX, Raspberry PI, Beagle Bone Black"
)
print("\nThis program requires Python 3.4, Pyserial 3.0")
print("\nFor assistance with customization, telemetry etc., contact Dr. Liu.")
print("\nhttps://liudr.wordpress.com/gadget/sdi-12-usb-adapter/")
print("+-" * 40)

port_names = []
a = serial.tools.list_ports.comports()
print("\nDetected the following serial ports:")
i = 0
for w in a:
    vidn = w.vid if (type(w.vid) is int) else 0
    print("%d)\t%s\t(USB VID=%04X)" % (i, w.device, vidn))
    i = i + 1
user_port_selection = input(
    "\nSelect port from list (0,1,2...). SDI-12 adapter has USB VID=0403:"
)
# Store the device name to open port with later in the script.
port_device = a[int(user_port_selection)].device

ser = serial.Serial(port=port_device, baudrate=9600, timeout=10)
time.sleep(2.5)  # delay for arduino bootloader and the 1 second delay of the adapter.


# Initialize sensor data dictionary
sensor_data = {}


def read_sensor_data(ser, sdi_12_address, measurement_code):
    # Send the measurement command to the sensor
    ser.write(sdi_12_address + b"M" + measurement_code + b"!")
    # Read and discard the first line of the response
    sdi_12_line = ser.readline()

    # Read and discard the second line of the response
    sdi_12_line = ser.readline()

    # Send the data command to the sensor
    ser.write(sdi_12_address + b"D0!")
    # Read the third line of the response, which contains the data
    sdi_12_line = ser.readline()

    # Remove the newline characters from the end of the line
    sdi_12_line = sdi_12_line[:-2]
    # Split the response into a list of values, excluding the first element (sensor address)
    sensor_values = sdi_12_line.decode("utf-8").split("+")[1:]

    # Iterate through the sensor values
    for i, value in enumerate(sensor_values):
        # If a negative sign is found in the value (indicating a diagnostic value)
        if "-" in value:
            # Split the value at the negative sign, keeping only the first part (soil moisture value)
            sensor_values[i] = value.split("-")[0]

    # Return the list of cleaned sensor values
    return sensor_values


# Rest of the code for setting up the serial connection

sensor_0_temperature = None
sensor_1_soil_moisture = None

while True:
    try:
        sensor_0_values = read_sensor_data(ser, b"0", b"1")
        if len(sensor_0_values) >= 2:
            sensor_0_temperature = float(sensor_0_values[1])

        sensor_1_values = read_sensor_data(ser, b"1", b"1")
        if len(sensor_1_values) >= 2:
            sensor_1_soil_moisture = float(sensor_1_values[0])

        if sensor_0_temperature is not None:
            print("Apogee temperature: {:.4f} °C".format(sensor_0_temperature))

        if sensor_1_soil_moisture is not None:
            print("CS655 soil moisture: {:.4f} cm^3/cm".format(sensor_1_soil_moisture))

        sensor_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "apogee_temperature": {"value": sensor_0_temperature, "unit": "°C"},
            "cs655_soil_moisture": {
                "value": sensor_1_soil_moisture,
                "unit": "cm^3/cm^3",
            },
        }

        with open("./sensor_data.json", "a") as f:
            json.dump(sensor_data, f)
            f.write("\n")

        time.sleep(1)

    except KeyboardInterrupt:
        print("Interrupted by user. Exiting...")
        break
    except Exception as e:
        print(f"Error: {str(e)}")
