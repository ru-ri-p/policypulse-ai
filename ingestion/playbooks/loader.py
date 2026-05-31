# ingestion/playbooks/loader.py
from functools import lru_cache
from pathlib import Path

import yaml

PLAYBOOKS_DIR = Path(__file__).parent


@lru_cache(maxsize=1)
def load_playbooks_config() -> dict:
    path = PLAYBOOKS_DIR / "gcc_playbooks.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def load_exposure_packs() -> dict:
    path = PLAYBOOKS_DIR / "exposure_packs.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_playbooks() -> list[dict]:
    return load_playbooks_config().get("playbooks", [])


def get_playbook(playbook_id: str) -> dict | None:
    for pb in get_playbooks():
        if pb["id"] == playbook_id:
            return pb
    return None


def get_exposure_pack(pack_id: str) -> dict | None:
    packs = load_exposure_packs()
    if pack_id not in packs:
        return None
    data = packs[pack_id]
    return {"id": pack_id, **data}


def list_exposure_pack_ids() -> list[str]:
    return list(load_exposure_packs().keys())
