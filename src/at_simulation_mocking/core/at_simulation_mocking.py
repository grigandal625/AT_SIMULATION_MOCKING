from uuid import UUID
from aio_pika import IncomingMessage
from at_config.core.at_config_handler import ATComponentConfig
from at_queue.core.at_component import ATComponent
from at_queue.core.session import ConnectionParameters
from at_queue.utils.decorators import authorized_method
from at_simulation_mocking.core.at_rao_structs import SMRun, TactsDict, ResourceMPDict
from typing import Dict, Union, List
import logging
import json
from xml.etree.ElementTree import fromstring, Element

logger = logging.getLogger(__name__)


class SM_LOAD_MODE:
    JSON = 'json'
    AT4_XML = 'at4_xml'


class ATSimulationMocking(ATComponent):
    sm_runs: Dict[str, SMRun]
    last_tacts: Dict[str, int]

    def __init__(self, connection_parameters: ConnectionParameters, *args, **kwargs):
        super().__init__(connection_parameters, *args, **kwargs)
        self.sm_runs = {}
        self.last_tacts = {}

    async def perform_configurate(self, config: ATComponentConfig, auth_token: str = None, *args, **kwargs) -> bool:
        auth_token = auth_token or 'default'
        sm_run_config = config.items.get('sm_run')
        sm_run = sm_run_config.data
        mode = SM_LOAD_MODE.AT4_XML if isinstance(sm_run, Element) else SM_LOAD_MODE.JSON
        return self.create_sm_run(sm_run, mode=mode, auth_token=auth_token)

    def create_sm_run(self, sm_run: Union[TactsDict, str, Element], mode: str = None, auth_token: str = None) -> bool:
        auth_token = auth_token or 'default'
        
        if mode == SM_LOAD_MODE.AT4_XML:
            if isinstance(sm_run, dict):
                raise ValueError('sm_run must be xml element or str but got dict')
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
    
    async def check_configured(self, *args, message: Dict, sender: str, message_id: str | UUID, reciever: str, msg: IncomingMessage, auth_token: str = None, **kwargs) -> bool:
        try:
            self.get_sm_run(auth_token)
            return True
        except ValueError:
            return False

    def get_sm_run(self, auth_token) -> SMRun:
        auth_token = auth_token or 'default'
        sm_run = self.sm_runs.get(auth_token)
        if sm_run is None:
            raise ValueError("Simulation model run for token '%s' is not created" % auth_token)
        return sm_run
    
    def get_last_tact(self, auth_token) -> int:
        auth_token = auth_token or 'default'
        last_tact = self.last_tacts.get(auth_token)
        if last_tact is None:
            last_tact = -1
            self.last_tacts[auth_token] = last_tact
        return last_tact
    
    @authorized_method
    def reset(self, auth_token: str = None) -> bool:
        auth_token = auth_token or 'default'
        self.last_tacts[auth_token] = 0

    @authorized_method
    def process_tact(self, recycle: bool = True, auth_token: str = None, ) -> List[ResourceMPDict]:
        sm_run = self.get_sm_run(auth_token)
        new_tact = self.get_last_tact(auth_token) + 1
        if new_tact > sm_run.max_tact:
            if not recycle:
                raise ValueError(f'Trying to process tact {new_tact} but max tact is {sm_run.max_tact}')
        
        sm_tact = new_tact % (sm_run.max_tact + 1)
        self.last_tacts[auth_token] = new_tact
        return sm_run.__dict__["tacts"][sm_tact]

    