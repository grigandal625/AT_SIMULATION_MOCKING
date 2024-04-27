from at_queue.core.at_component import ATComponent
from at_queue.core.session import ConnectionParameters
from at_queue.utils.decorators import authorized_method
from at_simulation_mocking.core.at_rao_structs import SMRun, TactsDict, ResourceMPDict
from typing import Dict, Union, List
import logging
import json
from xml.etree.ElementTree import fromstring

logger = logging.getLogger(__name__)


class ATSimulationMocking(ATComponent):
    sm_runs: Dict[str, SMRun]
    last_tacts: Dict[str, int]

    def __init__(self, connection_parameters: ConnectionParameters, *args, **kwargs):
        super().__init__(connection_parameters, *args, **kwargs)
        self.sm_runs = {}
        self.last_tacts = {}

    @authorized_method
    def create_sm(self, sm: Union[TactsDict, str], from_at4_xml_if_str: bool = True, auth_token: str = None) -> bool:
        auth_token = auth_token or 'default'
        if isinstance(sm, str):
            if from_at4_xml_if_str:
                parsed = fromstring(sm)
                sm_run_instance = SMRun.from_at4_xml(parsed)
            else:
                parsed = json.loads(sm)
                sm_run_instance = SMRun.from_tacts_dict(parsed)
        else:
            sm_run_instance = SMRun.from_tacts_dict(sm)
        self.sm_runs[auth_token] = sm_run_instance
        return True
    
    @authorized_method
    def has_sm(self, auth_token: str = None) -> bool:
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
    def reset_tact(self, auth_token: str = None) -> bool:
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

    