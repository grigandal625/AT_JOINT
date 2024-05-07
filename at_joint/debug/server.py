from at_queue.core.at_registry import ATRegistryInspector
from at_queue.core.session import ConnectionParameters, ConnectionKwargs
import argparse
from fastapi import FastAPI
from uvicorn import Config, Server
import asyncio

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