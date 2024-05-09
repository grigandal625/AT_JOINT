import argparse
from at_queue.core.session import ConnectionParameters
from at_joint.core.at_joint import ATJoint
from at_joint.debug.server import main as debugger_main
import asyncio
import logging

parser = argparse.ArgumentParser(
    prog='at-joint',
    description='Joint functioning component for AT_SIMULATION, AT_TEMPORAL_SOLVER and AT_SOLVER')

parser.add_argument('-u', '--url', help="RabbitMQ URL to connect", required=False, default=None)
parser.add_argument('-H', '--host', help="RabbitMQ host to connect", required=False, default="localhost")
parser.add_argument('-p', '--port', help="RabbitMQ port to connect", required=False, default=5672)
parser.add_argument('-L', '--login', '-U', '--user', '--user-name', '--username', '--user_name', dest="login", help="RabbitMQ login to connect", required=False, default="guest")
parser.add_argument('-P', '--password', help="RabbitMQ password to connect", required=False, default="guest")
parser.add_argument('-v',  '--virtualhost', '--virtual-host', '--virtual_host', dest="virtualhost", help="RabbitMQ virtual host to connect", required=False, default="/")


parser.add_argument('-d', '--debugger', action='store_true', dest="debugger", help="Start only debugger server")
parser.add_argument('-dh', '--debugger-host', dest="debugger_host", help="Debugger server host", required=False, default="127.0.0.1")
parser.add_argument('-dp', '--debugger-port', dest="debugger_port", help="Debugger server port", type=int, required=False, default=8000)

async def main(**connection_kwargs):
    connection_parameters = ConnectionParameters(**connection_kwargs)
    joint = ATJoint(connection_parameters=connection_parameters)
    await joint.initialize()
    await joint.register()
    await joint.start()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    args = parser.parse_args()
    args_dict = vars(args)

    if args_dict.pop('debugger', False):
        asyncio.run(debugger_main())
    else:
        asyncio.run(main(**args_dict))
