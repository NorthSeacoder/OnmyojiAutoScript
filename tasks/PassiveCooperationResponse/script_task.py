# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from time import sleep
from datetime import datetime

from tasks.base_task import BaseTask
from tasks.PassiveCooperationResponse.invite_detector import InviteDetector, InviteInfo
from tasks.PassiveCooperationResponse.config import PassiveCooperationResponse
from module.logger import logger
from module.exception import TaskEnd, RequestHumanTakeover


class ScriptTask(BaseTask):
    """被动响应任务主逻辑"""

    def __init__(self, config, device):
        super().__init__(device)
        self.config = config
        self.detector = InviteDetector(device)
        self.accept_counts = {
            "orochi": 0,
            "exploration": 0,
            "wanted_quests": 0
        }

    def run(self):
        """主循环：监听邀请 → 验证 → 接受 → 执行 → 返回待命态"""
        logger.hr("PassiveCooperationResponse", 0)
        logger.info("Start listening for invites")

        enabled_tasks = self._get_enabled_tasks()
        if not enabled_tasks:
            logger.warning("No passive tasks enabled, exiting")
            raise TaskEnd

        logger.info(f"Listening for: {', '.join(enabled_tasks)}")

        # TODO: T1.9 实现主循环
        # while True:
        #     self.screenshot()
        #     invite = self.detector.detect_invite()
        #     if invite is None:
        #         sleep(1)
        #         continue
        #     ...

        raise TaskEnd

    def _get_enabled_tasks(self) -> list[str]:
        """获取已启用的任务类型列表"""
        enabled = []
        passive_cfg = self.config.passive_cooperation_response.passive_config

        if passive_cfg.orochi.enable:
            enabled.append("orochi")
        if passive_cfg.exploration.enable:
            enabled.append("exploration")
        if passive_cfg.wanted_quests.enable:
            enabled.append("wanted_quests")

        return enabled

    def _should_accept_invite(self, invite: InviteInfo) -> bool:
        """
        验证是否应该接受邀请

        检查：
        1. 任务类型是否启用
        2. 接受次数是否超限
        3. 邀请者是否在白名单
        """
        # TODO: T1.6 实现验证逻辑
        pass

    def _get_rejection_reason(self, invite: InviteInfo) -> str:
        """获取拒绝原因（用于日志）"""
        # TODO: T1.6 实现
        return "reason not implemented"

    def _execute_task(self, invite: InviteInfo) -> bool:
        """
        执行对应任务的 member 模式

        Args:
            invite: 邀请信息

        Returns:
            True if success, False otherwise
        """
        try:
            if invite.task_type == "orochi":
                return self._execute_orochi_member(invite)
            elif invite.task_type == "exploration":
                return self._execute_exploration_member(invite)
            elif invite.task_type == "wanted_quests":
                return self._execute_cooperation_member(invite)
            else:
                logger.warning(f"Unknown task type: {invite.task_type}")
                return False
        except Exception as e:
            logger.exception(f"Failed to execute {invite.task_type}: {e}")
            return False

    def _execute_orochi_member(self, invite: InviteInfo) -> bool:
        """执行御魂 member 模式"""
        # TODO: T1.8 实现
        logger.info("Execute orochi member (not implemented)")
        return False

    def _execute_exploration_member(self, invite: InviteInfo) -> bool:
        """执行探索 member 模式"""
        # TODO: Phase 2 实现
        logger.info("Execute exploration member (not implemented)")
        return False

    def _execute_cooperation_member(self, invite: InviteInfo) -> bool:
        """执行协作 member 模式"""
        # TODO: Phase 3 实现
        logger.info("Execute cooperation member (not implemented)")
        return False


if __name__ == "__main__":
    from module.config.config import Config
    from module.device.device import Device

    config = Config('oas1')
    device = Device(config)
    task = ScriptTask(config, device)
    task.run()
