"""The smallest possible test: the package imports (spec §11.1, tier ``unit``)."""

import pytest


@pytest.mark.unit
def test_import_waveyard() -> None:
    import waveyard

    assert waveyard.hello() == "Hello from waveyard!"
