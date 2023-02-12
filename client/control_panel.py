from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from engine import QLPEngine
from models.device import QLSCDevice
from web.models.device import Device

app = FastAPI()


@app.get('/livecheck')
async def live_check():
    return {'live': 'ok'}


@app.get('/api/devices/search')
async def search_for_devices():
    QLPEngine().start()
    devices = await QLPEngine().discover_all_devices()
    devices.add(QLSCDevice('1.2.3.4', 'ABCDE', '12345', 'Test Device', QLPEngine()))
    return [Device.from_dc(dev) for dev in devices]


app.mount("/", StaticFiles(directory="web/public", html=True))
