import argparse
import asyncio
import os
from pathlib import Path
from typing import Dict
from uuid import NAMESPACE_OID
from uuid import uuid3
from uuid import uuid4

from at_queue.core.session import ConnectionParameters
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Query
from fastapi import Request
from fastapi import status
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uvicorn import Config as UviConfig
from uvicorn import Server

from at_joint.debug.debugger import ATJointDebugger
from at_joint.debug.models import ProcessTactModel


EXCHANGE_NAME = "at-joint-debugger-" + str(uuid3(NAMESPACE_OID, "at-joint-debugger"))


# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, auth_token: str, session_id: str, websocket: WebSocket):
        await websocket.accept()
        sessions = self.active_connections.get(auth_token, {})
        sessions[session_id] = websocket
        self.active_connections[auth_token] = sessions

    def disconnect(self, auth_token: str, session_id: str):
        sessions = self.active_connections.get(auth_token, {})
        sessions.pop(session_id, None)
        self.active_connections[auth_token] = sessions

    async def send_message(self, auth_token: str, message: str):
        sessions = self.active_connections.get(auth_token, {})
        for _, websocket in sessions.items():
            await websocket.send_text(message)


manager = ConnectionManager()


class GLOBAL:
    inspector: ATJointDebugger = None


CURRENT_FILE_PATH = Path(__file__).resolve()


def get_args() -> dict:
    parser = argparse.ArgumentParser(
        prog="at-joint-debugger",
        description="Debugging server for joint functioning component "
        "for AT_SIMULATION, AT_TEMPORAL_SOLVER and AT_SOLVER",
    )

    parser.add_argument("-u", "--url", help="RabbitMQ URL to connect", required=False, default=None)
    parser.add_argument("-H", "--host", help="RabbitMQ host to connect", required=False, default="localhost")
    parser.add_argument("-p", "--port", help="RabbitMQ port to connect", required=False, default=5672)
    parser.add_argument(
        "-L",
        "--login",
        "-U",
        "--user",
        "--user-name",
        "--username",
        "--user_name",
        dest="login",
        help="RabbitMQ login to connect",
        required=False,
        default="guest",
    )
    parser.add_argument("-P", "--password", help="RabbitMQ password to connect", required=False, default="guest")
    parser.add_argument(
        "-v",
        "--virtualhost",
        "--virtual-host",
        "--virtual_host",
        dest="virtualhost",
        help="RabbitMQ virtual host to connect",
        required=False,
        default="/",
    )

    parser.add_argument("-d", "--debugger", action="store_true", dest="debugger", help="Start only debugger server")
    parser.add_argument(
        "-dh", "--debugger-host", dest="debugger_host", help="Debugger server host", required=False, default="127.0.0.1"
    )
    parser.add_argument(
        "-dp",
        "--debugger-port",
        dest="debugger_port",
        help="Debugger server port",
        type=int,
        required=False,
        default=8000,
    )

    args = parser.parse_args()
    res = vars(args)
    res.pop("debugger", False)
    return res


async def get_inspector() -> ATJointDebugger:
    inspector = GLOBAL.inspector
    if inspector is None:
        args = get_args()
        args.pop("debugger_host", None)
        args.pop("debugger_port", None)
        connection_parameters = ConnectionParameters(**args)
        inspector = ATJointDebugger(websocket_manager=manager, connection_parameters=connection_parameters)
    if not inspector.initialized:
        await inspector.initialize()
    if not inspector.registered:
        await inspector.register()
    GLOBAL.inspector = inspector
    return inspector


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


templates = Jinja2Templates(directory=os.path.join(CURRENT_FILE_PATH.parent, "frontend/build"))


app.mount(
    "/static", StaticFiles(directory=os.path.join(CURRENT_FILE_PATH.parent, "frontend/build/static")), name="static"
)


