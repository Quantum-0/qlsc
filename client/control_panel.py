import fastapi.exceptions
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from engine import QLPEngine
from models.device import QLSCDevice

app = FastAPI()


@app.get('/livecheck')
async def live_check():
    return {'live': 'ok'}


@app.get('/api/devices/search')
async def search_for_devices():
    QLPEngine().start()
    devices = await QLPEngine().discover_all_devices()
    devices.add(QLSCDevice(ip='1.2.3.4', device_chip_id='ABCDE', device_uuid='12345', name='Test Device'))
    return devices

@app.get('/api/devices/{device_uuid}')
async def get_device_by_uuid(device_uuid):
    if device_uuid == '12345':
        return QLSCDevice(ip='1.2.3.4', device_chip_id='ABCDE', device_uuid='12345', name='Test Device')
    raise fastapi.exceptions.HTTPException(404)


app.mount("/", StaticFiles(directory="web/public", html=True))
