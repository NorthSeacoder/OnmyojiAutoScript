# This Python file uses the following encoding: utf-8
from datetime import datetime, timedelta

from module.exception import RequestHumanTakeover, TaskEnd
from module.logger import logger
from tasks.AreaBoss.script_task import ScriptTask as AreaBossScriptTask
from tasks.Component.SwitchAccount.switch_account import SwitchAccount
from tasks.DailyTrifles.script_task import ScriptTask as DailyTriflesScriptTask
from tasks.Exploration.script_task import ScriptTask as ExplorationScriptTask
from tasks.FindJade.script_task import ScriptTask as FindJadeScriptTask
from tasks.GameUi.game_ui import GameUi
from tasks.Hunt.script_task import ScriptTask as HuntScriptTask
from tasks.MysteryShop.script_task import ScriptTask as MysteryShopScriptTask
from tasks.Orochi.config import UserStatus as OrochiUserStatus
from tasks.Orochi.script_task import ScriptTask as OrochiScriptTask
from tasks.SubAccountRotation.config import AccountSource, SubAccountTask
from tasks.TalismanPass.script_task import ScriptTask as TalismanPassScriptTask


class ScriptTask(GameUi):
    def run(self):
        rotation = self.config.sub_account_rotation
        rotation_config = rotation.sub_account_rotation_config
        sub_tasks = rotation_config.sub_tasks()

        if not sub_tasks:
            logger.warning("SubAccountRotation has no enabled sub-task")
            self.next_run(success=True)
            raise TaskEnd("SubAccountRotation")

        accounts = self.load_accounts(rotation_config.account_source)
        if not accounts:
            logger.warning("SubAccountRotation has no account")
            self.next_run(success=True)
            raise TaskEnd("SubAccountRotation")

        logger.hr("SubAccountRotation")
        handled_accounts = 0
        for account in accounts:
            due_sub_tasks = [
                sub_task for sub_task in sub_tasks
                if rotation.need_run(account.character, account.svr, sub_task)
            ]
            if not due_sub_tasks:
                logger.info(f"SubAccountRotation skip {account.character}-{account.svr}: no due sub-task")
                continue

            if rotation_config.max_accounts_per_run and handled_accounts >= rotation_config.max_accounts_per_run:
                logger.info("SubAccountRotation max_accounts_per_run reached")
                break

            logger.info(
                f"SubAccountRotation start account {account.character}-{account.svr}, "
                f"sub_tasks={[task.value for task in due_sub_tasks]}"
            )
            if not self.switch_account(account):
                for sub_task in due_sub_tasks:
                    rotation.update_failure(account.character, account.svr, sub_task)
                self.config.save()
                if rotation_config.continue_on_switch_failure:
                    continue
                self.next_run(success=False)
                raise TaskEnd("SubAccountRotation")

            handled_accounts += 1
            for sub_task in due_sub_tasks:
                if self.run_sub_task(account, sub_task):
                    rotation.update_success(account.character, account.svr, sub_task)
                else:
                    rotation.update_failure(account.character, account.svr, sub_task)
                self.config.save()

        self.next_run(success=True)
        raise TaskEnd("SubAccountRotation")

    def load_accounts(self, account_source: AccountSource):
        if account_source == AccountSource.FIND_JADE:
            return self.config.find_jade.sup_account_list or []
        logger.warning(f"Unknown account source: {account_source}")
        return []

    def switch_account(self, account) -> bool:
        try:
            return SwitchAccount(self.config, self.device, account).switchAccount()
        except RequestHumanTakeover:
            raise
        except Exception as e:
            logger.error(f"SubAccountRotation switch account {account.character}-{account.svr} failed: {e}")
            return False

    def run_sub_task(self, account, sub_task: SubAccountTask):
        logger.info(f"SubAccountRotation run {sub_task.value} for {account.character}-{account.svr}")
        if sub_task == SubAccountTask.LOGIN_ONLY:
            return True
        if sub_task == SubAccountTask.FIND_JADE:
            return self.run_find_jade(account)
        if sub_task == SubAccountTask.OROCHI:
            return self.run_orochi(account)
        if sub_task == SubAccountTask.MYSTERY_SHOP:
            return self.run_mystery_shop(account)
        if sub_task == SubAccountTask.DAILY_TRIFLES_STORE_SIGN:
            return self.run_daily_trifles_store_sign(account)
        if sub_task == SubAccountTask.HUNT:
            return self.run_hunt(account)
        if sub_task == SubAccountTask.TALISMAN_PASS:
            return self.run_talisman_pass(account)
        if sub_task == SubAccountTask.EXPLORATION:
            return self.run_exploration(account)
        if sub_task == SubAccountTask.AREA_BOSS:
            return self.run_area_boss(account)
        logger.warning(f"SubAccountRotation sub-task {sub_task.value} is not implemented in MVP")
        return False

    def run_find_jade(self, account) -> bool:
        runner = FindJadeScriptTask(self.config, self.device)
        original_set_next_run = runner.set_next_run
        result = {"called": False, "success": None}

        def capture_next_run(task: str, finish: bool = False, success: bool = None,
                             server: bool = True, target: datetime = None) -> None:
            if task == "WantedQuests":
                result["called"] = True
                result["success"] = success
                logger.info(
                    "SubAccountRotation captured WantedQuests next_run from FindJade "
                    f"success={success}; keep WantedQuests scheduler unchanged"
                )
                return
            original_set_next_run(task, finish=finish, success=success, server=server, target=target)

        runner.set_next_run = capture_next_run
        try:
            success = runner.run_current_account(account)
        except RequestHumanTakeover:
            raise
        except Exception as e:
            logger.exception(e)
            return False
        if success:
            self.config.find_jade.update_account_login_history(account)
        return success

    def run_mystery_shop(self, account) -> bool:
        runner = MysteryShopScriptTask(self.config, self.device)
        original_set_next_run = runner.set_next_run
        result = {"called": False, "success": None}

        def capture_next_run(task: str, finish: bool = False, success: bool = None,
                             server: bool = True, target: datetime = None) -> None:
            if task == SubAccountTask.MYSTERY_SHOP.value:
                result["called"] = True
                result["success"] = success
                logger.info(
                    "SubAccountRotation captured MysteryShop next_run "
                    f"success={success}; keep MysteryShop scheduler unchanged"
                )
                return
            original_set_next_run(task, finish=finish, success=success, server=server, target=target)

        runner.set_next_run = capture_next_run
        try:
            runner.run()
        except TaskEnd:
            if not result["called"]:
                logger.warning(
                    "SubAccountRotation MysteryShop ended without set_next_run "
                    f"for {account.character}-{account.svr}"
                )
                return False
            return True
        except RequestHumanTakeover:
            raise
        except Exception as e:
            logger.exception(e)
            return False
        logger.warning(
            "SubAccountRotation MysteryShop returned without TaskEnd "
            f"for {account.character}-{account.svr}"
        )
        return bool(result["called"])

    def run_daily_trifles_store_sign(self, account) -> bool:
        runner = DailyTriflesScriptTask(self.config, self.device)
        original_set_next_run = runner.set_next_run
        result = {"called": False, "success": None}
        config = self.config.daily_trifles.trifles_config
        original_store_sign = config.store_sign
        original_buy_sushi_count = config.buy_sushi_count

        def capture_next_run(task: str, finish: bool = False, success: bool = None,
                             server: bool = True, target: datetime = None) -> None:
            if task == "DailyTrifles":
                result["called"] = True
                result["success"] = success
                logger.info(
                    "SubAccountRotation captured DailyTrifles next_run "
                    f"success={success}; keep DailyTrifles scheduler unchanged"
                )
                return
            original_set_next_run(task, finish=finish, success=success, server=server, target=target)

        runner.set_next_run = capture_next_run
        try:
            config.store_sign = True
            config.buy_sushi_count = -1
            runner.run_store()
            logger.info(
                "SubAccountRotation completed DailyTriflesStoreSign "
                f"for {account.character}-{account.svr}"
            )
            return True
        except RequestHumanTakeover:
            raise
        except Exception as e:
            logger.exception(e)
            return False
        finally:
            config.store_sign = original_store_sign
            config.buy_sushi_count = original_buy_sushi_count

    def run_hunt(self, account) -> bool:
        runner = HuntScriptTask(self.config, self.device)
        original_set_next_run = runner.set_next_run
        result = {"called": False, "success": None}

        def capture_next_run(task: str, finish: bool = False, success: bool = None,
                             server: bool = True, target: datetime = None) -> None:
            if task == SubAccountTask.HUNT.value:
                result["called"] = True
                result["success"] = success
                logger.info(
                    "SubAccountRotation captured Hunt next_run "
                    f"success={success}; keep Hunt scheduler unchanged"
                )
                return
            original_set_next_run(task, finish=finish, success=success, server=server, target=target)

        runner.set_next_run = capture_next_run
        try:
            runner.run()
        except TaskEnd:
            if not result["called"]:
                logger.warning(
                    "SubAccountRotation Hunt ended without set_next_run "
                    f"for {account.character}-{account.svr}"
                )
                return False
            return True
        except RequestHumanTakeover:
            raise
        except Exception as e:
            logger.exception(e)
            return False
        logger.warning(
            "SubAccountRotation Hunt returned without TaskEnd "
            f"for {account.character}-{account.svr}"
        )
        return bool(result["called"])

    def run_exploration(self, account) -> bool:
        runner = ExplorationScriptTask(self.config, self.device)
        original_set_next_run = runner.set_next_run
        result = {"called": False, "success": None}
        blocked_tasks = {"RealmRaid", "MemoryScrolls"}

        def capture_next_run(task: str, finish: bool = False, success: bool = None,
                             server: bool = True, target: datetime = None) -> None:
            if task == SubAccountTask.EXPLORATION.value:
                result["called"] = True
                result["success"] = success
                logger.info(
                    "SubAccountRotation captured Exploration next_run "
                    f"success={success}; keep Exploration scheduler unchanged"
                )
                return
            if task in blocked_tasks:
                logger.info(
                    "SubAccountRotation ignored Exploration side-effect next_run "
                    f"for {task}; keep {task} scheduler unchanged"
                )
                return
            original_set_next_run(task, finish=finish, success=success, server=server, target=target)

        runner.set_next_run = capture_next_run
        try:
            runner.run()
        except TaskEnd:
            if not result["called"]:
                logger.warning(
                    "SubAccountRotation Exploration ended without set_next_run "
                    f"for {account.character}-{account.svr}"
                )
                return False
            return True
        except RequestHumanTakeover:
            raise
        except Exception as e:
            logger.exception(e)
            return False
        logger.warning(
            "SubAccountRotation Exploration returned without TaskEnd "
            f"for {account.character}-{account.svr}"
        )
        return bool(result["called"])

    def run_area_boss(self, account) -> bool:
        runner = AreaBossScriptTask(self.config, self.device)
        original_set_next_run = runner.set_next_run
        result = {"called": False, "success": False}
        original_lock_team_enable = self.config.area_boss.general_battle.lock_team_enable

        def capture_next_run(task: str, finish: bool = False, success: bool = None,
                             server: bool = True, target: datetime = None) -> None:
            if task == SubAccountTask.AREA_BOSS.value:
                result["called"] = True
                result["success"] = bool(success)
                logger.info(
                    "SubAccountRotation captured AreaBoss next_run "
                    f"success={success}; keep AreaBoss scheduler unchanged"
                )
                return
            original_set_next_run(task, finish=finish, success=success, server=server, target=target)

        runner.set_next_run = capture_next_run
        try:
            runner.run()
        except TaskEnd:
            if not result["called"]:
                logger.warning(
                    "SubAccountRotation AreaBoss ended without set_next_run "
                    f"for {account.character}-{account.svr}"
                )
            return result["success"]
        except RequestHumanTakeover:
            raise
        except Exception as e:
            logger.exception(e)
            return False
        finally:
            # 必须在 finally 外层恢复配置，确保 TaskEnd 异常时也能执行
            self.config.area_boss.general_battle.lock_team_enable = original_lock_team_enable

        logger.warning(
            "SubAccountRotation AreaBoss returned without TaskEnd "
            f"for {account.character}-{account.svr}"
        )
        return result["success"]

    def run_talisman_pass(self, account) -> bool:
        runner = TalismanPassScriptTask(self.config, self.device)
        original_set_next_run = runner.set_next_run
        result = {"called": False, "success": None}

        def capture_next_run(task: str, finish: bool = False, success: bool = None,
                             server: bool = True, target: datetime = None) -> None:
            if task == SubAccountTask.TALISMAN_PASS.value:
                result["called"] = True
                result["success"] = success
                logger.info(
                    "SubAccountRotation captured TalismanPass next_run "
                    f"success={success}; keep TalismanPass scheduler unchanged"
                )
                return
            original_set_next_run(task, finish=finish, success=success, server=server, target=target)

        runner.set_next_run = capture_next_run
        try:
            runner.run()
        except TaskEnd:
            if not result["called"]:
                logger.warning(
                    "SubAccountRotation TalismanPass ended without set_next_run "
                    f"for {account.character}-{account.svr}"
                )
                return False
            return True
        except RequestHumanTakeover:
            raise
        except Exception as e:
            logger.exception(e)
            return False
        logger.warning(
            "SubAccountRotation TalismanPass returned without TaskEnd "
            f"for {account.character}-{account.svr}"
        )
        return bool(result["called"])

    def run_orochi(self, account) -> bool:
        if self.config.orochi.orochi_config.user_status != OrochiUserStatus.LEADER:
            logger.warning(
                "SubAccountRotation Orochi requires orochi_config.user_status=leader "
                f"for {account.character}-{account.svr}"
            )
            return False
        if not self.config.orochi.invite_config.friend_1:
            logger.warning(
                "SubAccountRotation Orochi requires orochi.invite_config.friend_1 "
                f"for {account.character}-{account.svr}"
            )
            return False

        runner = OrochiScriptTask(self.config, self.device)
        original_set_next_run = runner.set_next_run
        result = {"called": False, "success": False}

        def capture_next_run(task: str, finish: bool = False, success: bool = None,
                             server: bool = True, target: datetime = None) -> None:
            if task == SubAccountTask.OROCHI.value:
                result["called"] = True
                result["success"] = bool(success)
                logger.info(
                    "SubAccountRotation captured Orochi next_run "
                    f"success={success}; keep Orochi scheduler unchanged"
                )
                return
            original_set_next_run(task, finish=finish, success=success, server=server, target=target)

        runner.set_next_run = capture_next_run
        try:
            runner.run()
        except TaskEnd:
            if not result["called"]:
                logger.warning(
                    "SubAccountRotation Orochi ended without set_next_run "
                    f"for {account.character}-{account.svr}"
                )
            return result["success"]
        except RequestHumanTakeover:
            raise
        except Exception as e:
            logger.exception(e)
            return False
        logger.warning(
            "SubAccountRotation Orochi returned without TaskEnd "
            f"for {account.character}-{account.svr}"
        )
        return result["success"]

    def next_run(self, success: bool):
        if success:
            self.set_next_run("SubAccountRotation", success=True, finish=True)
        else:
            self.set_next_run("SubAccountRotation", target=datetime.now() + timedelta(minutes=10))


if __name__ == "__main__":
    from module.config.config import Config
    from module.device.device import Device

    c = Config("oas1")
    d = Device(c)
    t = ScriptTask(c, d)
    t.run()
