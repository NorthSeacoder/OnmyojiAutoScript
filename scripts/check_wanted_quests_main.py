#!/usr/bin/env python3
"""Check whether a main-account config can run WantedQuests after cooperation accept."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from module.config.config_manual import ConfigManual


DEFAULT_CONFIG = Path("config/oas_main.json")
DEFAULT_PRIORITY = "WantedQuests"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def filter_contains_wanted_quests(data: dict) -> bool:
    schedule_rule = data.get("script", {}).get("optimization", {}).get("schedule_rule")
    if schedule_rule != "Filter":
        return True
    return DEFAULT_PRIORITY.lower() in ConfigManual.SCHEDULER_PRIORITY.lower()


def ensure_wanted_quests(data: dict, fix: bool) -> list[str]:
    messages = []
    wanted_quests = data.setdefault("wanted_quests", {})
    scheduler = wanted_quests.setdefault("scheduler", {})

    if scheduler.get("enable") is True:
        messages.append("OK wanted_quests.scheduler.enable=true")
    elif fix:
        scheduler["enable"] = True
        messages.append("FIX wanted_quests.scheduler.enable=true")
    else:
        messages.append("FAIL wanted_quests.scheduler.enable is not true")

    if scheduler.get("next_run"):
        messages.append(f"OK wanted_quests.scheduler.next_run={scheduler['next_run']}")
    elif fix:
        scheduler["next_run"] = "2023-01-01 00:00:00"
        messages.append("FIX wanted_quests.scheduler.next_run=2023-01-01 00:00:00")
    else:
        messages.append("FAIL wanted_quests.scheduler.next_run is missing")

    scheduler.setdefault("priority", 5)
    scheduler.setdefault("success_interval", "01 00:00:00")
    scheduler.setdefault("failure_interval", "01 00:00:00")
    scheduler.setdefault("server_update", "09:00:00")
    scheduler.setdefault("delay_date", 1)
    scheduler.setdefault("float_time", "00:00:00")

    if filter_contains_wanted_quests(data):
        messages.append("OK schedule rule will not exclude WantedQuests")
    else:
        messages.append("WARN schedule_rule=Filter may exclude WantedQuests")

    return messages


def main() -> int:
    parser = argparse.ArgumentParser(
        description="检查大号配置是否允许接受协作后调度 WantedQuests。"
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="配置文件路径，默认 config/oas_main.json")
    parser.add_argument("--fix", action="store_true", help="显式修正缺失或未启用的 wanted_quests.scheduler")
    args = parser.parse_args()

    path = Path(args.config)
    data = load_json(path)
    messages = ensure_wanted_quests(data, fix=args.fix)
    if args.fix:
        save_json(path, data)

    print(f"checked {path}")
    for message in messages:
        print(message)

    has_failure = any(message.startswith("FAIL") for message in messages)
    return 1 if has_failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
