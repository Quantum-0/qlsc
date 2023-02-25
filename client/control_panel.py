from typing import List

import fastapi.exceptions
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from engine import QLPEngine
from models.device import QLSCDevice

app = FastAPI()
engine = QLPEngine().start()


@app.get('/livecheck')
async def live_check():
    return {'live': 'ok'}


@app.get('/api/devices/search', response_model=List[QLSCDevice])
async def search_for_devices():
    devices = await engine.discover_all_devices()
    devices.add(QLSCDevice(ip='1.2.3.4', device_chip_id='ABCDE', device_uuid='12345', name='Test Device'))
    return devices


@app.get('/api/devices/{device_uuid}', response_model=QLSCDevice)
async def get_device_by_uuid(device_uuid):
    device = engine[device_uuid]
    if not device:
        raise fastapi.exceptions.HTTPException(404)
    return device
    # return QLSCDevice(ip='1.2.3.4', device_chip_id='ABCDE', device_uuid='12345', name='Test Device')


app.mount("/", StaticFiles(directory="web/public", html=True))
