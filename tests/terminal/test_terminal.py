from io import StringIO

import pytest

import hedgehogs as hdg


def test_echo_is_plain_when_redirected():
    output = StringIO()
    hdg.echo("complete", tone="success", file=output)
    assert output.getvalue() == "complete\n"


def test_echo_rejects_unknown_tone():
    with pytest.raises(ValueError, match="Unknown tone"):
        hdg.echo("message", tone="unknown")


def test_rule_uses_requested_width():
    output = StringIO()
    hdg.rule("Results", width=24, file=output)
    assert len(output.getvalue().rstrip("\n")) == 24
