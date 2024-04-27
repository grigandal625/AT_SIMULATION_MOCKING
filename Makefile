help:
	@echo "Tasks in \033[1;32mdemo\033[0m:"
	@cat Makefile

lint:
	mypy src --ignore-missing-imports
	flake8 src --ignore=$(shell cat .flakeignore)

dev:
	pipenv run python setup.py develop

test: dev
	pytest

clean:
	@rm -rf .pytest_cache/ .mypy_cache/ junit/ build/ dist/
	
build: clean
	pip install wheel
	python setup.py bdist_wheel
stable:
	cp dist/at_simulation_mocker-*.*-py3-none-any.whl dist/at_simulation_mocker-stable-py3-none-any.whl
latest:
	cp dist/at_simulation_mocker-*.*-py3-none-any.whl dist/at_simulation_mocker-latest-py3-none-any.whl
requirements:
	pip freeze > requirements.txt
# sed -i 1d requirements.txt
rabbit:
	docker run --rm -p 15672:15672 -p 5672:5672 rabbitmq:management