from tasks.Component.SwitchAccount.assets import SwitchAccountAssets
from tasks.base_task import BaseTask
from module.logger import logger
from module.base.timer import Timer
from time import sleep


class ExitGame(BaseTask, SwitchAccountAssets):

    def exitGame(self):
        logger.info("start game exit")
        # 打开该页面比较慢 如果interval短 将发生异常
        self.ui_click(self.C_SA_EG_PROFILE_PHOTO, self.I_SA_USER_CENTER_PROFILE, 3)
        self.ui_click(self.I_SA_USER_CENTER, self.I_SA_SWITCH_ACCOUNT_BTN, 6)
        self.ui_click_until_disappear(self.I_SA_SWITCH_ACCOUNT_BTN, 3)

        timer = Timer(20).start()
        while not timer.reached():
            self.screenshot()
            if self.appear(self.I_SA_NETEASE_GAME_LOGO) or self.appear(self.I_CHECK_LOGIN_FORM):
                logger.info("Account switch page ready")
                return
            if hasattr(self, "appear_select_server_overlay") and self.appear_select_server_overlay():
                logger.info("Account switch select server overlay ready")
                return
            sleep(0.5)
        logger.warning("Account switch page did not become ready after switch account")
