import argparse
from at_queue.core.session import ConnectionParameters
from at_simulation_mocking.core.at_simulation_mocking import ATSimulationMocking
import asyncio
import logging

parser = argparse.ArgumentParser(
    prog='at-temporal-solver',
    description='General working memory for AT-TECHNOLOGY components')

parser.add_argument('-u', '--url', help="RabbitMQ URL to connect", required=False, default=None)
parser.add_argument('-H', '--host', help="RabbitMQ host to connect", required=False, default="localhost")
parser.add_argument('-p', '--port', help="RabbitMQ port to connect", required=False, default=5672)
parser.add_argument('-L', '--login', '-U', '--user', '--user-name', '--username', '--user_name', dest="login", help="RabbitMQ login to connect", required=False, default="guest")
parser.add_argument('-P', '--password', help="RabbitMQ password to connect", required=False, default="guest")
parser.add_argument('-v',  '--virtualhost', '--virtual-host', '--virtual_host', dest="virtualhost", help="RabbitMQ virtual host to connect", required=False, default="/")


async def main(**connection_kwargs):
    connection_parameters = ConnectionParameters(**connection_kwargs)
    mocker = ATSimulationMocking(connection_parameters=connection_parameters)
    await mocker.initialize()
    await mocker.register()
    await mocker.start()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    args = parser.parse_args()
    args_dict = vars(args)

    asyncio.run(main(**args_dict))