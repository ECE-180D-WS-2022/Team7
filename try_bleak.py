import asyncio
from bleak import BleakScanner
from bleak import BleakClient
import logging
import struct

logger = logging.getLogger(__name__)


class Connection:
    
    client: BleakClient = None
    
    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        max_x_characteristic: str,
        max_z_characteristic: str
    ):
        self.loop = loop
        self.max_x_characteristic = max_x_characteristic
        self.max_z_characteristic = max_z_characteristic
        
        # Device state
        self.connected = False
        self.connected_device = None

        self.max_x_data = []
        self.max_z_data = []

    def on_disconnect(self, client: BleakClient):
        self.connected = False
        # Put code here to handle what happens on disconnet.
        print(f"Disconnected from {self.connected_device.name}!")

    def max_x_characteristic_handler(self, sender: str, data: bytearray):
        print("X value:")
        clean_data = struct.unpack('f', data)
        print(clean_data)

    def max_z_characteristic_handler(self, sender: str, data: bytearray):
        print("Z value:")
        clean_data = struct.unpack('f', data)
        print(clean_data)

    async def manager(self):
        print("Starting connection manager.")
        while True:
            if self.client:
                await self.connect()
            else:
                await self.select_device()
                await asyncio.sleep(15.0, loop=loop) 

    async def connect(self):
        if self.connected:
            return
        try:
            # print("here now")
            # print(self.client)
            await self.client.connect()
            print("client was connected")
            # self.connected = await self.client.is_connected()
            # if self.connected:
            if self.client.is_connected():
                print(f"Connected to {self.connected_device.name}")
                self.client.set_disconnected_callback(self.on_disconnect)

                await self.client.start_notify(
                    self.max_x_characteristic, self.max_x_characteristic_handler,
                )
                await self.client.start_notify(
                    self.max_z_characteristic, self.max_z_characteristic_handler,
                )
                while True:
                    if not self.connected:
                        break
                    for service in self.client.services:
                        for char in service.characteristics:
                            if "read" in char.properties:
                                value = bytes(await self.client.read_gatt_char(char.uuid))
                                print(f"\t[Characteristic] {char} ({','.join(char.properties)}), Value: {value}")
                    await asyncio.sleep(5.0, loop=loop)
                    
            else:
                print(f"Failed to connect to {self.connected_device.name}")
        except Exception as e:
            print(e)
    
    async def cleanup(self):
        if self.client:
            await self.client.stop_notify(max_x_characteristic)
            await self.client.stop_notify(max_z_characteristic)
            await self.client.disconnect()

    async def select_device(self):
        print("Bluetooh LE hardware warming up...")
        await asyncio.sleep(2.0, loop=loop) # Wait for BLE to initialize.
        # devices = await BleakScanner.discover()

        # print("Please select device: ")
        # for i, device in enumerate(devices):
        #     print(f"{i}: {device.name}")

        # response = -1
        # while True:
        #     response = input("Select device: ")
        #     try:
        #         response = int(response.strip())
        #     except:
        #         print("Please make valid selection.")
            
        #     if response > -1 and response < len(devices):
        #         break
        #     else:
        #         print("Please make valid selection.")
        
        # print(f"Connecting to {devices[response].name}")
        # self.connected_device = devices[response]
        # self.client = BleakClient(devices[response].address)
        self.client = BleakClient("E8:1B:8C:C4:B0:B5")
        # print("here")



if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

    loop = asyncio.get_event_loop()
    max_x_characteristic = "00001142-0000-1000-8000-00805f9b34fb"
    max_z_characteristic = "00001143-0000-1000-8000-00805f9b34fb"
    connection = Connection(
        loop, max_x_characteristic, max_z_characteristic,)
    try:
        # asyncio.ensure_future(main())
        asyncio.ensure_future(connection.manager())
        # asyncio.ensure_future(user_console_manager(connection))
        loop.run_forever()
    except KeyboardInterrupt:
        print()
        print("User stopped program.")
    finally:
        print("Disconnecting...")
        loop.run_until_complete(connection.cleanup())
