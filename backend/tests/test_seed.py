import json

import pytest

from app.seed import load_seed


def test_seed_file_is_valid():
    records = load_seed()
    assert len(records) >= 10


def test_invalid_seed_record_stops_the_seed(tmp_path):
    bad = json.loads(open("data/opportunities.json", encoding="utf-8").read())
    bad[0]["work_mode"] = "on the moon"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(SystemExit, match="programme-assistant-ngo-berlin"):
        load_seed(path)
