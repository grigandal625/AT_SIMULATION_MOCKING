import json
from xml.etree.ElementTree import fromstring

from at_queue.core.session import ConnectionParameters
from pytest import fixture

from at_simulation_mocking.core.at_simulation_mocking import ATSimulationMocking


@fixture
def json_sm_run():
    return json.loads(open("./tests/fixtures/sm_run.json").read())


@fixture
def xml_sm_run():
    return fromstring(open("./tests/fixtures/sm_run.xml").read())


async def test_load_and_run_from_xml(xml_sm_run):
    mocking = ATSimulationMocking(connection_parameters=ConnectionParameters())
    await mocking.create_sm_run(xml_sm_run, mode="at4_xml")

    processes = mocking.get_processes(auth_token="default")
    assert isinstance(processes, list)
    assert not len(processes)
    process = mocking.create_process(auth_token="default")
    assert "id" in process

    process_id = process["id"]
    processes = mocking.get_processes(auth_token="default")
    assert isinstance(processes, list)
    assert len(processes) == 1
    assert processes[0]["id"] == process_id
    assert processes[0]["status"] == "PAUSE"

    tick = mocking.run_tick(auth_token="default", process_id=process_id)
    assert isinstance(tick, dict)
    assert "resources" in tick

    tick = mocking.run_tick(auth_token="default", process_id=process_id)
    assert isinstance(tick, dict)
    assert "resources" in tick

    process = mocking.kill_process(process_id=process_id, auth_token="default")
    assert isinstance(process, dict)
    assert "id" in process
    assert process["id"] == process_id
    assert process["status"] == "KILLED"


async def test_load_and_run_from_json(json_sm_run):
    mocking = ATSimulationMocking(connection_parameters=ConnectionParameters())
    mocking.create_sm_run(json_sm_run, mode="json")

    processes = mocking.get_processes(auth_token="default")
    assert isinstance(processes, list)
    assert not len(processes)
    process = mocking.create_process(auth_token="default")
    assert "id" in process

    process_id = process["id"]
    processes = mocking.get_processes(auth_token="default")
    assert isinstance(processes, list)
    assert len(processes) == 1
    assert processes[0]["id"] == process_id
    assert processes[0]["status"] == "PAUSE"

    tick = mocking.run_tick(auth_token="default", process_id=process_id)
    assert isinstance(tick, dict)
    assert "resources" in tick

    tick = mocking.run_tick(auth_token="default", process_id=process_id)
    assert isinstance(tick, dict)
    assert "resources" in tick

    process = mocking.kill_process(process_id=process_id, auth_token="default")
    assert isinstance(process, dict)
    assert "id" in process
    assert process["id"] == process_id
    assert process["status"] == "KILLED"
