from at_queue.core.at_registry import ATRegistryInspector
from at_queue.core.session import ConnectionParameters, ConnectionKwargs
import argparse
from fastapi import FastAPI, WebSocket, Query, Cookie, WebSocketException, status, HTTPException, Depends
from uvicorn import Config, Server
import asyncio
from typing import Annotated, Union
from uuid import uuid3, NAMESPACE_OID


QUEUE_NAME = 'at-joint-debugger-' + str(uuid3(NAMESPACE_OID, 'at-joint-debugger'))


class GLOBAL:
    inspector: ATRegistryInspector = None


def get_args() -> dict:
    parser = argparse.ArgumentParser(
        prog='at-joint-debugger',
        description='Debugging server for joint functioning component for AT_SIMULATION, AT_TEMPORAL_SOLVER and AT_SOLVER')

    parser.add_argument('-u', '--url', help="RabbitMQ URL to connect", required=False, default=None)
    parser.add_argument('-H', '--host', help="RabbitMQ host to connect", required=False, default="localhost")
    parser.add_argument('-p', '--port', help="RabbitMQ port to connect", required=False, default=5672)
    parser.add_argument('-L', '--login', '-U', '--user', '--user-name', '--username', '--user_name', dest="login", help="RabbitMQ login to connect", required=False, default="guest")
    parser.add_argument('-P', '--password', help="RabbitMQ password to connect", required=False, default="guest")
    parser.add_argument('-v',  '--virtualhost', '--virtual-host', '--virtual_host', dest="virtualhost", help="RabbitMQ virtual host to connect", required=False, default="/")

    parser.add_argument('-dh', '--debugger-host', dest="debugger_host", help="Debugger server host", required=False, default="127.0.0.1")
    parser.add_argument('-dp', '--debugger-host', dest="debugger_port", help="Debugger server port", type=int, required=False, default=8000)

    args = parser.parse_args()
    return vars(args)


async def get_inspector() -> ATRegistryInspector:
    inspector = GLOBAL.inspector
    if inspector is None:
        args = get_args()
        args.pop('debugger_host', None)
        args.pop('debugger_port', None)
        connection_parameters = ConnectionParameters(**args)
        inspector = ATRegistryInspector(connection_parameters=connection_parameters)
    if not inspector.initialized:
        await inspector.initialize()
    if not inspector.registered:
        await inspector.register()
    GLOBAL.inspector = inspector
    return inspector


app = FastAPI()


@app.get('/api/process_tact')
async def process_tact(*, token: str):
    inspector = await get_inspector()
    if not inspector.started:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Inspector is not started")
    if not await inspector.check_external_registered('ATJoint'):
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail='ATJoint is not registered')
    if not await inspector.check_external_configured('ATJoint', auth_token=token):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail='ATJoint is not configured for provided token')
    result = await inspector.exec_external_method('ATJoint', 'process_tact', {}, auth_token=token)
    return result


@app.get('/api/state')
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

    if not await inspector.check_external_registered('ATJoint'):
        result['at_joint']['registered'] = False

    else:
        result['at_joint']['registered'] = True

        if not await inspector.check_external_configured('ATJoint', auth_token=token):
            result['at_joint']['configured'] = False
        else:
            result['at_joint']['configured'] = True

            components = await inspector.exec_external_method('ATJoint', 'get_config', {}, auth_token=token)
            for cmp in result:
                if cmp in components:
                    result[cmp]['registered'] = await inspector.check_external_registered(components[cmp])
                    if result[cmp]['registered']:
                        result[cmp]['configured'] = await inspector.check_external_configured(components[cmp], auth_token=token)

    return result


async def get_cookie_or_token(
    websocket: WebSocket,
    session: Annotated[Union[str, None], Cookie()] = None,
    token: Annotated[Union[str, None], Query()] = None,
):
    if session is None and token is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    return session or token


@app.websocket("/api/ws")
async def websocket_endpoint(
    *,
    websocket: WebSocket,
    cookie_or_token: Annotated[str, Depends(get_cookie_or_token)],
):
    await websocket.accept()
    inspector = await get_inspector()
    if not inspector.started:
        raise WebSocketException(status=status.WS_1013_TRY_AGAIN_LATER, reason="Inspector is not started")
    args = get_args()
    args.pop('debugger_host', None)
    args.pop('debugger_port', None)
    connection_parameters = ConnectionParameters(**args)

    connection = await connection_parameters.connect_robust()
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(QUEUE_NAME)
        async for message in queue:
            if message.headers.get('auth_token') == cookie_or_token:
                await message.ack()
                data = message.body.decode('utf-8')
                await websocket.send_text(data)


async def main():
    args = get_args()
    inspector = await get_inspector()
    loop = asyncio.get_event_loop()
    inspector_task = None
    if not inspector.started:
        inspector_task = loop.create_task(inspector.start)
    
    debugger_host = args.get('debugger_host', '127.0.0.1')
    debugger_port = args.get('debugger_port', 8000)

    if not isinstance(debugger_port, int):
        debugger_port = int(debugger_port)

    config = Config(app, host=debugger_host, port=debugger_port, loop=loop)
    server = Server(config)
    await server.serve()
    await inspector_task


if __name__ == '__main__':
    asyncio.run(main())