#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T1.6 单元测试：邀请验证逻辑

测试场景：
1. 基础验证：enable/disable
2. 次数限制：max_accept_count = -1/0/n
3. 白名单：空列表/非空列表/匹配/不匹配
4. 协作类型：wanted_quests 特有的 allowed_cooperation_types
"""

from datetime import datetime
from typing import List


class MockInviteInfo:
    """模拟 InviteInfo 数据类"""
    def __init__(self, task_type, inviter_name, cooperation_type=None):
        self.task_type = task_type
        self.inviter_name = inviter_name
        self.cooperation_type = cooperation_type
        self.detected_at = datetime.now()


class MockTaskConfig:
    """模拟 PassiveTaskConfig"""
    def __init__(self, enable=False, max_accept_count=-1, allowed_inviters=None):
        self.enable = enable
        self.max_accept_count = max_accept_count
        self.allowed_inviters = allowed_inviters or []


class MockCooperationConfig(MockTaskConfig):
    """模拟 PassiveCooperationConfig"""
    def __init__(self, enable=False, max_accept_count=-1, allowed_inviters=None, allowed_cooperation_types=None):
        super().__init__(enable, max_accept_count, allowed_inviters)
        self.allowed_cooperation_types = allowed_cooperation_types or ["jade", "cat_food", "dog_food"]


def should_accept_invite(invite, task_cfg, current_count=0):
    """
    模拟 _should_accept_invite 验证逻辑

    检查：
    1. 任务类型是否启用
    2. 接受次数是否超限
    3. 邀请者是否在白名单
    4. 协作类型过滤（仅 wanted_quests）
    """
    # 检查 1: 任务类型是否启用
    if not task_cfg.enable:
        return False

    # 检查 2: 接受次数是否超限
    if task_cfg.max_accept_count >= 0:  # -1 表示无限制
        if current_count >= task_cfg.max_accept_count:
            return False

    # 检查 3: 邀请者是否在白名单
    if task_cfg.allowed_inviters:  # 空列表表示接受所有
        if invite.inviter_name not in task_cfg.allowed_inviters:
            return False

    # 检查 4: 协作类型过滤（仅 wanted_quests）
    if invite.task_type == "wanted_quests" and invite.cooperation_type:
        if hasattr(task_cfg, 'allowed_cooperation_types'):
            if invite.cooperation_type not in task_cfg.allowed_cooperation_types:
                return False

    return True


def test_invite_validation():
    """模拟验证逻辑测试"""

    print("=" * 60)
    print("T1.6 邀请验证逻辑单元测试")
    print("=" * 60)

    # 测试用邀请
    invite_orochi = MockInviteInfo(
        task_type="orochi",
        inviter_name="测试好友A"
    )

    invite_wq = MockInviteInfo(
        task_type="wanted_quests",
        inviter_name="测试好友B",
        cooperation_type="jade"
    )

    # 场景 1: 任务未启用
    print("\n场景 1: 任务未启用")
    cfg_disabled = MockTaskConfig(enable=False)
    result = should_accept_invite(invite_orochi, cfg_disabled)
    print(f"  enable={cfg_disabled.enable} → should_accept={result}")
    assert not result, "❌ Should reject when disabled"
    print("  ✅ PASS: Correctly rejects disabled task")

    # 场景 2: 次数限制 max_accept_count=0
    print("\n场景 2: 次数限制 max_accept_count=0")
    cfg_limit_0 = MockTaskConfig(enable=True, max_accept_count=0)
    result = should_accept_invite(invite_orochi, cfg_limit_0, current_count=0)
    print(f"  max_accept_count={cfg_limit_0.max_accept_count}, current=0 → should_accept={result}")
    assert not result, "❌ Should reject when limit=0"
    print("  ✅ PASS: Correctly rejects when limit=0")

    # 场景 3: 次数限制 max_accept_count=-1 (无限制)
    print("\n场景 3: 次数限制 max_accept_count=-1 (无限制)")
    cfg_unlimited = MockTaskConfig(enable=True, max_accept_count=-1)
    result = should_accept_invite(invite_orochi, cfg_unlimited, current_count=100)
    print(f"  max_accept_count={cfg_unlimited.max_accept_count}, current=100 → should_accept={result}")
    assert result, "❌ Should accept when unlimited"
    print("  ✅ PASS: Correctly accepts unlimited")

    # 场景 4: 次数限制 max_accept_count=3, current=2
    print("\n场景 4: 次数限制 max_accept_count=3, current=2")
    cfg_limit_3 = MockTaskConfig(enable=True, max_accept_count=3)
    result = should_accept_invite(invite_orochi, cfg_limit_3, current_count=2)
    print(f"  max_accept_count={cfg_limit_3.max_accept_count}, current=2 → should_accept={result}")
    assert result, "❌ Should accept when under limit"
    print("  ✅ PASS: Correctly accepts when under limit")

    # 场景 5: 次数限制 max_accept_count=3, current=3
    print("\n场景 5: 次数限制 max_accept_count=3, current=3")
    result = should_accept_invite(invite_orochi, cfg_limit_3, current_count=3)
    print(f"  max_accept_count={cfg_limit_3.max_accept_count}, current=3 → should_accept={result}")
    assert not result, "❌ Should reject when at limit"
    print("  ✅ PASS: Correctly rejects when at limit")

    # 场景 6: 白名单为空（接受所有）
    print("\n场景 6: 白名单为空（接受所有）")
    cfg_no_whitelist = MockTaskConfig(enable=True, allowed_inviters=[])
    result = should_accept_invite(invite_orochi, cfg_no_whitelist)
    print(f"  allowed_inviters={cfg_no_whitelist.allowed_inviters}, inviter='{invite_orochi.inviter_name}' → should_accept={result}")
    assert result, "❌ Should accept when whitelist empty"
    print("  ✅ PASS: Correctly accepts when whitelist empty")

    # 场景 7: 白名单匹配
    print("\n场景 7: 白名单匹配")
    cfg_whitelist_match = MockTaskConfig(enable=True, allowed_inviters=["测试好友A", "测试好友B"])
    result = should_accept_invite(invite_orochi, cfg_whitelist_match)
    print(f"  allowed_inviters={cfg_whitelist_match.allowed_inviters}, inviter='{invite_orochi.inviter_name}' → should_accept={result}")
    assert result, "❌ Should accept when inviter in whitelist"
    print("  ✅ PASS: Correctly accepts when inviter in whitelist")

    # 场景 8: 白名单不匹配
    print("\n场景 8: 白名单不匹配")
    cfg_whitelist_nomatch = MockTaskConfig(enable=True, allowed_inviters=["其他好友"])
    result = should_accept_invite(invite_orochi, cfg_whitelist_nomatch)
    print(f"  allowed_inviters={cfg_whitelist_nomatch.allowed_inviters}, inviter='{invite_orochi.inviter_name}' → should_accept={result}")
    assert not result, "❌ Should reject when inviter not in whitelist"
    print("  ✅ PASS: Correctly rejects when inviter not in whitelist")

    # 场景 9: 协作类型允许 (wanted_quests)
    print("\n场景 9: 协作类型允许 (wanted_quests)")
    cfg_coop_allowed = MockCooperationConfig(enable=True, allowed_cooperation_types=["jade", "dog_food"])
    result = should_accept_invite(invite_wq, cfg_coop_allowed)
    print(f"  allowed_cooperation_types={cfg_coop_allowed.allowed_cooperation_types}, type='{invite_wq.cooperation_type}' → should_accept={result}")
    assert result, "❌ Should accept when cooperation type allowed"
    print("  ✅ PASS: Correctly accepts when cooperation type allowed")

    # 场景 10: 协作类型不允许
    print("\n场景 10: 协作类型不允许")
    cfg_coop_disallowed = MockCooperationConfig(enable=True, allowed_cooperation_types=["dog_food", "cat_food"])
    result = should_accept_invite(invite_wq, cfg_coop_disallowed)
    print(f"  allowed_cooperation_types={cfg_coop_disallowed.allowed_cooperation_types}, type='{invite_wq.cooperation_type}' → should_accept={result}")
    assert not result, "❌ Should reject when cooperation type not allowed"
    print("  ✅ PASS: Correctly rejects when cooperation type not allowed")

    # 场景 11: 组合测试 - 全部通过
    print("\n场景 11: 组合测试 - 全部条件通过")
    cfg_all_pass = MockTaskConfig(enable=True, max_accept_count=5, allowed_inviters=["测试好友A"])
    result = should_accept_invite(invite_orochi, cfg_all_pass, current_count=2)
    print(f"  enable={cfg_all_pass.enable}, max_accept_count={cfg_all_pass.max_accept_count}, current=2, whitelist={cfg_all_pass.allowed_inviters}")
    print(f"  → should_accept={result}")
    assert result, "❌ Should accept when all conditions pass"
    print("  ✅ PASS: Correctly accepts when all conditions pass")

    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_invite_validation()
