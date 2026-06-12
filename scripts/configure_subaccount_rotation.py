#!/usr/bin/env python3
"""Configure SubAccountRotation for a script config."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path


DEFAULT_CONFIG = Path("config/oas_findjade.json")
DEFAULT_TIME = "2023-01-01 00:00:00"
KNOWN_SUB_TASKS = {
    "LoginOnly",
    "Orochi",
    "FindJade",
    "MysteryShop",
    "DailyTriflesStoreSign",
    "Hunt",
    "TalismanPass",
    "Exploration",
    "AreaBoss",
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def scheduler(enable: bool, existing: dict | None = None, run_now: bool = False) -> dict:
    value = deepcopy(existing or {})
    value["enable"] = enable
    if run_now:
        value["next_run"] = DEFAULT_TIME
    else:
        value.setdefault("next_run", DEFAULT_TIME)
    value.setdefault("priority", 5)
    value.setdefault("success_interval", "01 00:00:00")
    value.setdefault("failure_interval", "01 00:00:00")
    value.setdefault("server_update", "09:00:00")
    value.setdefault("delay_date", 1)
    value.setdefault("float_time", "00:00:00")
    return value


def normalize_sub_tasks(values: list[str]) -> str:
    result = []
    for value in values:
        for item in value.replace("，", ",").split(","):
            name = item.strip()
            if not name:
                continue
            if name not in KNOWN_SUB_TASKS:
                raise argparse.ArgumentTypeError(
                    f"未知子任务 {name}; 可选: {', '.join(sorted(KNOWN_SUB_TASKS))}"
                )
            if name not in result:
                result.append(name)
    return ",".join(result or ["LoginOnly"])


def disable_find_jade_scheduler(data: dict) -> bool:
    scheduler_data = data.get("find_jade", {}).get("scheduler")
    if not isinstance(scheduler_data, dict):
        return False
    scheduler_data["enable"] = False
    return True


def configure_orochi(data: dict, main_friend: str, limit_count: int | None = None) -> None:
    orochi = data.setdefault("orochi", {})
    orochi_config = orochi.setdefault("orochi_config", {})
    invite_config = orochi.setdefault("invite_config", {})
    orochi_config["user_status"] = "leader"
    if limit_count is not None:
        orochi_config["limit_count"] = limit_count
    invite_config["friend_1"] = main_friend


def configure_exploration(
        data: dict,
        main_friend: str,
        minions_count: int | None = None,
        limit_time: str | None = None,
) -> None:
    exploration = data.setdefault("exploration", {})
    exploration_config = exploration.setdefault("exploration_config", {})
    invite_config = exploration.setdefault("invite_config", {})
    scrolls = exploration.setdefault("scrolls", {})
    exploration_config["user_status"] = "leader"
    exploration_config["exploration_level"] = "第二十八章"
    if minions_count is not None:
        exploration_config["minions_cnt"] = minions_count
    if limit_time is not None:
        exploration_config["limit_time"] = limit_time
    invite_config["friend_1"] = main_friend
    scrolls["scrolls_enable"] = False


def disable_harvest(data: dict) -> None:
    restart = data.setdefault("restart", {})
    harvest_config = restart.setdefault("harvest_config", {})
    harvest_config["enable"] = False
    harvest_config["enable_courtyard_affairs"] = False


def enable_harvest(data: dict) -> None:
    restart = data.setdefault("restart", {})
    harvest_config = restart.setdefault("harvest_config", {})
    harvest_config["enable"] = True
    harvest_config["enable_courtyard_affairs"] = True


def main() -> int:
    parser = argparse.ArgumentParser(description="初始化或更新 SubAccountRotation 小号轮换配置。")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="配置文件路径，默认 config/oas_findjade.json")
    parser.add_argument("--enable", action="store_true", help="启用 SubAccountRotation 调度器")
    parser.add_argument("--run-now", action="store_true", help="把 SubAccountRotation.next_run 重置为过去时间，便于立即验证")
    parser.add_argument(
        "--sub-task",
        action="append",
        default=[],
        help="启用子任务，可重复传或逗号分隔；默认 LoginOnly",
    )
    parser.add_argument("--account-interval", default="00 13:00:00", help="每账号/子任务间隔，默认 13 小时")
    parser.add_argument("--max-accounts-per-run", type=int, default=0, help="每轮最多处理账号数，0 表示不限制")
    parser.add_argument(
        "--disable-find-jade",
        action="store_true",
        help="同时关闭 FindJade 调度器，用于隔离验证 SubAccountRotation，避免旧 FindJade 继续执行。",
    )
    parser.add_argument(
        "--configure-orochi",
        action="store_true",
        help="把御魂配置为小号队长并设置邀请大号；不启用 Orochi 独立调度器。",
    )
    parser.add_argument("--main-friend", default="不知庭院", help="御魂/组队邀请的大号昵称，默认 不知庭院")
    parser.add_argument("--orochi-limit-count", type=int, default=None, help="可选：设置御魂次数，建议实机验证先设小值")
    parser.add_argument(
        "--configure-exploration",
        action="store_true",
        help="把探索配置为小号队长、困难28、邀请大号，并关闭探索内绘卷/突破票联动；不启用 Exploration 独立调度器。",
    )
    parser.add_argument("--exploration-minions-count", type=int, default=None, help="可选：设置探索战斗次数，建议实机验证先设小值")
    parser.add_argument("--exploration-limit-time", default=None, help="可选：设置探索限时，例如 00:05:00")
    parser.add_argument(
        "--disable-harvest",
        action="store_true",
        help="临时关闭登录收取和庭院事务，仅用于隔离验证子任务；正常使用不建议开启。",
    )
    parser.add_argument(
        "--enable-harvest",
        action="store_true",
        help="恢复登录收取和庭院事务，用于隔离验证后回到正常配置。",
    )
    args = parser.parse_args()

    if args.disable_harvest and args.enable_harvest:
        parser.error("--disable-harvest 和 --enable-harvest 不能同时使用")

    path = Path(args.config)
    data = load_json(path)
    existing = deepcopy(data.get("sub_account_rotation", {}))
    sub_tasks = normalize_sub_tasks(args.sub_task)
    data["sub_account_rotation"] = {
        "scheduler": scheduler(args.enable, existing.get("scheduler", {}), run_now=args.run_now),
        "sub_account_rotation_config": {
            "account_source": "find_jade",
            "enabled_sub_tasks": sub_tasks,
            "account_interval": args.account_interval,
            "continue_on_switch_failure": True,
            "max_accounts_per_run": args.max_accounts_per_run,
        },
    }

    for key, value in existing.items():
        if key.startswith("history_list_"):
            data["sub_account_rotation"][key] = value

    find_jade_disabled = False
    if args.disable_find_jade:
        find_jade_disabled = disable_find_jade_scheduler(data)
    if args.configure_orochi:
        configure_orochi(data, args.main_friend, args.orochi_limit_count)
    if args.configure_exploration:
        configure_exploration(
            data,
            args.main_friend,
            minions_count=args.exploration_minions_count,
            limit_time=args.exploration_limit_time,
        )
    if args.disable_harvest:
        disable_harvest(data)
    if args.enable_harvest:
        enable_harvest(data)

    save_json(path, data)
    print(f"updated {path}")
    print(f"enable: {args.enable}")
    print(f"run_now: {args.run_now}")
    print(f"sub_tasks: {sub_tasks}")
    if args.disable_find_jade:
        print(f"find_jade disabled: {find_jade_disabled}")
    if args.configure_orochi:
        print(f"orochi leader friend_1: {args.main_friend}")
        if args.orochi_limit_count is not None:
            print(f"orochi limit_count: {args.orochi_limit_count}")
    if args.configure_exploration:
        print(f"exploration leader friend_1: {args.main_friend}")
        print("exploration level: 第二十八章")
        print("exploration scrolls disabled: True")
        if args.exploration_minions_count is not None:
            print(f"exploration minions_cnt: {args.exploration_minions_count}")
        if args.exploration_limit_time is not None:
            print(f"exploration limit_time: {args.exploration_limit_time}")
    if args.disable_harvest:
        print("harvest disabled: True")
    if args.enable_harvest:
        print("harvest enabled: True")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
