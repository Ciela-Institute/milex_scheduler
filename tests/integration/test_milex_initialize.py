from argparse import Namespace
from unittest.mock import patch
from milex_scheduler.apps.milex_initialize import main
import pytest
import os


@pytest.fixture
def mock_parse_known_args():
    with patch("argparse.ArgumentParser.parse_args") as mock_parse_known_args:
        mock_parse_known_args.return_value = Namespace(bundle="bundle_name")
        yield mock_parse_known_args


@pytest.fixture
def mock_load_config(tmp_path):
    mock_config = {"local": {"path": tmp_path}}
    os.makedirs(tmp_path / "jobs", exist_ok=True)
    with patch(
        "milex_scheduler.save_load_jobs.load_config", return_value=mock_config
    ) as mock_load_config:
        yield mock_load_config


def test_main(mock_parse_known_args, mock_load_config):
    main()
