# Компонент для имитации работы подсистемы имитационного моделирования

По сути заглушка, создан для тестирования решателей итд

## Установка

```bash
poetry add git+https://github.com/grigandal625/AT_SIMULATION_MOCKING.git@master
```

## Запуск

Должен быть запущен модуль [at_queue](https://github.com/grigandal625/AT_QUEUE)

```bash
python -m at_simulation_mocking
```

## Параметры запуска

1. **`-u`, `--url`** - URL для подключения к RabbitMQ.
   Значение по умолчанию: `None`

2. **`-H`, `--host`** - Хост для подключения к RabbitMQ.
   Значение по умолчанию: `"localhost"`

3. **`-p`, `--port`** - Порт для подключения к RabbitMQ.
   Значение по умолчанию: `5672`

4. **`-L`, `--login`, `-U`, `--user`, `--user-name`, `--username`, `--user_name`** - Логин для подключения к RabbitMQ.
   Значение по умолчанию: `"guest"`

5. **`-P`, `--password`** - Пароль для подключения к RabbitMQ.
   Значение по умолчанию: `"guest"`

6. **`-v`, `--virtualhost`, `--virtual-host`, `--virtual_host`** - Виртуальный хост для подключения к RabbitMQ.
   Значение по умолчанию: `"/"`


## Пример использования

Общая идея:

1. Запустить компонент.
2. Загрузить готовый прогон имитационной модели в формате json/xml (xml - для старой подсистемы имитационного моделирования на C#)
    - Пример json-прогона - [sm_run.json](tests/fixtures/sm_run.json)
    - Пример xml-прогона - [sm_run.xml](tests/fixtures/sm_run.xml)
3. Запущенный компонент предоставляет метод `run_tick` - почти такой же, как у новой подсистемы имитационного моделирования, который возвращает параметры ресурсов каждый раз для очережного такта прогона при вызове.

Более конкретно:

1. `python -m at_simulation_mocking` + необходимые аргументы

2. Загрузить прогон можно с помощью [конфигуратора](https://github.com/grigandal625/AT_CONFIGURATOR)

Пример файла конфигурации:

```yaml
auth_token: default # или другое значение token
config:
  # ...
  ATSimulationMocking:
    sm_run:
      path: path/to/sm_run.xml
  # ...
```
Нужно сохранить конфигурационный файл, после этого запустить конфигуратор:

```bash
python -m at_configurator -c path/to/config.yaml
```

3. После этого можно пользоваться методом `run_tick` в другом компоненте (с использованием указанного токена), например в средствах совместного функционирования:

```python

class ATJoint(ATComponent):

    # ...

    def process_tact(self, auth_token):

        # получаем параметры ресурсов для очередного такта
        tact = await self.exec_external_method(
            'ATSimulationMocking',
            'run_tick',
            { }, # можно передать любые аргументы
            auth_token=auth_token
        )
        resources = tact.get('resources')

        # передаем их в общую рабочую память и грузим в темпоральный решатель (ATTemporalSolver)
        # вызываем построение интерпретации модели развития событий (наносим интервалы и события на временную шаклу) и расчет темпоральных связок между ними в правилах

        # получаем результат, грузим в общую рабочую память и в АТ-РЕШАТЕЛЬ (ATSolver)
        # запускаем вывод

```
