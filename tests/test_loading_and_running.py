import json
from xml.etree.ElementTree import fromstring

import pytest
from at_queue.core.session import ConnectionParameters
from pytest import fixture

from at_simulation_mocking.core.at_simulation_mocking import ATSimulationMocking

pytest_plugins = ("pytest_asyncio",)


@fixture
def json_sm_run():
    return json.loads(open("./tests/fixtures/sm_run.json").read())


@fixture
def xml_sm_run():
    return fromstring(open("./tests/fixtures/sm_run.xml").read())


@pytest.mark.asyncio
async def test_load_and_run_from_xml(xml_sm_run):
    mocking = ATSimulationMocking(connection_parameters=ConnectionParameters())
    await mocking.create_sm_run(xml_sm_run, mode="at4_xml")

    processes = await mocking.get_processes(auth_token="default")
    assert isinstance(processes, list)
    assert not len(processes)
    process = await mocking.create_process(auth_token="default")
    assert "id" in process

    process_id = process["id"]
    processes = await mocking.get_processes(auth_token="default")
    assert isinstance(processes, list)
    assert len(processes) == 1
    assert processes[0]["id"] == process_id
    assert processes[0]["status"] == "PAUSE"

    tick = await mocking.run_tick(auth_token="default", process_id=process_id)
    assert isinstance(tick, dict)
    assert "resources" in tick

    tick = await mocking.run_tick(auth_token="default", process_id=process_id)
    assert isinstance(tick, dict)
    assert "resources" in tick

    process = await mocking.kill_process(process_id=process_id, auth_token="default")
    assert isinstance(process, dict)
    assert "id" in process
    assert process["id"] == process_id
    assert process["status"] == "KILLED"


@pytest.mark.asyncio
async def test_load_and_run_from_json(json_sm_run):
    mocking = ATSimulationMocking(connection_parameters=ConnectionParameters())
    await mocking.create_sm_run(json_sm_run, mode="json")

    processes = await mocking.get_processes(auth_token="default")
    assert isinstance(processes, list)
    assert not len(processes)
    process = await mocking.create_process(auth_token="default")
    assert "id" in process

    process_id = process["id"]
    processes = await mocking.get_processes(auth_token="default")
    assert isinstance(processes, list)
    assert len(processes) == 1
    assert processes[0]["id"] == process_id
    assert processes[0]["status"] == "PAUSE"

    tick = await mocking.run_tick(auth_token="default", process_id=process_id)
    assert isinstance(tick, dict)
    assert "resources" in tick

    tick = await mocking.run_tick(auth_token="default", process_id=process_id)
    assert isinstance(tick, dict)
    assert "resources" in tick

    process = await mocking.kill_process(process_id=process_id, auth_token="default")
    assert isinstance(process, dict)
    assert "id" in process
    assert process["id"] == process_id
    assert process["status"] == "KILLED"
