import click
from click.testing import CliRunner
from mock import patch

from pdtools import __main__ as main


def test_help():
    runner = CliRunner()
    result = runner.invoke(main.root, ["help"], obj={})
    assert result.exit_code == 0
