import json
import logging
from datetime import datetime
from typing import Dict
from typing import List
from typing import Literal
from typing import TypedDict
from typing import Union
from uuid import UUID
from uuid import uuid4
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import fromstring

from aio_pika import IncomingMessage
from at_config.core.at_config_handler import ATComponentConfig
from at_queue.core.at_component import ATComponent
from at_queue.core.session import ConnectionParameters
from at_queue.utils.decorators import authorized_method

from at_simulation_mocking.core.at_rao_structs import ResourceMPDict
from at_simulation_mocking.core.at_rao_structs import SMRun
from at_simulation_mocking.core.at_rao_structs import TactDict

logger = logging.getLogger(__name__)


class ProcessDict(TypedDict):
    id: str
    name: str
    file_id: str
    status: Literal["PAUSE", "RUNNING", "KILLED"]
    current_tick: int


class TranslatedFileDict(TypedDict):
    id: str
    name: str
    model_id: int
    created_at: datetime
    size: int
    model_name: str


class SM_LOAD_MODE:
    JSON = "json"
    AT4_XML = "at4_xml"


class ATSimulationMocking(ATComponent):
    sm_runs: Dict[str, SMRun]
    process_mockings: Dict[str, List[ProcessDict]]
    translated_files: List[TranslatedFileDict]

    def __init__(self, connection_parameters: ConnectionParameters, *args, **kwargs):
        super().__init__(connection_parameters, *args, **kwargs)
        self.sm_runs = {}
        self.process_mockings = {}
        self.translated_files = [
            {
                "id": str(uuid4()),
                "name": "File 1",
                "model_id": 1,
                "created_at": datetime.now(),
                "size": 1024,
                "model_name": "Unknown",
            }
        ]

    async def perform_configurate(self, config: ATComponentConfig, auth_token: str = None, *args, **kwargs) -> bool:
        auth_token = auth_token or "default"
        sm_run_config = config.items.get("sm_run")
        sm_run = sm_run_config.data
        if isinstance(sm_run, str):
            at4_xml = config.items.get("at4_xml")
            if at4_xml is not None and at4_xml.data:
                sm_run = fromstring(sm_run)
            else:
                sm_run = json.loads(sm_run)
        mode = SM_LOAD_MODE.AT4_XML if isinstance(sm_run, Element) else SM_LOAD_MODE.JSON
        return self.create_sm_run(sm_run, mode=mode, auth_token=auth_token)

    def create_sm_run(self, sm_run: Union[TactDict, str, Element], mode: str = None, auth_token: str = None) -> bool:
        auth_token = auth_token or "default"

        if mode == SM_LOAD_MODE.AT4_XML:
            if isinstance(sm_run, dict):
                raise ValueError("sm_run must be xml element or str but got dict")
            parsed = sm_run
            if isinstance(sm_run, str):
                parsed = fromstring(sm_run)
            sm_run_instance = SMRun.from_at4_xml(parsed)
        else:
            parsed = sm_run
            if isinstance(sm_run, str):
                parsed = json.loads(sm_run)
            sm_run_instance = SMRun.from_tacts_dict(parsed)

        self.sm_runs[auth_token] = sm_run_instance
        return True

    async def check_configured(
        self,
        *args,
        message: Dict,
        sender: str,
        message_id: str | UUID,
        reciever: str,
        msg: IncomingMessage,
        auth_token: str = None,
        **kwargs,
    ) -> bool:
        try:
            self.get_sm_run(auth_token)
            return True
        except ValueError:
            return False

    def get_sm_run(self, auth_token) -> SMRun:
        auth_token = auth_token or "default"
        sm_run = self.sm_runs.get(auth_token)
        if sm_run is None:
            raise ValueError("Simulation model run for token '%s' is not created" % auth_token)
        return sm_run

    def get_process_mocking(self, auth_token, process_id) -> ProcessDict:
        auth_token = auth_token or "default"
        process_mockings = self.process_mockings.get(auth_token, [])
        process_mocking = next(iter([p for p in process_mockings if p["id"] == process_id]), None)
        if process_mocking is None:
            raise ValueError(f"No processes created for provided token with id {process_id}")
        return process_mocking

    @authorized_method
    def get_translated_files(self, auth_token: str = None) -> List[TranslatedFileDict]:
        return self.translated_files

    @authorized_method
    def create_process(self, auth_token: str = None, **kwargs) -> ProcessDict:
        auth_token = auth_token or "default"
        processes = self.process_mockings.get(auth_token, [])
        processes.append(
            {
                "id": str(uuid4()),
                "name": kwargs.get("process_name") or "process_name",
                "file_id": kwargs.get("file_id") or str(uuid4()),
                "status": "PAUSE",
                "current_tick": 0,
            }
        )
        self.process_mockings[auth_token] = processes
        return processes[-1]

    @authorized_method
    def kill_process(self, process_id: str, auth_token: str = None, **kwargs) -> None:
        auth_token = auth_token or "default"
        process = self.get_process_mocking(auth_token, process_id)
        process["status"] = "KILLED"
        return process

    @authorized_method
    def run_tick(self, process_id: str, recycle: bool = True, auth_token: str = None, **kwargs) -> List[ResourceMPDict]:
        sm_run = self.get_sm_run(auth_token)
        process = self.get_process_mocking(auth_token, process_id)
        if process["status"] == "KILLED":
            raise ValueError("Can not run tick of killed process")
        current_tact = process["current_tick"]
        new_tact = current_tact + 1
        if new_tact > sm_run.max_tact:
            if not recycle:
                raise ValueError(f"Trying to process tact {new_tact} but max tact is {sm_run.max_tact}")

        sm_tact = new_tact % (sm_run.max_tact + 1)
        process["current_tick"] = new_tact
        return sm_run.__dict__[sm_tact]

    @authorized_method
    def get_processes(self, auth_token: str = None, **kwargs) -> List[ProcessDict]:
        auth_token = auth_token or "default"
        return self.process_mockings.get(auth_token, [])
