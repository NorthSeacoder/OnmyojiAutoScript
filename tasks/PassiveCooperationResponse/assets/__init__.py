# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
"""
被动响应任务资产

复用 GeneralInvite 组件的邀请弹窗检测资产：
- I_I_ACCEPT: 队员接受邀请按钮（主要检测）
- I_I_ACCEPT_DEFAULT: 队员默认接受邀请按钮（备用检测）
- I_I_ACCEPT_JY: 寄养邀请按钮（备用检测）
- I_GI_SURE: 确定按钮（点击接受后的确认）
- I_I_NO_DEFAULT: 不勾选默认邀请（需要取消勾选）

OCR 区域：
- O_FRIEND_NAME_1/O_FRIEND_NAME_2: 可用于识别邀请者昵称（如果弹窗中有昵称显示）
"""

# 直接从 GeneralInvite 组件导入邀请相关资产
from tasks.Component.GeneralInvite.assets import GeneralInviteAssets

# 为了保持接口一致性，创建本地别名
class PassiveCooperationResponseAssets:
    """
    被动响应任务资产类

    复用 GeneralInvite 的邀请检测资产，避免重复维护图片资源。
    """

    # 邀请弹窗检测 - 主要用于判断是否有邀请
    INVITE_POPUP = GeneralInviteAssets.I_I_ACCEPT
    INVITE_POPUP_DEFAULT = GeneralInviteAssets.I_I_ACCEPT_DEFAULT
    INVITE_POPUP_JY = GeneralInviteAssets.I_I_ACCEPT_JY

    # 接受按钮 - 用于点击接受邀请
    INVITE_ACCEPT_BUTTON = GeneralInviteAssets.I_I_ACCEPT
    INVITE_ACCEPT_DEFAULT_BUTTON = GeneralInviteAssets.I_I_ACCEPT_DEFAULT

    # 确认按钮 - 点击接受后的确认
    INVITE_SURE_BUTTON = GeneralInviteAssets.I_GI_SURE

    # 取消默认邀请勾选
    INVITE_NO_DEFAULT = GeneralInviteAssets.I_I_NO_DEFAULT

    # OCR 区域 - 用于识别邀请者昵称（如果需要）
    INVITER_NAME_REGION_1 = GeneralInviteAssets.O_FRIEND_NAME_1
    INVITER_NAME_REGION_2 = GeneralInviteAssets.O_FRIEND_NAME_2

    # 房间状态检测
    IN_ROOM = GeneralInviteAssets.I_GI_IN_ROOM
    HOME_PAGE = GeneralInviteAssets.I_GI_HOME
    EXPLORE_PAGE = GeneralInviteAssets.I_GI_EXPLORE

    # 加成图标
    BUFF_ICON = GeneralInviteAssets.I_GI_BUFF