@app.post("/api/process_tact")
async def process_tact(*, token: str, body: ProcessTactModel):
    inspector = await get_inspector()
    if not inspector.started:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Inspector is not started")
    if not await inspector.check_external_registered("ATJoint"):
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail="ATJoint is not registered")
    if not await inspector.check_external_configured("ATJoint", auth_token=token):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="ATJoint is not configured for provided token")

    data = body.model_dump()
    background = data.pop("background")
    loop = asyncio.get_event_loop()
    task = loop.create_task(inspector.exec_external_method("ATJoint", "process_tact", data, auth_token=token))
    if background:
        await asyncio.sleep(0)
        return {"success": True}
    return await task


@app.get("/api/stop")
async def stop(*, token: str):
    inspector = await get_inspector()
    if not inspector.started:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Inspector is not started")

    if not await inspector.check_external_registered("ATJoint"):
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail="ATJoint is not registered")
    if not await inspector.check_external_configured("ATJoint", auth_token=token):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="ATJoint is not configured for provided token")

    await inspector.exec_external_method("ATJoint", "stop", {}, auth_token=token)
    return {"success": True}


@app.get("/api/reset")
async def reset(*, token: str):
    inspector = await get_inspector()
    if not inspector.started:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Inspector is not started")

    if not await inspector.check_external_registered("ATJoint"):
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail="ATJoint is not registered")

    if not await inspector.check_external_configured("ATJoint", auth_token=token):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="ATJoint is not configured for provided token")

    components = await inspector.exec_external_method("ATJoint", "get_config", {}, auth_token=token)
    for cmp in ["at_temporal_solver", "at_solver"]:
        component = components.get(cmp)
        if not component:
            raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail=f"Component {cmp} is not set up in ATJoint")
        if await inspector.check_external_registered(components[cmp]):
            if await inspector.check_external_configured(components[cmp], auth_token=token):
                await inspector.exec_external_method(component, "reset", {}, auth_token=token)
        if await inspector.check_external_registered("ATJoint"):
            if await inspector.check_external_configured("ATJoint"):
                await inspector.exec_external_method("ATJoint", "reset", {}, auth_token=token)

    return {"success": True}


@app.get("/api/state")
async def state(*, token: str):
    inspector = await get_inspector()
    if not inspector.started:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Inspector is not started")

    result = {
        "at_joint": {},
        "at_solver": {},
        "at_temporal_solver": {},
        "at_simulation": {},
        "at_blackboard": {},
    }

    if not await inspector.check_external_registered("ATJoint"):
        result["at_joint"]["registered"] = False
    else:
        result["at_joint"]["registered"] = True

        if not await inspector.check_external_configured("ATJoint", auth_token=token):
            result["at_joint"]["configured"] = False
        else:
            result["at_joint"]["configured"] = True

            components = await inspector.exec_external_method("ATJoint", "get_config", {}, auth_token=token)
            for cmp in result:
                if cmp in components:
                    result[cmp]["registered"] = await inspector.check_external_registered(components[cmp])
                    if result[cmp]["registered"]:
                        result[cmp]["configured"] = await inspector.check_external_configured(
                            components[cmp], auth_token=token
                        )

    return result


@app.websocket("/api/ws")
async def websocket_endpoint(
    *,
    websocket: WebSocket,
    auth_token: str = Query(...),
):
    session = str(uuid4())
    await manager.connect(auth_token, session, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(auth_token, session)


@app.get("/{path:path}")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


async def main():
    args = get_args()
    inspector = await get_inspector()
    loop = asyncio.get_event_loop()
    inspector_task = None
    if not inspector.started:
        inspector_task = loop.create_task(inspector.start())

    debugger_host = args.get("debugger_host", "127.0.0.1")
    debugger_port = args.get("debugger_port", 8000)

    if not isinstance(debugger_port, int):
        debugger_port = int(debugger_port)

    config = UviConfig(app, debugger_host, debugger_port, loop=loop, ws="websockets")
    server = Server(config=config)
    loop.create_task(server.serve())

    try:
        if not os.path.exists("/var/run/at_joint_debugger/"):
            os.makedirs("/var/run/at_joint_debugger/")

        with open("/var/run/at_joint_debugger/pidfile.pid", "w") as f:
            f.write(str(os.getpid()))
    except PermissionError:
        pass

    if inspector_task is not None:
        await inspector_task


if __name__ == "__main__":
    asyncio.run(main())
