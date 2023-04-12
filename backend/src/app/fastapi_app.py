from datetime import datetime
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from wakeonlan import send_magic_packet

from models import Device, Session

app = FastAPI()


class WakeOnLANRequest(BaseModel):
    mac_address: str


class WakeOnLANResponse(BaseModel):
    success: bool


class DeviceModel(BaseModel):
    ip_address: str
    mac_address: str
    hostname: str
    last_seen: datetime


class DevicesResponse(BaseModel):
    success: bool
    devices: list[DeviceModel]


class WakeError(Exception):
    def __init__(self, message: str):
        self.message = message


class DevicesError(Exception):
    def __init__(self, message: str):
        self.message = message


@app.exception_handler(WakeError)
async def handle_wake_error(request, exc: WakeError):
    return JSONResponse(
        status_code=500,
        content={"detail": {"error": exc.message}},
    )


@app.exception_handler(DevicesError)
async def handle_devices_error(request, exc: DevicesError):
    return JSONResponse(
        status_code=500,
        content={"detail": {"error": exc.message}},
    )


@app.post("/wake", response_model=WakeOnLANResponse)
async def wake_on_lan(request: WakeOnLANRequest):
    try:
        send_magic_packet(request.mac_address)
        return {"success": True}
    except Exception as e:
        raise WakeError(f"Error sending magic packet: {str(e)}")


@app.get("/devices", response_model=DevicesResponse)
def devices() -> DevicesResponse:
    try:
        session = Session()
        devices = session.query(Device).all()
        session.close()
    except Exception as e:
        raise DevicesError(f"Error getting devices: {str(e)}")

    return {
        "success": True,
        "devices": [
            {
                "ip_address": device.ip_address,
                "mac_address": device.mac_address,
                "hostname": device.hostname,
                "last_seen": device.last_seen.isoformat(),
            }
            for device in devices
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
