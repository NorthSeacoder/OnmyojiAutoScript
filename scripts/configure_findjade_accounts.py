#!/usr/bin/env python3
"""Configure FindJade small-account settings for oas_findjade."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path


DEFAULT_CONFIG = Path("config/oas_findjade.json")
DEFAULT_SERVER = "月蚀长夜"
DEFAULT_MAIN = "不知庭院"
DEFAULT_ACCOUNTS = [
    {"character": "最后的黄泉", "account": "bmkfh1992@126.com"},
    {"character": "破晓的森林", "account": "CRfalling"},
]
DEFAULT_TIME = "2023-01-01 00:00:00"


def account_item(character: str, account: str, server: str, alias: str = "", android: bool = True) -> dict:
    return {
        "character": character,
        "svr": server,
        "account": account,
        "account_alias": alias,
        "apple_or_android": android,
        "last_complete_time": DEFAULT_TIME,
    }


def invite_item(main_name: str) -> dict:
    return {
        "name": main_name,
        "default_invite_type": "JadeAndFood",
        "invite_history_1": DEFAULT_TIME,
        "invite_history_2": DEFAULT_TIME,
        "invite_history_4": DEFAULT_TIME,
        "invite_history_8": DEFAULT_TIME,
    }


def parse_account(value: str) -> dict:
    parts = value.split(":")
    if len(parts) not in (2, 3):
        raise argparse.ArgumentTypeError("账号格式应为 昵称:账号 或 昵称:账号:OCR别名")
    character, account = parts[0].strip(), parts[1].strip()
    alias = parts[2].strip() if len(parts) == 3 else ""
    if not character or not account:
        raise argparse.ArgumentTypeError("昵称和账号不能为空")
    return {"character": character, "account": account, "account_alias": alias}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def build_find_jade(existing: dict, server: str, main_name: str, accounts: list[dict]) -> dict:
    find_jade = deepcopy(existing.get("find_jade", {}))
    scheduler = deepcopy(find_jade.get("scheduler", {}))
    scheduler["enable"] = True
    scheduler["next_run"] = DEFAULT_TIME
    scheduler.setdefault("priority", 5)
    scheduler.setdefault("success_interval", "01 00:00:00")
    scheduler.setdefault("failure_interval", "01 00:00:00")
    scheduler["server_update"] = "09:00:00"
    scheduler.setdefault("delay_date", 1)
    scheduler.setdefault("float_time", "00:00:00")

    new_find_jade = {
        "scheduler": scheduler,
        "find_jade_config": {
            "invite_info_count": 1,
            "sup_account_count": len(accounts),
        },
        "invite_info_list_1": invite_item(main_name),
    }

    for index, raw in enumerate(accounts, start=1):
        new_find_jade[f"sup_account_list_{index}"] = account_item(
            character=raw["character"],
            account=raw["account"],
            server=server,
            alias=raw.get("account_alias", ""),
            android=raw.get("apple_or_android", True),
        )

    return new_find_jade


def main() -> int:
    parser = argparse.ArgumentParser(
        description="更新 config/oas_findjade.json 的 FindJade 小号列表配置。"
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="配置文件路径，默认 config/oas_findjade.json")
    parser.add_argument("--server", default=DEFAULT_SERVER, help=f"小号所在服务器，默认 {DEFAULT_SERVER}")
    parser.add_argument("--main", default=DEFAULT_MAIN, help=f"被邀请的大号昵称，默认 {DEFAULT_MAIN}")
    parser.add_argument(
        "--add",
        action="append",
        type=parse_account,
        default=[],
        metavar="昵称:账号[:OCR别名]",
        help="追加一个小号；可重复传。未传时写入脚本内置的两个小号。",
    )
    parser.add_argument(
        "--replace-defaults",
        action="store_true",
        help="只使用 --add 提供的小号，不包含脚本内置的两个默认小号。",
    )
    args = parser.parse_args()

    path = Path(args.config)
    data = load_json(path)
    data.setdefault("script", {}).setdefault("optimization", {})["schedule_rule"] = "FIFO"
    accounts = [] if args.replace_defaults else deepcopy(DEFAULT_ACCOUNTS)
    accounts.extend(args.add)
    if not accounts:
        parser.error("至少需要一个小号")

    data["find_jade"] = build_find_jade(data, args.server, args.main, accounts)
    save_json(path, data)

    print(f"updated {path}")
    print(f"server: {args.server}")
    print(f"main invitee: {args.main}")
    print(f"small accounts: {len(accounts)}")
    for index, item in enumerate(accounts, start=1):
        print(f"  {index}. {item['character']} / {item['account']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
