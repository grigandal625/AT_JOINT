from at_queue.core.at_component import ATComponent
from at_queue.core.session import ConnectionParameters
from typing import TYPE_CHECKING
import json

from at_queue.utils.decorators import authorized_method


if TYPE_CHECKING:
    from at_joint.debug.server import ConnectionManager

class ATJointDebugger(ATComponent):

    websocket_manager: 'ConnectionManager'

    def __init__(self, connection_parameters: ConnectionParameters, websocket_manager: 'ConnectionManager', *args, **kwargs):
        super().__init__(connection_parameters, *args, **kwargs)
        self.websocket_manager = websocket_manager

    @authorized_method
    async def debug(self, data: dict, auth_token: str = None):
        await self.websocket_manager.send_message(auth_token, json.dumps(data))
        return True
    
    async def inspect(self, component):
        return await self.session.send_await(
            'registry',
            {
                'type': 'inspect',
                'component': component
            }
        )

