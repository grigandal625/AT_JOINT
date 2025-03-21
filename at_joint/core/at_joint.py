import asyncio
from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import List
from typing import TypedDict
from typing import Union
from uuid import UUID

from aio_pika import IncomingMessage
from at_config.core.at_config_handler import ATComponentConfig
from at_queue.core.at_component import ATComponent
from at_queue.core.session import ConnectionParameters
from at_queue.utils.decorators import authorized_method


AT_SOLVER = "ATSolver"
AT_TEMPORAL_SOLVER = "ATTemporalSolver"
AT_SIMULATION = "ATSimulation"
AT_BLACKBOARD = "ATBlackBoard"


class ResourceMPDict(TypedDict):
    resource_name: str


class ResourceParameterRequired(TypedDict):
    name: str


class ResourceParameterType(ResourceParameterRequired, total=False):
    parameters: Dict[str, Any]


@dataclass
class ComponentSet:
    at_solver: str
    at_temporal_solver: str
    at_simulation: str
    at_blackboard: str


class ATJoint(ATComponent):
    component_sets: Dict[str, ComponentSet]
    stop_command: Dict[str, Union[bool, None]]
    at_simulation_processes: Dict[str, int | str]
    at_translated_files: Dict[str, str]

    def __init__(self, connection_parameters: ConnectionParameters, *args, **kwargs):
        super().__init__(connection_parameters, *args, **kwargs)
        self.component_sets = {}
        self.stop_command = {}
        self.at_simulation_processes = {}
        self.at_translated_files = {}

    async def perform_configurate(self, config: ATComponentConfig, auth_token: str = None, *args, **kwargs) -> bool:
        at_solver_item = config.items.get("at_solver")
        at_solver = AT_SOLVER
        if at_solver_item is not None:
            at_solver = at_solver_item.data

        at_temporal_solver_item = config.items.get("at_temporal_solver")
        at_temporal_solver = AT_TEMPORAL_SOLVER
        if at_temporal_solver_item is not None:
            at_temporal_solver = at_temporal_solver_item.data

        at_simulation_item = config.items.get("at_simulation")
        at_simulation_file = config.items.get("at_simulation_file")
        at_simulation = AT_SIMULATION
        if at_simulation_item is not None:
            at_simulation = at_simulation_item.data
        if at_simulation_file is None:
            raise ValueError('Expected "at_simulation_file" id provided')

        process = await self.exec_external_method(
            at_simulation,
            "create_process",
            {"process_name": "runtime_process", "file_id": at_simulation_file.data},
            auth_token=auth_token,
        )
        auth_token_or_user_id = await self.get_user_id_or_token(auth_token, raize_on_failed=False)
        self.at_translated_files[auth_token_or_user_id] = at_simulation_file.data

        self.at_simulation_processes[auth_token_or_user_id] = process.get("id")

        at_blackboard_item = config.items.get("at_blackboard")
        at_blackboard = AT_BLACKBOARD
        if at_blackboard_item is not None:
            at_blackboard = at_blackboard_item.data

        return await self.create(
            at_solver=at_solver,
            at_temporal_solver=at_temporal_solver,
            at_simulation=at_simulation,
            at_blackboard=at_blackboard,
            auth_token=auth_token,
        )

    async def check_configured(
        self,
        *args,
        message: Dict,
        sender: str,
        message_id: str | UUID,
        reciever: str,
        msg: IncomingMessage,
        auth_token: str = None,
        **kwargs
    ) -> bool:
        auth_token_or_user_id = await self.get_user_id_or_token(auth_token, raize_on_failed=False)
        return self.has_component_set(auth_token_or_user_id=auth_token_or_user_id)

    async def create(
        self,
        at_solver: str = AT_SOLVER,
        at_temporal_solver: str = AT_TEMPORAL_SOLVER,
        at_simulation: str = AT_SIMULATION,
        at_blackboard: str = AT_BLACKBOARD,
        auth_token: str = None,
    ) -> bool:
        auth_token = auth_token or "default"
        auth_token_or_user_id = await self.get_user_id_or_token(auth_token, raize_on_failed=False)
        component_set = ComponentSet(at_solver, at_temporal_solver, at_simulation, at_blackboard)
        self.component_sets[auth_token_or_user_id] = component_set
        return True

    def get_component_set(self, auth_token_or_user_id):
        auth_token_or_user_id = auth_token_or_user_id or "default"
        component_set = self.component_sets.get(auth_token_or_user_id)
        if component_set is None:
            raise ValueError(
                "Component set (solver, temporal solver, simulation model) for provided token or uer id is not created"
            )
        return component_set

    def get_stop_command(self, auth_token_or_user_id: str | int = None):
        auth_token_or_user_id = auth_token_or_user_id or 'default'
        return self.stop_command.get(auth_token_or_user_id, False)

    def get_at_simulation_process_id(self, auth_token_or_user_id: str = None):
        auth_token_or_user_id = auth_token_or_user_id or 'default'
        return self.at_simulation_processes.get(auth_token_or_user_id)

    def has_component_set(self, auth_token_or_user_id: str = None):
        try:
            self.get_component_set(auth_token_or_user_id)
            return True
        except ValueError:
            return False

    def _items_from_resource_parameters(self, resource_parameters: List[ResourceParameterType]) -> List:
        items = []
        for resource in resource_parameters:
            for param_name, param_value in resource.get("parameters", {}).items():
                items.append({"ref": resource.get("name") + "." + param_name, "value": param_value})
        return items

    def _items_from_solver_result(self, solver_result) -> List:
        return [
            {
                "ref": key,
                "value": wm_item["content"],
                "belief": wm_item.get("non_factor", {}).get("belief"),
                "probability": wm_item.get("non_factor", {}).get("probability"),
                "accuracy": wm_item.get("non_factor", {}).get("accuracy"),
            }
            for key, wm_item in solver_result.get("wm", {}).items()
        ]

    async def process_simulation(self, auth_token: str, auth_token_or_user_id: str | int) -> bool:
        c_set = self.get_component_set(auth_token_or_user_id)
        if await self.check_external_registered(c_set.at_simulation):
            if await self.check_external_configured(c_set.at_simulation, auth_token=auth_token):
                tact = await self.exec_external_method(
                    c_set.at_simulation,
                    "run_tick",
                    {"process_id": self.get_at_simulation_process_id(auth_token)},
                    auth_token=auth_token,
                )
                return tact
        return {"resources": []}

    async def process_temporal_solver(self, auth_token: str, auth_token_or_user_id: str | int) -> bool:
        c_set = self.get_component_set(auth_token_or_user_id)
        if await self.check_external_registered(c_set.at_temporal_solver):
            if await self.check_external_configured(c_set.at_temporal_solver, auth_token=auth_token):
                await self.exec_external_method(
                    c_set.at_temporal_solver, "update_wm_from_bb", {}, auth_token=auth_token
                )

                temporal_result = await self.exec_external_method(
                    c_set.at_temporal_solver, "process_tact", {}, auth_token=auth_token
                )
                return temporal_result
        return {"wm": {}, "timeline": {"tacts": []}, "signified": {}, "signified_meta": {}}

    async def process_solver(self, auth_token: str, auth_token_or_user_id: str | int):
        c_set = self.get_component_set(auth_token_or_user_id)
        if await self.check_external_registered(c_set.at_solver):
            if await self.check_external_configured(c_set.at_solver, auth_token=auth_token):
                await self.exec_external_method(c_set.at_solver, "update_wm_from_bb", {}, auth_token=auth_token)
                solver_result = await self.exec_external_method(c_set.at_solver, "run", {}, auth_token=auth_token)
                return solver_result
        return {"wm": {}, "trace": {"steps": []}}

    async def debug(self, initiator: str, data: dict, auth_token: str):
        if await self.check_external_registered("ATJointDebugger"):
            await self.exec_external_method(
                "ATJointDebugger", "debug", {"data": {"initiator": initiator, "data": data}}, auth_token=auth_token
            )

    @authorized_method
    async def reset(self, auth_token: str = None):
        auth_token = auth_token or "default"
        auth_token_or_user_id = await self.get_user_id_or_token(auth_token, raize_on_failed=False)
        process_id = self.get_at_simulation_process_id(auth_token_or_user_id)
        c_set = self.get_component_set(auth_token_or_user_id)
        await self.exec_external_method(
            c_set.at_simulation, "kill_process", {"process_id": process_id}, auth_token=auth_token
        )
        file_id = self.at_translated_files.get(auth_token_or_user_id)
        process = await self.exec_external_method(
            c_set.at_simulation,
            "create_process",
            {"process_name": "runtime_process", "file_id": file_id},
            auth_token=auth_token,
        )
        self.at_simulation_processes[auth_token_or_user_id] = process.get("id")
        return True

    @authorized_method
    async def stop(self, auth_token_or_user_id: str = None):
        auth_token_or_user_id = auth_token_or_user_id or "default"
        self.stop_command[auth_token_or_user_id] = True

    async def run_solvers(self, items, c_set: ComponentSet, auth_token: str, auth_token_or_user_id: str | int):
        await self.exec_external_method(c_set.at_blackboard, "set_items", {"items": items}, auth_token=auth_token)

        temporal_result = await self.process_temporal_solver(auth_token=auth_token, auth_token_or_user_id=auth_token_or_user_id)
        await self.debug("at_temporal_solver", temporal_result, auth_token)
        temporal_items = [{"ref": key, "value": value} for key, value in temporal_result.get("signified", {}).items()]
        await self.exec_external_method(
            c_set.at_blackboard, "set_items", {"items": temporal_items}, auth_token=auth_token
        )

        solver_result = await self.process_solver(auth_token, auth_token_or_user_id=auth_token_or_user_id)
        await self.debug("at_solver", solver_result, auth_token)
        solver_items = self._items_from_solver_result(solver_result)

        await self.exec_external_method(
            c_set.at_blackboard, "set_items", {"items": solver_items}, auth_token=auth_token
        )

        return {"at_temporal_solver": temporal_result, "at_solver": solver_result}

    @authorized_method
    async def process_tact(self, iterate: int = 1, wait: int = 1000, auth_token: str = None):
        loop = asyncio.get_event_loop()

        result = []
        auth_token = auth_token or "default"
        auth_token_or_user_id = await self.get_user_id_or_token(auth_token, raize_on_failed=False)
        self.stop_command[auth_token_or_user_id] = False
        c_set = self.get_component_set(auth_token_or_user_id)

        solvers_task = loop.create_future()
        solvers_task.set_result(None)
        previous_resource_parameters = None

        for tact in range(iterate):
            if self.get_stop_command(auth_token_or_user_id):
                break

            tact_data = await self.process_simulation(auth_token=auth_token, auth_token_or_user_id=auth_token_or_user_id)
            resources: List[ResourceMPDict] = tact_data.get("resources", [])

            resource_parameters: List[ResourceParameterType] = [
                {
                    "name": resource["resource_name"],
                    "parameters": {key: value for key, value in resource.items() if key != "resource_name"},
                }
                for resource in resources
            ]
            await self.debug("at_simulation", resource_parameters, auth_token)
            items = self._items_from_resource_parameters(resource_parameters)

            await solvers_task

            if solvers_task.result() is not None:
                result.append(
                    {
                        "tact": tact,
                        "at_simulation": previous_resource_parameters,
                        **solvers_task.result(),
                        # 'at_temporal_solver': temporal_result,
                        # 'at_solver': solver_result
                    }
                )

            previous_resource_parameters = resource_parameters

            solvers_task = loop.create_task(self.run_solvers(items, c_set, auth_token=auth_token, auth_token_or_user_id=auth_token_or_user_id))

            if iterate > 1:
                await asyncio.sleep(wait / 1000)

        await solvers_task
        result.append(
            {
                "tact": tact,
                "at_simulation": previous_resource_parameters,
                **solvers_task.result(),
                # 'at_temporal_solver': temporal_result,
                # 'at_solver': solver_result
            }
        )

        await self.debug("at_joint", {"stop": True}, auth_token)
        return result

    @authorized_method
    async def get_config(self, auth_token: str) -> dict:
        auth_token_or_user_id = await self.get_user_id_or_token(auth_token, raize_on_failed=False)
        c_set = self.get_component_set(auth_token_or_user_id=auth_token_or_user_id)
        return c_set.__dict__
