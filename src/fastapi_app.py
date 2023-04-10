from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from scapy.all import ARP, Ether, srp
from wakeonlan import send_magic_packet

from models import Device, Session

app = FastAPI()


class WakeOnLANRequest(BaseModel):
    mac_address: str
    ip_address: Optional[str] = None
    port: Optional[int] = 9


class WakeOnLANResponse(BaseModel):
    success: bool


class DeviceModel(BaseModel):
    ip_address: str
    mac_address: str
    last_seen: datetime


class ScanResponse(BaseModel):
    success: bool
    devices: list[DeviceModel]


class WakeError(Exception):
    def __init__(self, message: str):
        self.message = message


class NetworkScanError(Exception):
    def __init__(self, message: str):
        self.message = message


@app.exception_handler(WakeError)
async def handle_wake_error(request, exc: WakeError):
    return JSONResponse(
        status_code=500,
        content={"detail": {"error": exc.message}},
    )


@app.exception_handler(NetworkScanError)
async def handle_network_scan_error(request, exc: NetworkScanError):
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


@app.get("/scan", response_model=ScanResponse)
def scan(from_database: bool = Query(False)) -> ScanResponse:
    session = Session()
    if not from_database:
        try:
            network_ip = "192.168.4.0/24"
            arp_request = ARP(pdst=network_ip)
            broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
            arp_request_broadcast = broadcast / arp_request
            answered, _ = srp(arp_request_broadcast, timeout=2, verbose=False)

            session = Session()
            now = datetime.utcnow()

            for _, received in answered:
                ip_address = received.psrc
                mac_address = received.hwsrc
                device = (
                    session.query(Device)
                    .filter(Device.mac_address == mac_address)
                    .one_or_none()
                )
                if device:
                    device.last_seen = now
                else:
                    new_device = Device(
                        ip_address=ip_address, mac_address=mac_address, last_seen=now
                    )
                    session.add(new_device)
            session.commit()
        except Exception as e:
            raise NetworkScanError(f"Error scanning network: {str(e)}")

    devices = session.query(Device).all()
    session.close()

    return {
        "success": True,
        "devices": [
            {
                "ip_address": device.ip_address,
                "mac_address": device.mac_address,
                "last_seen": device.last_seen.isoformat(),
            }
            for device in devices
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
