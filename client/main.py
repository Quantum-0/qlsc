import asyncio
import logging

from engine import QLPEngine
from models.color import Color
from models.device import QLSCDevice

logging.basicConfig(level=logging.DEBUG)


async def main():
    eng = QLPEngine()
    eng.start()
    # eng.start()
    await asyncio.sleep(1)
    devs = await eng.discover_all_devices()
    print(devs)
    if devs:
        print('Device was found')
        d = list(devs)[0]
    else:
        print('Emulating device')
        d = QLSCDevice(ip='1.2.3.4', device_chip_id='ABCDE', device_uuid='12345', name='Test Device')
        # setattr(d, '_engine', eng)
        d.set_engine(eng)
    await d.set_length(30)
    # await asyncio.sleep(1)
    await d.fill(Color(3, 1, 4))
    # await asyncio.sleep(1)
    await d.set_pixel_color(5,Color(5,0,5))
    # await d.set_line_color(2,3,Color(5,5,5))
    # for i in range(500):
        # await d.set_pixel_color(i % 30, Color(i%5,i%6,i%7))
        # await asyncio.sleep(0.1)
        # await d.set_pixel_color(i % 30, Color(0,0,0))
        # await asyncio.sleep(0.02)
    await asyncio.sleep(5)
    await d.reboot()
    eng.stop()
    # eng.stop()


if __name__ == '__main__':
    asyncio.run(main())


# TODO:
#  - this will be protocol implementation
#  - make control panel - web ui, working with that protocol
