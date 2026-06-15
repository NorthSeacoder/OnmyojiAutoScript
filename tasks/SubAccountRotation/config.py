# This Python file uses the following encoding: utf-8
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict

from deploy.logger import logger
from pydantic import BaseModel, Field, SerializationInfo, ValidationError, model_serializer, model_validator

from tasks.Component.config_base import ConfigBase, DateTime, TimeDelta
from tasks.Component.config_scheduler import Scheduler
from tasks.Component.SwitchAccount.switch_account_config import AccountInfo


class SubAccountTask(str, Enum):
    LOGIN_ONLY = "LoginOnly"
    FIND_JADE = "FindJade"
    OROCHI = "Orochi"
    MYSTERY_SHOP = "MysteryShop"
    DAILY_TRIFLES_STORE_SIGN = "DailyTriflesStoreSign"
    HUNT = "Hunt"
    TALISMAN_PASS = "TalismanPass"
    EXPLORATION = "Exploration"
    AREA_BOSS = "AreaBoss"


class SubAccountRotationConfig(ConfigBase):
    # 批量配置：全部小号的通用服务器
    default_svr: str = Field(default="", description="default_svr_help")
    # 批量配置：全部小号是否为安卓（True=安卓，False=苹果）
    default_apple_or_android: bool = Field(default=True, description="default_apple_or_android_help")
    # 账号数量（GUI 动态生成对应数量的输入框）
    account_count: int = Field(default=1, ge=0, le=20, description="account_count_help")

    enabled_sub_tasks: str = Field(default=SubAccountTask.LOGIN_ONLY.value, description="enabled_sub_tasks_help")
    account_interval: TimeDelta = Field(default=TimeDelta(hours=13), description="account_interval_help")
    continue_on_switch_failure: bool = Field(default=True, description="continue_on_switch_failure_help")
    max_accounts_per_run: int = Field(default=0, ge=0, description="max_accounts_per_run_help")
    auto_reset_tasks_on_startup: bool = Field(default=False, description="auto_reset_tasks_on_startup_help")
    include_current_account: bool = Field(default=True, description="include_current_account_help")

    def sub_tasks(self) -> list[SubAccountTask]:
        tasks = []
        for raw in self.enabled_sub_tasks.replace("，", ",").split(","):
            name = raw.strip()
            if not name:
                continue
            try:
                tasks.append(SubAccountTask(name))
            except ValueError:
                logger.warning(f"Unknown sub account sub-task: {name}")
        return tasks


class SubTaskHistory(ConfigBase):
    character: str = Field(default="", description="character_help")
    svr: str = Field(default="", description="svr_help")
    sub_task: SubAccountTask = Field(default=SubAccountTask.LOGIN_ONLY, description="sub_task_help")
    last_complete_time: DateTime = Field(
        default=DateTime.fromisoformat("2023-01-01 00:00:00"),
        description="last_complete_time_help",
    )
    last_failure_time: DateTime = Field(
        default=DateTime.fromisoformat("2023-01-01 00:00:00"),
        description="last_failure_time_help",
    )
    failure_count: int = Field(default=0, ge=0, description="failure_count_help")

    def same_key(self, character: str, svr: str, sub_task: SubAccountTask) -> bool:
        return self.character == character and self.svr == svr and self.sub_task == sub_task


class SubAccountRotation(ConfigBase):
    scheduler: Scheduler = Field(default_factory=Scheduler)
    sub_account_rotation_config: SubAccountRotationConfig = Field(default_factory=SubAccountRotationConfig)
    # 账号列表（独立管理，不再依赖 FindJade）
    account_list: list[AccountInfo] = Field(default_factory=list, exclude=False)
    history_list: list[SubTaskHistory] = Field(default_factory=list, exclude=True)

    @classmethod
    def model_json_schema(cls, *args, **kwargs) -> Dict[str, Any]:
        schema = super().model_json_schema(*args, **kwargs)
        schema.get("properties", {}).pop("history_list", None)
        return schema

    def get_history(self, character: str, svr: str, sub_task: SubAccountTask) -> SubTaskHistory:
        for item in self.history_list:
            if item.same_key(character, svr, sub_task):
                return item
        item = SubTaskHistory(character=character, svr=svr, sub_task=sub_task)
        self.history_list.append(item)
        return item

    def need_run(self, character: str, svr: str, sub_task: SubAccountTask) -> bool:
        history = self.get_history(character, svr, sub_task)
        return datetime.now() - history.last_complete_time >= self.sub_account_rotation_config.account_interval

    def update_success(self, character: str, svr: str, sub_task: SubAccountTask):
        history = self.get_history(character, svr, sub_task)
        history.last_complete_time = datetime.now()
        history.failure_count = 0

    def update_failure(self, character: str, svr: str, sub_task: SubAccountTask):
        history = self.get_history(character, svr, sub_task)
        history.last_failure_time = datetime.now()
        history.failure_count += 1

    @model_validator(mode="before")
    @classmethod
    def validator_all(cls, v: dict) -> Any:
        if not isinstance(v, dict):
            return v

        # Handle history_list migration
        if "history_list" not in v:
            v["history_list"] = []

        remove_keys = []
        for key, value in v.items():
            if key == "history_list" or "history_list" not in key:
                continue
            try:
                item = SubTaskHistory(**value)
                if item.character:
                    v["history_list"].append(item)
                remove_keys.append(key)
            except (ValidationError, TypeError):
                pass

        for key in remove_keys:
            del v[key]

        # Handle account_list migration
        if "account_list" not in v:
            v["account_list"] = []

        remove_keys = []
        for key, value in v.items():
            if key == "account_list" or "account_list" not in key:
                continue
            try:
                item = AccountInfo(**value)
                if item.character:
                    v["account_list"].append(item)
                remove_keys.append(key)
            except (ValidationError, TypeError):
                pass

        for key in remove_keys:
            del v[key]

        return v

    @model_serializer()
    def serializer_model(self, info: SerializationInfo) -> Dict[str, Any]:
        data = {}
        hide_runtime_state = bool(info.context and info.context.get("hide", False))
        for key, value in self.__dict__.items():
            if hide_runtime_state and key == "history_list":
                continue
            if isinstance(value, list):
                for index, item in enumerate(value):
                    data[f"{key}_{index + 1}"] = item.model_dump()
            else:
                try:
                    data[key] = value.model_dump()
                except AttributeError:
                    data[key] = value
        return data
