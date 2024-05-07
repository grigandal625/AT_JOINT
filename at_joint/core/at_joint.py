from uuid import UUID
from aio_pika import IncomingMessage
from at_config.core.at_config_handler import ATComponentConfig
from at_queue.core.at_component import ATComponent
from at_queue.core.session import ConnectionParameters
from at_queue.utils.decorators import authorized_method
from dataclasses import dataclass
from typing import Dict, Union, List
from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractQueue
from aio_pika import Message
from at_joint.debug.server import QUEUE_NAME
import json

AT_SOLVER = 'ATSolver'
AT_TEMPORAL_SOLVER = 'ATTemporalSolver'
AT_SIMULATION = 'ATSimulation'
AT_BLACKBOARD = 'ATBlackboard'


@dataclass
class ComponentSet:
    at_solver: str
    at_temporal_solver: str
    at_simulation: str
    at_blackboard: str


class ATJoint(ATComponent):
    component_sets: Dict[str, ComponentSet]
    debug_connection: AbstractConnection
    debug_channel: AbstractChannel
    debug_queue: AbstractQueue

    def __init__(self, connection_parameters: ConnectionParameters, *args, **kwargs):
        super().__init__(connection_parameters, *args, **kwargs)
        self.component_sets = {}

    async def initialize(self):
        res = await super().initialize()
        self.debug_connection = await self.register_session.connection_parameters.connect_robust()
        self.debug_channel = await self.debug_connection.channel()
        self.debug_queue = await self.debug_channel.declare_queue(QUEUE_NAME)
        return res

    async def perform_configurate(self, config: ATComponentConfig, auth_token: str = None, *args, **kwargs) -> bool:
        at_solver_item = config.items.get('at_solver')
        at_solver = AT_SOLVER
        if at_solver_item is not None:
            at_solver = at_solver_item.data

        at_temporal_solver_item = config.items.get('at_temporal_solver')
        at_temporal_solver = AT_TEMPORAL_SOLVER
        if at_temporal_solver_item is not None:
            at_temporal_solver = at_temporal_solver_item.data

        at_simulation_item = config.items.get('at_simulation')
        at_simulation = AT_SIMULATION
        if at_simulation_item is not None:
            at_simulation = at_simulation_item.data

        at_blackboard_item = config.items.get('at_blackboard')
        at_blackboard = AT_BLACKBOARD
        if at_blackboard_item is not None:
            at_blackboard = at_blackboard_item.data

        return self.create(
            at_solver=at_solver, 
            at_temporal_solver=at_temporal_solver, 
            at_simulation=at_simulation, 
            at_blackboard=at_blackboard, 
            auth_token=auth_token
        ) 
    
    async def check_configured(self, *args, message: Dict, sender: str, message_id: str | UUID, reciever: str, msg: IncomingMessage, auth_token: str = None, **kwargs) -> bool:
        return self.has_component_set(auth_token=auth_token)

    def create(
        self,
        at_solver: str = AT_SOLVER, 
        at_temporal_solver: str = AT_TEMPORAL_SOLVER,
        at_simulation: str = AT_SIMULATION,
        at_blackboard: str = AT_BLACKBOARD,
        auth_token: str = None
    ) -> bool:
        auth_token = auth_token or 'default'
        component_set = ComponentSet(at_solver, at_temporal_solver, at_simulation, at_blackboard)
        self.component_sets[auth_token] = component_set
        return True

    def get_component_set(self, auth_token):
        auth_token = auth_token or 'default'
        component_set = self.component_sets.get(auth_token)
        if component_set is None:
            raise ValueError("Component set (solver, temporal solver, simulation model) for token '%s' is not created" % auth_token)
        return component_set
    
    def has_component_set(self, auth_token: str = None):
        try:
            self.get_component_set(auth_token)
            return True
        except ValueError:
            return False
        
    def _items_from_resource_parameters(self, resource_parameters: List) -> List:
        items = []
        for resource in resource_parameters:
            for param_name, param_value in resource.get('parameters', {}).items():
                items.append({
                    'ref': resource.get('name') + '.' + param_name,
                    'value': param_value
                })
        return items

    def _items_from_solver_result(self, solver_result) -> List:
        return [
            {
                'ref': key, 
                'value': wm_item['content'], 
                'belief': wm_item.get('non_factor', {}).get('belief'),
                'probability': wm_item.get('non_factor', {}).get('probability'),
                'accuracy': wm_item.get('non_factor', {}).get('accuracy'),
            }
            for key, wm_item in solver_result.get('wm', {}).items()
        ]

    async def process_simulation(self, auth_token: str) -> bool:
        c_set = self.get_component_set(auth_token)
        if await self.check_external_registered(c_set.at_simulation):
            if await self.check_external_configured(c_set.at_simulation, auth_token=auth_token):
                resource_parameters = await self.exec_external_method(
                    c_set.at_simulation,
                    'process_tact',
                    {},
                    auth_token=auth_token
                )
                return resource_parameters
        return []
    
    async def process_temporal_solver(self, auth_token: str) -> bool:
        c_set = self.get_component_set(auth_token)
        if await self.check_external_registered(c_set.at_temporal_solver):
            if await self.check_external_configured(c_set.at_temporal_solver, auth_token=auth_token):
                await self.exec_external_method(
                    c_set.at_temporal_solver,
                    'update_wm_from_bb',
                    {},
                    auth_token=auth_token
                )

                temporal_result = await self.exec_external_method(
                    c_set.at_temporal_solver,
                    'process_tact',
                    {},
                    auth_token=auth_token
                )
                return temporal_result
        return {'wm': {}, 'timeline': {'tacts': []}, 'signified': {}}

    async def process_solver(self, auth_token: str):
        if await self.check_external_registered(c_set.at_solver):
            if await self.check_external_configured(c_set.at_solver, auth_token=auth_token):
                c_set = self.get_component_set(auth_token)
                await self.exec_external_method(
                    c_set.at_solver,
                    'update_wm_from_bb',
                    {},
                    auth_token=auth_token
                )

                solver_result = await self.exec_external_method(
                    c_set.at_solver,
                    'run',
                    {},
                    auth_token=auth_token
                )
                return solver_result
        return {'wm': {}, 'trace': {'steps': []}}
        
    async def debug(self, initiator: str, data: dict, auth_token: str):
        msg_data = {
            'initiator': initiator,
            'data': data
        }
        await self.debug_channel.default_exchange.publish(
            Message(
                json.dumps(msg_data, ensure_ascii=False).encode(),
                headers={'auth_token': auth_token}
            ),
            routing_key=QUEUE_NAME
        )
    
    @authorized_method
    async def process_tact(self, auth_token: str = None):
        
        c_set = self.get_component_set(auth_token)
        resource_parameters = await self.process_simulation(auth_token=auth_token)
        await self.debug('at_simulation', resource_parameters, auth_token)
        items = self._items_from_resource_parameters(resource_parameters)

        await self.exec_external_method(
            c_set.at_blackboard,
            'set_items',
            {'items': items},
            auth_token=auth_token
        )

        temporal_result = await self.process_temporal_solver(auth_token=auth_token)
        await self.debug('at_temporal_solver', temporal_result, auth_token)
        temporal_items = [{'ref': key, 'value': value} 
                          for key, value in temporal_result.get('signified', {}).items()]
        await self.exec_external_method(
            c_set.at_blackboard,
            'set_items',
            {'items': temporal_items},
            auth_token=auth_token
        )

        solver_result = await self.process_solver(auth_token)
        await self.debug('at_solver', solver_result, auth_token)
        solver_items = self._items_from_solver_result(solver_result)

        await self.exec_external_method(
            c_set.at_blackboard,
            'set_items',
            {'items': solver_items},
            auth_token=auth_token
        )
