# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from time import sleep
from datetime import datetime
from typing import Optional, Literal
from dataclasses import dataclass

from tasks.PassiveCooperationResponse.assets import PassiveCooperationResponseAssets
from module.logger import logger


@dataclass
class InviteInfo:
    """邀请信息"""
    task_type: Literal["orochi", "exploration", "wanted_quests", "unknown"]
    inviter_name: str
    detected_at: datetime
    layer: Optional[str] = None  # 御魂层级/探索章节
    cooperation_type: Optional[str] = None  # 协作类型（玉藻/狗粮/猫粮）


class InviteDetector(PassiveCooperationResponseAssets):
    """邀请检测器"""

    def __init__(self, parent):
        """
        Args:
            parent: ScriptTask instance (provides appear, screenshot, ui_get_current_page methods)
        """
        self.parent = parent

    def detect_invite(self) -> Optional[InviteInfo]:
        """
        检测当前屏幕是否有邀请弹窗

        Returns:
            InviteInfo if detected, None otherwise
        """
        # 检测邀请弹窗（优先级：默认 > 普通 > 寄养）
        if not (self.parent.appear(self.INVITE_POPUP_DEFAULT) or
                self.parent.appear(self.INVITE_POPUP) or
                self.parent.appear(self.INVITE_POPUP_JY)):
            return None

        logger.info("Detected invite popup")

        # 推断邀请类型
        task_type = self._infer_invite_type()

        # OCR 解析邀请者昵称（暂时使用占位符）
        inviter_name = self._parse_inviter_name()

        # 构造邀请信息
        invite_info = InviteInfo(
            task_type=task_type,
            inviter_name=inviter_name,
            detected_at=datetime.now()
        )

        logger.info(f"Invite detected: type={task_type}, inviter={inviter_name}")
        return invite_info

    def _infer_invite_type(self) -> str:
        """
        根据当前页面上下文推断邀请类型

        Returns:
            "orochi" | "exploration" | "wanted_quests" | "unknown"
        """
        # 获取当前页面
        current_page = self.parent.ui_get_current_page()
        page_name = str(current_page)

        logger.info(f"Current page for invite inference: {page_name}")

        # 根据页面判断邀请类型
        # 庭院页面：可能是御魂/探索/协作
        if "main" in page_name.lower() or "home" in page_name.lower():
            # 在庭院时，优先判断为御魂邀请（最常见）
            # 后续可通过 OCR 邀请内容进一步判断
            return "orochi"

        # 探索页面：探索邀请
        if "explore" in page_name.lower() or "exploration" in page_name.lower():
            return "exploration"

        # 悬赏页面：协作邀请
        if "wanted" in page_name.lower() or "cooperation" in page_name.lower():
            return "wanted_quests"

        # 默认返回 unknown
        logger.warning(f"Unable to infer invite type from page: {page_name}")
        return "unknown"

    def _parse_inviter_name(self) -> str:
        """
        OCR 解析邀请者昵称

        Returns:
            邀请者昵称（失败时返回占位符）
        """
        # TODO: T1.4 实现 OCR 解析
        # 暂时返回占位符，避免阻塞主流程
        return "Unknown"

    def accept_invite(self) -> bool:
        """
        点击接受邀请按钮

        Returns:
            True if accepted, False otherwise
        """
        logger.info("Attempting to accept invite")

        max_attempts = 10
        for attempt in range(max_attempts):
            self.parent.screenshot()

            # 检查是否已进入房间（接受成功）
            if self.parent.appear(self.IN_ROOM):
                logger.info("Successfully entered room")
                return True

            # 取消默认邀请勾选（如果出现）
            if self.parent.appear_then_click(self.INVITE_NO_DEFAULT, interval=1):
                logger.info("Unchecked default invite")
                continue

            # 点击确定按钮（接受后的确认）
            if self.parent.appear_then_click(self.INVITE_SURE_BUTTON, interval=1):
                logger.info("Clicked invite sure button")
                continue

            # 点击接受按钮（默认位置）
            if self.parent.appear_then_click(self.INVITE_ACCEPT_DEFAULT_BUTTON, interval=1):
                logger.info("Clicked default accept button")
                continue

            # 点击接受按钮
            if self.parent.appear_then_click(self.INVITE_ACCEPT_BUTTON, interval=1):
                logger.info("Clicked accept button")
                continue

            sleep(0.5)

        logger.warning(f"Failed to accept invite after {max_attempts} attempts")
        return False
                continue

            # 点击接受按钮（优先默认接受）
            if self.appear_then_click(self.INVITE_ACCEPT_DEFAULT_BUTTON, interval=1):
                logger.info("Clicked accept default button")
                continue

            # 点击普通接受按钮
            if self.appear_then_click(self.INVITE_ACCEPT_BUTTON, interval=1):
                logger.info("Clicked accept button")
                continue

            # 等待页面响应
            sleep(0.5)

        logger.warning(f"Failed to accept invite after {max_attempts} attempts")
        return False
