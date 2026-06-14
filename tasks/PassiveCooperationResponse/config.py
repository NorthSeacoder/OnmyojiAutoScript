# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from typing import Literal, List
from pydantic import BaseModel, Field

from tasks.Component.config_scheduler import Scheduler
from tasks.Component.config_base import ConfigBase, TimeDelta


class PassiveTaskConfig(ConfigBase):
    """被动响应任务配置"""
    enable: bool = Field(default=False, description="是否接受该类型邀请")
    max_accept_count: int = Field(default=-1, description="最大接受次数，-1表示无限制")
    allowed_inviters: List[str] = Field(default_factory=list, description="邀请者白名单，空列表表示接受所有")
    buff_enable: bool = Field(default=False, description="是否自动开启加成（御魂加成/探索经验加成）")


class PassiveCooperationConfig(PassiveTaskConfig):
    """协作邀请配置（继承自PassiveTaskConfig，添加协作类型过滤）"""
    allowed_cooperation_types: List[str] = Field(
        default_factory=lambda: ["jade", "cat_food", "dog_food"],
        description="允许的协作类型：玉藻/狗粮/猫粮"
    )


class PassiveConfigModel(ConfigBase):
    """被动响应配置容器"""
    orochi: PassiveTaskConfig = Field(default_factory=PassiveTaskConfig, description="御魂邀请配置")
    exploration: PassiveTaskConfig = Field(default_factory=PassiveTaskConfig, description="探索邀请配置")
    wanted_quests: PassiveCooperationConfig = Field(default_factory=PassiveCooperationConfig, description="协作邀请配置")


class PassiveCooperationResponse(ConfigBase):
    """被动响应任务顶层配置"""
    scheduler: Scheduler = Field(default_factory=Scheduler, description="调度器配置")
    passive_config: PassiveConfigModel = Field(default_factory=PassiveConfigModel, description="被动响应配置")
