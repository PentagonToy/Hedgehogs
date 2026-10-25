"""Keep load and image-comparison checks explicitly opt-in."""
import pytest


def pytest_addoption(parser):
    parser.addoption('--run-load', action='store_true', help='Run explicitly requested load tests.')
    parser.addoption('--load-report', default=None, help='Write load measurements to this JSON file.')
    parser.addoption('--run-visual', action='store_true', help='Compare reference figures in the matching render environment.')
    parser.addoption('--visual-baseline-dir', default=None, help='Parent of environment-specific visual reference directories.')


def pytest_collection_modifyitems(config, items):
    for marker, option in [('load', '--run-load'), ('visual', '--run-visual')]:
        if config.getoption(option):
            continue
        skip = pytest.mark.skip(reason=f'{marker.capitalize()} tests require explicit {option}.')
        for item in items:
            if item.get_closest_marker(marker) is not None:
                item.add_marker(skip)
