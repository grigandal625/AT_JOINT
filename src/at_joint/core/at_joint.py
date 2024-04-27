from at_queue.core.at_component import ATComponent
from at_queue.core.session import ConnectionParameters
from at_queue.utils.decorators import authorized_method
from dataclasses import dataclass
from typing import Dict, Union

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

    def __init__(self, connection_parameters: ConnectionParameters, *args, **kwargs):
        super().__init__(connection_parameters, *args, **kwargs)
        self.component_sets = {}

    @authorized_method
    async def create(
        self, 
        kb: dict,
        sm: Union[str, dict],
        at_solver: str = AT_SOLVER, 
        at_temporal_solver: str = AT_TEMPORAL_SOLVER,
        at_simulation: str = AT_SIMULATION,
        at_blackboard: str = AT_BLACKBOARD,
        auth_token: str = None
    ):
        auth_token = auth_token or 'default'
        component_set = ComponentSet(at_solver, at_temporal_solver, at_simulation, at_blackboard)
        await self.exec_external_method(
            at_solver,
            'create_solver',
            {'kb': kb},
            auth_token
        )
        await self.exec_external_method(
            at_temporal_solver,
            'create_temporal_solver',
            {'kb': kb},
            auth_token
        )
        await self.exec_external_method(
            at_simulation,
            'create_sm',
            {'sm': sm},
            auth_token
        )
        await self.exec_external_method(
            at_blackboard,
            'get_all_items',
            {},
            auth_token
        )
        self.component_sets[auth_token] = component_set

    def get_component_set(self, auth_token):
        auth_token = auth_token or 'default'
        component_set = self.component_sets.get(auth_token)
        if component_set is None:
            raise ValueError("Component set (solver, temporal solver, simulation model) for token '%s' is not created" % auth_token)
        return component_set
    
    @authorized_method
    def has_component_set(self, auth_token: str = None):
        try:
            self.get_component_set(auth_token)
            return True
        except ValueError:
            return False
        
    @authorized_method
    async def process_tact(self, auth_token: str = None):
        c_set = self.get_component_set(auth_token)
        resource_parameters = await self.exec_external_method(
            c_set.at_simulation,
            'process_tact',
            {},
            auth_token=auth_token
        )
        items = []
        for resource in resource_parameters:
            for param_name, param_value in resource.get('parameters', {}).items():
                items.append({
                    'ref': resource.get('name') + '.' + param_name,
                    'value': param_value
                })

        await self.exec_external_method(
            c_set.at_blackboard,
            'set_items',
            {'items': items},
            auth_token=auth_token
        )

        all_items = await self.exec_external_method(
            c_set.at_blackboard,
            'get_all_items',
            {},
            auth_token
        )

        await self.exec_external_method(
            c_set.at_temporal_solver,
            'update_wm',
            {'items': all_items },
            auth_token=auth_token
        )

        temporal_result = await self.exec_external_method(
            c_set.at_temporal_solver,
            'process_tact',
            {},
            auth_token=auth_token
        )

        temporal_items = [{'ref': key, 'value': value} 
                          for key, value in temporal_result.get('signified', {}).items()]
        
        await self.exec_external_method(
            c_set.at_blackboard,
            'set_items',
            {'items': temporal_items},
            auth_token=auth_token
        )

        all_items = await self.exec_external_method(
            c_set.at_blackboard,
            'get_all_items',
            {},
            auth_token
        )

        await self.exec_external_method(
            c_set.at_solver,
            'update_wm',
            {'items': all_items },
            auth_token=auth_token
        )

        solver_result = await self.exec_external_method(
            c_set.at_solver,
            'run',
            {},
            auth_token=auth_token
        )

        solver_items = [
            {
                'ref': key, 
                'value': wm_item['content'], 
                'belief': wm_item.get('non_factor', {}).get('belief'),
                'probability': wm_item.get('non_factor', {}).get('probability'),
                'accuracy': wm_item.get('non_factor', {}).get('accuracy'),
            }
            for key, wm_item in solver_result.get('wm', {}).items()
        ]

        await self.exec_external_method(
            c_set.at_blackboard,
            'set_items',
            {'items': solver_items},
            auth_token=auth_token
        )


