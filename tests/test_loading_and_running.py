from pytest import fixture
from at_simulation_mocking.core.at_simulation_mocking import ATSimulationMocking
import json
from at_queue.core.session import ConnectionParameters
from xml.etree.ElementTree import fromstring


@fixture
def json_sm_run():
    return json.loads(open('./tests/fixtures/sm_run.json').read())


@fixture
def xml_sm_run():
    return fromstring(open('./tests/fixtures/sm_run.xml').read())


def test_load_and_run_from_xml(xml_sm_run):
    mocking = ATSimulationMocking(connection_parameters=ConnectionParameters())
    mocking.create_sm_run(xml_sm_run, mode='at4_xml')
    tick = mocking.run_tick(auth_token='default', process_id='test-proc-id')
    assert 'resources' in tick
    


def test_load_and_run_from_json(json_sm_run):
    mocking = ATSimulationMocking(connection_parameters=ConnectionParameters())
    mocking.create_sm_run(json_sm_run, mode='json')
    tick = mocking.run_tick(auth_token='default', process_id='test-proc-id')
    assert 'resources' in tick