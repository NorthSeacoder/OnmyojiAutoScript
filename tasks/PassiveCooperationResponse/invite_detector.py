# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from datetime import datetime
from typing import Optional, Literal
from dataclasses import dataclass

from tasks.base_task import BaseTask
from module.logger import logger


@dataclass
class InviteInfo:
    """邀请信息"""
    task_type: Literal["orochi", "exploration", "wanted_quests", "unknown"]
    inviter_name: str
    detected_at: datetime
    layer: Optional[str] = None  # 御魂层级/探索章节
    cooperation_type: Optional[str] = None  # 协作类型（玉藻/狗粮/猫粮）


class InviteDetector(BaseTask):
    """邀请检测器"""

    def __init__(self, device):
        super().__init__(device)

    def detect_invite(self) -> Optional[InviteInfo]:
        """
        检测当前屏幕是否有邀请弹窗

        Returns:
            InviteInfo if detected, None otherwise
        """
        # TODO: T1.4 实现检测逻辑
        # 1. 检测通用邀请弹窗资产
        # 2. OCR 解析邀请者昵称
        # 3. 推断邀请类型
        pass

    def _infer_invite_type(self) -> str:
        """
        根据当前页面上下文推断邀请类型

        Returns:
            "orochi" | "exploration" | "wanted_quests" | "unknown"
        """
        # TODO: T1.4 实现类型推断
        # 根据 ui_get_current_page() 或独特资产判断
        pass

    def accept_invite(self) -> bool:
        """
        点击接受邀请按钮

        Returns:
            True if accepted, False otherwise
        """
        # TODO: T1.4 实现接受逻辑
        # 点击 INVITE_ACCEPT_BUTTON
        # 等待弹窗消失
        pass
