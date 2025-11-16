import json
from pathlib import Path

from src.utils.smartctl_wrapper import SmartctlWrapper


def load_json(name: str):
    return json.loads(Path(__file__).parent.joinpath('fixtures', name).read_text(encoding='utf-8'))


def test_parse_nvme_smart():
    wrapper = SmartctlWrapper()
    data = load_json('nvme_smart.json')
    out = wrapper._parse_smart_json(data)
    assert out['device_type'] == 'nvme'
    assert out['temperature'] == 46
    assert out['power_on_hours'] == 1234
    # 100000 units * 512000 bytes ≈ 51.2 GB
    assert out['read_bytes'] == 100000 * 512000
    assert out['write_bytes'] == 250000 * 512000
    assert 0 <= out['health_percentage'] <= 100


def test_parse_sata_smart():
    wrapper = SmartctlWrapper()
    data = load_json('sata_smart.json')
    out = wrapper._parse_smart_json(data)
    assert out['device_type'] == 'ata'
    assert out['temperature'] == 35
    assert out['power_on_hours'] == 8765
    # 241/242 en unidades de 32MiB
    assert out['write_bytes'] == 12000 * 32 * 1024 * 1024
    assert out['read_bytes'] == 8000 * 32 * 1024 * 1024


def test_parse_hdd_smart_minimal():
    wrapper = SmartctlWrapper()
    data = load_json('hdd_smart.json')
    out = wrapper._parse_smart_json(data)
    assert out['device_type'] == 'ata'
    assert out['temperature'] == 29
    assert out['power_on_hours'] == 22000
    # HDD puede no reportar 241/242
    assert out['read_bytes'] is None or out['read_bytes'] >= 0
    assert out['write_bytes'] is None or out['write_bytes'] >= 0


