"""Keep expensive load checks explicitly opt-in."""
import pytest


def pytest_addoption(parser):
    parser.addoption('--run-load', action='store_true', help='Run explicitly requested load tests.')
    parser.addoption('--load-report', default=None, help='Write load measurements to this JSON file.')


def pytest_collection_modifyitems(config, items):
    if config.getoption('--run-load'):
        return
    skip = pytest.mark.skip(reason='Load tests require explicit --run-load.')
    for item in items:
        if 'load' in item.keywords:
            item.add_marker(skip)
