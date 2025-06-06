import argparse
import asyncio
import logging
import os

from at_queue.core.session import ConnectionParameters

from at_joint.core.at_joint import ATJoint
from at_joint.debug.server import main as debugger_main

parser = argparse.ArgumentParser(
    prog="at-joint", description="Joint functioning component for AT_SIMULATION, AT_TEMPORAL_SOLVER and at_joint"
)

parser.add_argument("-u", "--url", help="RabbitMQ URL to connect", required=False, default=None)
parser.add_argument("-H", "--host", help="RabbitMQ host to connect", required=False, default="localhost")
parser.add_argument("-p", "--port", help="RabbitMQ port to connect", required=False, type=int, default=5672)
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


parser.add_argument("-d", "--debugger-only", action="store_true", dest="debugger_only", help="Start only debugger server")
parser.add_argument("-nd", "--no-debugger", action="store_true", dest="no_debugger", help="Start only debugger server")
parser.add_argument(
    "-dh", "--debugger-host", dest="debugger_host", help="Debugger server host", required=False, default="127.0.0.1"
)
parser.add_argument(
    "-dp", "--debugger-port", dest="debugger_port", help="Debugger server port", type=int, required=False, default=8000
)


async def main(no_debugger=False, **connection_kwargs):
    connection_parameters = ConnectionParameters(**connection_kwargs)
    joint = ATJoint(connection_parameters=connection_parameters)
    await joint.initialize()
    await joint.register()

    try:
        if not os.path.exists("/var/run/at_joint/"):
            os.makedirs("/var/run/at_joint/")

        with open("/var/run/at_joint/pidfile.pid", "w") as f:
            f.write(str(os.getpid()))
    except PermissionError:
        pass
    
    loop = asyncio.get_event_loop()
    task = loop.create_task(joint.start())
    if not no_debugger:
        await debugger_main()
    await task


if __name__ == "__main__":
    args = parser.parse_args()
    args_dict = vars(args)

    if args_dict.pop("debugger_only", False):
        asyncio.run(debugger_main())
    else:
        logging.basicConfig(level=logging.INFO)
        asyncio.run(main(**args_dict))
