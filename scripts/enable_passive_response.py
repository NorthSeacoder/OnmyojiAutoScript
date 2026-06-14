#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PassiveCooperationResponse 配置启用脚本

用法:
  python3 scripts/enable_passive_response.py <config_name> [--enable-orochi] [--buff] [--test]

示例:
  # 启用大号被动响应（御魂，开启加成）
  python3 scripts/enable_passive_response.py oas1 --enable-orochi --buff

  # 仅测试配置是否存在
  python3 scripts/enable_passive_response.py oas1 --test
"""

import sys
import json
from pathlib import Path
from datetime import datetime


def load_config(config_name):
    """加载配置文件"""
    config_path = Path("config") / f"{config_name}.json"
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return None

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(config_name, data):
    """保存配置文件"""
    config_path = Path("config") / f"{config_name}.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Config saved: {config_path}")


def ensure_passive_config_exists(data):
    """确保 passive_cooperation_response 配置存在"""
    if 'passive_cooperation_response' not in data:
        print("⚠️  Creating passive_cooperation_response config block...")
        data['passive_cooperation_response'] = {
            "scheduler": {
                "enable": False,
                "priority": 999,
                "success_interval": 86400,
                "failure_interval": 600,
                "next_run": "2023-01-01 00:00:00"
            },
            "passive_config": {
                "orochi": {
                    "enable": False,
                    "max_accept_count": -1,
                    "allowed_inviters": [],
                    "buff_enable": False
                },
                "exploration": {
                    "enable": False,
                    "max_accept_count": -1,
                    "allowed_inviters": [],
                    "buff_enable": False
                },
                "wanted_quests": {
                    "enable": False,
                    "max_accept_count": -1,
                    "allowed_inviters": [],
                    "allowed_cooperation_types": ["jade", "cat_food", "dog_food"]
                }
            }
        }
        return True
    return False


def enable_passive_response(config_name, enable_orochi=False, buff_enable=False, test_only=False):
    """启用被动响应配置"""
    print(f"{'='*60}")
    print(f"PassiveCooperationResponse Configuration Tool")
    print(f"{'='*60}")
    print(f"Config: {config_name}")
    print(f"Mode: {'TEST' if test_only else 'ENABLE'}")
    print(f"{'='*60}\n")

    # 加载配置
    data = load_config(config_name)
    if data is None:
        return False

    # 确保配置块存在
    created = ensure_passive_config_exists(data)
    if created:
        print("✅ Created new passive_cooperation_response config block")

    # 获取配置引用
    pcr = data['passive_cooperation_response']

    # 测试模式：仅显示当前状态
    if test_only:
        print("\n📊 Current Configuration:")
        print(f"  scheduler.enable: {pcr['scheduler']['enable']}")
        print(f"  scheduler.next_run: {pcr['scheduler']['next_run']}")
        print(f"  passive_config.orochi.enable: {pcr['passive_config']['orochi']['enable']}")
        print(f"  passive_config.orochi.buff_enable: {pcr['passive_config']['orochi']['buff_enable']}")
        print(f"  passive_config.orochi.max_accept_count: {pcr['passive_config']['orochi']['max_accept_count']}")
        print(f"  passive_config.orochi.allowed_inviters: {pcr['passive_config']['orochi']['allowed_inviters']}")
        return True

    # 修改配置
    changes = []

    # 启用 scheduler
    if not pcr['scheduler']['enable']:
        pcr['scheduler']['enable'] = True
        pcr['scheduler']['next_run'] = "2023-01-01 00:00:00"
        changes.append("✅ Enabled scheduler")

    # 启用御魂被动响应
    if enable_orochi:
        if not pcr['passive_config']['orochi']['enable']:
            pcr['passive_config']['orochi']['enable'] = True
            changes.append("✅ Enabled orochi passive response")

        if buff_enable and not pcr['passive_config']['orochi']['buff_enable']:
            pcr['passive_config']['orochi']['buff_enable'] = True
            changes.append("✅ Enabled orochi buff auto-management")

    # 显示变更
    if changes:
        print("\n📝 Configuration Changes:")
        for change in changes:
            print(f"  {change}")

        # 保存配置
        save_config(config_name, data)

        print("\n✅ Configuration updated successfully!")
        print("\n📋 Final Configuration:")
        print(f"  scheduler.enable: {pcr['scheduler']['enable']}")
        print(f"  passive_config.orochi.enable: {pcr['passive_config']['orochi']['enable']}")
        print(f"  passive_config.orochi.buff_enable: {pcr['passive_config']['orochi']['buff_enable']}")
    else:
        print("\n✅ Configuration already correct, no changes needed.")

    return True


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    config_name = sys.argv[1]
    enable_orochi = '--enable-orochi' in sys.argv
    buff_enable = '--buff' in sys.argv
    test_only = '--test' in sys.argv

    success = enable_passive_response(config_name, enable_orochi, buff_enable, test_only)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
