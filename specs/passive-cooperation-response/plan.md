# Implementation Plan: Passive Cooperation Response

**Workspace**: `passive-cooperation-response`
**Created**: 2026-06-13
**Status**: Draft

---

## Design Principles (Patch-first Strategy)

遵循项目开发原则，最小化对现有代码的修改，确保 upstream 兼容性：

1. **Adapter pattern over injection**: 新增 `PassiveCooperationResponse` 作为独立任务，不修改现有 `Orochi`/`Exploration`/`WantedQuests` 任务代码
2. **Interception over rewrite**: 不调用 `set_next_run()`，避免污染普通任务的 scheduler
3. **Temporary config mutation with restoration**: 被动响应任务临时修改 `user_status=member`、开启加成，执行完恢复
4. **Narrow entry points**: 调用现有任务的 member 模式方法（如 `run_member()`），不重写组队逻辑
5. **Guard conditions at task boundaries**: 在 `PassiveCooperationResponse` 入口处添加邀请检测和配置验证，不深入修改现有任务内部

---

## Architecture Overview

### High-Level Flow

```
PassiveCooperationResponse (新增任务)
  ↓
[1. 待命态循环]
  ↓
  Screenshot → 检测邀请弹窗
  ↓
  检测到邀请 → OCR 解析邀请者昵称 + 上下文判断类型
  ↓
[2. 验证配置]
  ↓
  检查 passive_config[task_type].enable
  检查 allowed_inviters 白名单
  检查 max_accept_count 限制
  ↓
  验证通过 → 接受邀请
  ↓
[3. 执行任务 (调用现有任务的 member 流程)]
  ↓
  临时修改配置:
    - user_status = "member"
    - buff_enable = passive_config[task_type].buff_enable
  ↓
  调用现有任务:
    - Orochi: runner.run() (会自动识别 user_status=member)
    - Exploration: runner.run_member()
    - WantedQuests: runner.run() (cooperation_only 模式)
  ↓
  恢复原始配置
  ↓
[4. 返回待命态]
  ↓
  更新 accept_counts
  记录 history
  回到步骤 1
```

### Module Boundaries

```
tasks/PassiveCooperationResponse/  (新增)
├── __init__.py
├── script_task.py              (主任务逻辑)
├── invite_detector.py          (邀请检测模块)
├── assets/                     (邀请弹窗识别资产)
└── config/
    └── passive_cooperation_response.yaml

module/config/
├── config_model.py             (新增 PassiveCooperationResponseConfig)
└── config_generated.py         (自动生成)

tasks/Orochi/script_task.py     (无修改，或极小修改)
tasks/Exploration/script_task.py (无修改，或极小修改)
tasks/WantedQuests/script_task.py (无修改)
```

---

## Implementation Phases

### Phase 1: 基础架构和御魂邀请 (MVP)

**目标**: 实现最小可验证原型，支持御魂邀请的检测、接受和执行

#### 1.1 配置模型 (Config Model)

**文件**: `module/config/config_model.py`

**新增配置类**:
```python
class PassiveTaskConfig(ConfigModel):
    enable: bool = Field(default=False)
    max_accept_count: int = Field(default=-1)  # -1 = unlimited
    allowed_inviters: List[str] = Field(default_factory=list)  # empty = all
    buff_enable: bool = Field(default=False)

class PassiveCooperationConfig(PassiveTaskConfig):
    allowed_cooperation_types: List[str] = Field(default_factory=lambda: ["jade", "cat_food", "dog_food"])

class PassiveCooperationResponseConfig(ConfigModel):
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    passive_config: PassiveConfigModel = Field(default_factory=PassiveConfigModel)

class PassiveConfigModel(ConfigModel):
    orochi: PassiveTaskConfig = Field(default_factory=PassiveTaskConfig)
    exploration: PassiveTaskConfig = Field(default_factory=PassiveTaskConfig)
    wanted_quests: PassiveCooperationConfig = Field(default_factory=PassiveCooperationConfig)

class Config:
    # 新增顶层配置
    passive_cooperation_response: PassiveCooperationResponseConfig = Field(...)
```

**风险**: 配置模型修改可能与 upstream 冲突
**缓解**: 
- 独立的配置块，不修改现有任务配置
- 配置文件向后兼容，未配置时使用默认值

#### 1.2 邀请检测模块 (Invite Detector)

**文件**: `tasks/PassiveCooperationResponse/invite_detector.py`

**职责**:
- 检测屏幕上的邀请弹窗
- OCR 解析邀请者昵称
- 根据上下文页面判断邀请类型

**接口**:
```python
class InviteDetector:
    def __init__(self, device):
        self.device = device
    
    def detect_invite(self) -> Optional[InviteInfo]:
        """
        检测当前屏幕是否有邀请弹窗
        Returns:
            InviteInfo if detected, None otherwise
        """
        # 检测通用邀请弹窗资产
        if not self.appear(INVITE_POPUP):
            return None
        
        # OCR 解析邀请者昵称
        inviter_name = self.ocr_inviter_name()
        
        # 根据上下文判断类型
        invite_type = self._infer_invite_type()
        
        return InviteInfo(
            task_type=invite_type,
            inviter_name=inviter_name,
            detected_at=datetime.now()
        )
    
    def _infer_invite_type(self) -> str:
        """根据当前页面上下文推断邀请类型"""
        current_page = self.ui_get_current_page()
        if current_page == page_soul_zones:
            return "orochi"
        elif current_page == page_exploration:
            return "exploration"
        elif self.appear(COOPERATION_INVITE_UNIQUE_ASSET):
            return "wanted_quests"
        else:
            logger.warning("Unknown invite type, context: %s", current_page)
            return "unknown"
    
    def accept_invite(self) -> bool:
        """点击接受邀请按钮"""
        return self.appear_then_click(INVITE_ACCEPT_BUTTON, interval=1)
```

**复用现有代码**:
- `module/base/base.py` 的 `appear()`, `ocr_*()` 方法
- `module/ui/ui.py` 的 `ui_get_current_page()`
- `tasks/*/assets/*.py` 的现有邀请弹窗资产（如 `GeneralInvite` 的资产）

**风险**: 邀请弹窗资产识别不准确
**缓解**: 
- 复用 `GeneralInvite` 已验证的资产
- 添加日志记录识别过程，便于调试

#### 1.3 主任务逻辑 (Script Task)

**文件**: `tasks/PassiveCooperationResponse/script_task.py`

**核心流程**:
```python
class ScriptTask(OasScriptTask):
    def __init__(self, config: Config, device):
        super().__init__(config, device)
        self.detector = InviteDetector(device)
        self.accept_counts = {"orochi": 0, "exploration": 0, "wanted_quests": 0}
    
    def run(self):
        logger.info("PassiveCooperationResponse: Start listening for invites")
        enabled_tasks = self._get_enabled_tasks()
        logger.info(f"Listening for: {', '.join(enabled_tasks)}")
        
        while True:
            self.screenshot()
            
            # 检测邀请
            invite = self.detector.detect_invite()
            if invite is None:
                sleep(1)  # 轮询间隔
                continue
            
            logger.info(f"Detected {invite.task_type} invite from {invite.inviter_name}")
            
            # 验证配置
            if not self._should_accept_invite(invite):
                logger.info(f"Rejected invite: {self._get_rejection_reason(invite)}")
                continue
            
            # 接受邀请
            if not self.detector.accept_invite():
                logger.warning("Failed to accept invite")
                continue
            
            # 执行对应任务
            success = self._execute_task(invite)
            
            # 更新状态
            if success:
                self.accept_counts[invite.task_type] += 1
                logger.info(f"Accepted {invite.task_type} invite ({self.accept_counts[invite.task_type]})")
            
            # 返回待命态
            self.ui_goto_main()
    
    def _should_accept_invite(self, invite: InviteInfo) -> bool:
        """验证是否应该接受邀请"""
        task_config = self.config.passive_cooperation_response.passive_config
        
        if invite.task_type == "orochi":
            cfg = task_config.orochi
        elif invite.task_type == "exploration":
            cfg = task_config.exploration
        elif invite.task_type == "wanted_quests":
            cfg = task_config.wanted_quests
        else:
            return False
        
        # 检查 enable
        if not cfg.enable:
            return False
        
        # 检查 max_accept_count
        if cfg.max_accept_count != -1 and self.accept_counts[invite.task_type] >= cfg.max_accept_count:
            return False
        
        # 检查 allowed_inviters
        if cfg.allowed_inviters and invite.inviter_name not in cfg.allowed_inviters:
            return False
        
        return True
    
    def _execute_task(self, invite: InviteInfo) -> bool:
        """执行对应任务的 member 模式"""
        try:
            if invite.task_type == "orochi":
                return self._execute_orochi_member(invite)
            elif invite.task_type == "exploration":
                return self._execute_exploration_member(invite)
            elif invite.task_type == "wanted_quests":
                return self._execute_cooperation_member(invite)
        except Exception as e:
            logger.exception(f"Failed to execute {invite.task_type}: {e}")
            return False
    
    def _execute_orochi_member(self, invite: InviteInfo) -> bool:
        """执行御魂 member 模式"""
        from tasks.Orochi.script_task import ScriptTask as OrochiTask
        
        # 保存原始配置
        original_user_status = self.config.orochi.orochi_config.user_status
        original_buff_enable = self.config.orochi.orochi_config.soul_buff_enable
        
        try:
            # 临时修改配置
            self.config.orochi.orochi_config.user_status = OrochiUserStatus.MEMBER
            passive_cfg = self.config.passive_cooperation_response.passive_config.orochi
            self.config.orochi.orochi_config.soul_buff_enable = passive_cfg.buff_enable
            
            # 调用现有 Orochi 任务
            runner = OrochiTask(self.config, self.device)
            
            # 拦截 set_next_run，避免污染 scheduler
            original_set_next_run = runner.set_next_run
            def capture_next_run(task, finish=False, success=None, server=True, target=None):
                logger.info(f"PassiveCooperationResponse: Captured Orochi next_run (ignored)")
                return
            runner.set_next_run = capture_next_run
            
            # 执行任务
            runner.run()  # Orochi.run() 会根据 user_status 自动选择 run_member()
            
            return True
        
        except TaskEnd:
            return True
        except RequestHumanTakeover:
            raise
        except Exception as e:
            logger.exception(e)
            return False
        finally:
            # 恢复原始配置
            self.config.orochi.orochi_config.user_status = original_user_status
            self.config.orochi.orochi_config.soul_buff_enable = original_buff_enable
```

**关键设计点**:
1. **配置隔离**: 临时修改 + finally 恢复，不影响普通任务
2. **拦截 set_next_run**: 避免污染普通任务的 scheduler
3. **复用现有任务**: 调用 `OrochiTask.run()`，依赖其内部 `user_status` 判断
4. **异常处理**: `TaskEnd` 视为成功，其他异常记录并返回失败

**风险**: 现有 `Orochi.run()` 可能不支持纯 member 模式
**缓解**: 
- 先验证现有代码是否支持 `user_status=member` 直接调用 `run()`
- 如不支持，调用 `run_member()` 方法（需确认接口）

#### 1.4 资产和配置文件

**文件**: `tasks/PassiveCooperationResponse/assets/*.py`

**复用现有资产**:
- `tasks/Orochi/assets/assets.py` 中的 `I_INVITE_*` 资产
- `module/ui/page.py` 中的页面定义

**新增资产** (如需要):
- `INVITE_POPUP`: 通用邀请弹窗检测框
- `INVITE_ACCEPT_BUTTON`: 接受按钮位置

**配置文件**: `tasks/PassiveCooperationResponse/config/passive_cooperation_response.yaml`

```yaml
PassiveCooperationResponse:
  scheduler:
    enable: false  # 默认关闭，用户手动启用
    priority: 999  # 高优先级，避免被其他任务阻塞
    next_run: "2026-01-01 00:00:00"
  
  passive_config:
    orochi:
      enable: false
      max_accept_count: -1
      allowed_inviters: []
      buff_enable: false
    
    exploration:
      enable: false
      max_accept_count: -1
      allowed_inviters: []
      buff_enable: false
    
    wanted_quests:
      enable: false
      max_accept_count: -1
      allowed_inviters: []
      allowed_cooperation_types:
        - jade
        - cat_food
        - dog_food
```

---

### Phase 2: 探索邀请支持

**目标**: 扩展 Phase 1 架构，支持探索邀请

#### 2.1 探索 member 模式验证

**前置工作**: 验证 `tasks/Exploration/script_task.py` 的 member 模式接口

**可能的接口形式**:
```python
# 形式 1: 根据 user_status 自动选择
runner = ExplorationTask(config, device)
config.exploration.exploration_config.user_status = "member"
runner.run()  # 内部判断 user_status

# 形式 2: 独立的 run_member() 方法
runner.run_member()
```

**风险**: 探索任务可能没有独立的 member 接口
**缓解**: 
- 如无接口，需添加最小化的适配代码（见下文）
- 优先使用现有流程，避免重写

#### 2.2 实现 `_execute_exploration_member()`

```python
def _execute_exploration_member(self, invite: InviteInfo) -> bool:
    """执行探索 member 模式"""
    from tasks.Exploration.script_task import ScriptTask as ExplorationTask
    
    original_user_status = self.config.exploration.exploration_config.user_status
    original_exp_enable = self.config.exploration.exploration_config.exp_enable
    
    try:
        # 临时修改配置
        self.config.exploration.exploration_config.user_status = "member"
        passive_cfg = self.config.passive_cooperation_response.passive_config.exploration
        self.config.exploration.exploration_config.exp_enable = passive_cfg.buff_enable
        
        runner = ExplorationTask(self.config, self.device)
        
        # 拦截 set_next_run
        original_set_next_run = runner.set_next_run
        def capture_next_run(task, finish=False, success=None, server=True, target=None):
            logger.info(f"PassiveCooperationResponse: Captured Exploration next_run (ignored)")
            return
        runner.set_next_run = capture_next_run
        
        # 执行
        runner.run()
        
        return True
    
    except TaskEnd:
        return True
    except Exception as e:
        logger.exception(e)
        return False
    finally:
        # 恢复配置
        self.config.exploration.exploration_config.user_status = original_user_status
        self.config.exploration.exploration_config.exp_enable = original_exp_enable
```

#### 2.3 探索邀请检测增强

**更新 `InviteDetector._infer_invite_type()`**:
- 添加探索邀请的独特资产识别
- 确保与御魂邀请区分清晰

---

### Phase 3: 协作邀请支持

**目标**: 支持 WantedQuests 协作邀请

#### 3.1 复用现有 `cooperation_only` 流程

**文件**: `tasks/WantedQuests/script_task.py`

**验证**:
- 确认 `wanted_quests_config.cooperation_only=true` 时的行为
- 确认是否可以通过临时修改配置来复用

#### 3.2 实现 `_execute_cooperation_member()`

```python
def _execute_cooperation_member(self, invite: InviteInfo) -> bool:
    """执行协作 member 模式"""
    from tasks.WantedQuests.script_task import ScriptTask as WantedQuestsTask
    
    original_cooperation_only = self.config.wanted_quests.wanted_quests_config.cooperation_only
    
    try:
        # 启用 cooperation_only 模式
        self.config.wanted_quests.wanted_quests_config.cooperation_only = True
        
        runner = WantedQuestsTask(self.config, self.device)
        
        # 拦截 set_next_run
        def capture_next_run(task, finish=False, success=None, server=True, target=None):
            logger.info(f"PassiveCooperationResponse: Captured WantedQuests next_run (ignored)")
            return
        runner.set_next_run = capture_next_run
        
        # 执行
        runner.run()
        
        return True
    
    except TaskEnd:
        return True
    except Exception as e:
        logger.exception(e)
        return False
    finally:
        # 恢复配置
        self.config.wanted_quests.wanted_quests_config.cooperation_only = original_cooperation_only
```

---

### Phase 4: 加成管理增强

**目标**: 确保加成状态检测和自动开启逻辑可靠

#### 4.1 加成状态检测

**在 `_execute_orochi_member()` 和 `_execute_exploration_member()` 中插入加成管理逻辑**:

```python
def _ensure_buff_enabled(self, buff_type: str, buff_enable: bool):
    """确保加成开启（如果配置要求）"""
    if not buff_enable:
        logger.info(f"{buff_type} buff not required by config")
        return
    
    # 检测当前加成状态
    if buff_type == "orochi":
        buff_button = I_OROCHI_BUFF
        buff_indicator = I_OROCHI_BUFF_ACTIVE
    elif buff_type == "exploration":
        buff_button = I_EXPLORATION_EXP_BUFF
        buff_indicator = I_EXPLORATION_EXP_BUFF_ACTIVE
    else:
        return
    
    self.screenshot()
    
    # 检查是否已开启
    if self.appear(buff_indicator):
        logger.info(f"{buff_type} buff already enabled")
        return
    
    # 点击开启
    if self.appear_then_click(buff_button, interval=1):
        logger.info(f"{buff_type} buff enabled")
        sleep(0.5)
        self.screenshot()
        
        # 验证是否开启成功
        if self.appear(buff_indicator):
            logger.info(f"{buff_type} buff enabled successfully")
        else:
            logger.warning(f"{buff_type} buff may be insufficient or not enabled")
    else:
        logger.warning(f"Failed to find {buff_type} buff button")
```

**调用时机**:
- 御魂：接受邀请后，进入组队界面时
- 探索：接受邀请后，进入探索准备界面时

#### 4.2 加成资产准备

**复用现有资产**:
- `tasks/Orochi/assets/assets.py` 中的御魂加成按钮和指示器
- `tasks/Exploration/assets/assets.py` 中的经验加成资产

**风险**: 加成状态识别可能不准确
**缓解**: 
- 添加详细日志
- 即使识别失败也继续执行，不阻塞流程

---

## Risk Mitigation

### 风险 1: 现有任务 member 模式接口不完整

**症状**: 调用 `runner.run()` 时，member 模式未正确执行

**缓解方案**:
1. **优先验证**: 在实现前先阅读 `Orochi/Exploration/WantedQuests` 的 `run()` 和 `run_member()` 方法
2. **最小化适配**: 如需修改现有任务，只添加 `if user_status == "member"` 分支，不改变现有逻辑
3. **文档记录**: 如果添加了适配代码，记录在 `plan.md` 中，标注为"Upstream compatibility patch"

### 风险 2: 配置模型冲突

**症状**: Upstream 更新了配置结构，导致合并冲突

**缓解方案**:
1. **独立配置块**: `passive_cooperation_response` 是顶层独立配置，不修改现有任务配置
2. **向后兼容**: 所有新配置字段提供默认值
3. **配置迁移指南**: 提供从 `cooperation_only` 迁移到 `passive_cooperation_response` 的文档

### 风险 3: 邀请检测误识别

**症状**: 检测到非目标邀请，或漏检真实邀请

**缓解方案**:
1. **复用成熟资产**: 优先使用 `GeneralInvite` 已验证的资产
2. **白名单机制**: `allowed_inviters` 过滤非目标邀请
3. **详细日志**: 记录每次检测的 OCR 结果和上下文页面
4. **用户反馈**: 提供配置选项调整检测灵敏度

### 风险 4: 多轮邀请大号不响应

**症状**: 小号发起第二次邀请，大号未检测到

**根本原因**: 大号 member 任务完成后返回主界面，但 `PassiveCooperationResponse` 的轮询循环可能正在执行其他逻辑

**缓解方案**:
1. **快速返回待命态**: 任务完成后立即 `ui_goto_main()` 并恢复轮询
2. **缩短轮询间隔**: 从 1 秒缩短到 0.5 秒（需权衡性能）
3. **日志分析**: 记录邀请检测的时间戳，分析漏检原因

---

## Testing Strategy

### 单元测试 (Phase 1)

**测试内容**:
- `InviteDetector.detect_invite()` 在不同上下文页面的识别准确性
- `_should_accept_invite()` 的白名单和次数限制逻辑
- 配置模型的序列化和反序列化

**测试方法**:
- Mock `self.appear()` 和 `self.ocr_*()` 返回值
- 准备不同的邀请场景（不同邀请者、不同类型）

### 集成测试 (Phase 1-3)

**测试内容**:
- 御魂邀请端到端流程（检测 → 接受 → 执行 → 返回）
- 探索邀请端到端流程
- 协作邀请端到端流程
- 多轮邀请响应

**测试环境**:
- 双实例（大号 + 小号）
- 小号发起邀请，大号被动响应

### 实机验证 (Phase 4)

**验证场景**:
- 御魂加成自动开启
- 探索经验加成自动开启
- 次数限制生效
- 白名单过滤生效
- 普通任务 scheduler 未被污染

**验证方法**:
- 参考 `SubAccountRotation` 的实机验证流程
- 准备验证脚本（类似 `scripts/verify_*.sh`）

---

## Upstream Compatibility Checklist

在每个 Phase 完成后，检查以下项目：

- [ ] **无现有文件修改**: 除了 `module/config/config_model.py`，没有修改任何现有任务文件
- [ ] **配置向后兼容**: 新配置字段有默认值，不影响未配置用户
- [ ] **资产复用**: 优先复用现有资产，新增资产放在独立目录
- [ ] **日志清晰**: 新增日志明确标注 `PassiveCooperationResponse`，不与现有任务混淆
- [ ] **异常处理**: 不改变现有任务的异常处理行为
- [ ] **文档更新**: 更新 `CLAUDE.md` 或 `AGENTS.md`，说明新功能不影响现有功能

---

## Delivery Timeline

| Phase | 预计工作量 | 依赖 | 产出 |
|---|---|---|---|
| Phase 1: 基础架构和御魂邀请 | 3-4 天 | 无 | MVP: 御魂邀请检测和执行 |
| Phase 2: 探索邀请支持 | 1-2 天 | Phase 1 | 探索邀请端到端流程 |
| Phase 3: 协作邀请支持 | 1-2 天 | Phase 1 | 协作邀请端到端流程 |
| Phase 4: 加成管理增强 | 1 天 | Phase 1, 2 | 加成自动管理验证通过 |
| **总计** | **6-9 天** | | 完整功能 + 实机验证 |

---

## Implementation Research Results (2026-06-13)

### ✅ Orochi member 模式接口

**源码**: `tasks/Orochi/script_task.py`

**调用方式**:
```python
# run() 方法根据 user_status 自动分发
def run(self):
    # ... 前置处理（御魂切换、加成开启）
    match config.orochi_config.user_status:
        case UserStatus.LEADER: success = self.run_leader()
        case UserStatus.MEMBER: success = self.run_member()  # 自动调用
        case UserStatus.ALONE: self.run_alone()
        case UserStatus.WILD: success = self.run_wild()
    # ... 后置处理（加成关闭、set_next_run）
    raise TaskEnd
```

**run_member() 行为**:
- 不需要进入御魂界面（注释掉了 `ui_goto(page_soul_zones)` 和 `orochi_enter()`）
- 直接进入等待邀请循环：`check_then_accept()` → `wait_battle()` → `run_general_battle()`
- 根据 `limit_count` 和 `limit_time` 控制接受次数
- 完成后返回 `True`

**结论**: 
✅ **方式 A 可行**：设置 `user_status=member` 后调用 `run()`，会自动进入 `run_member()` 流程
⚠️ **前置处理问题**：`run()` 会执行御魂切换和加成开启逻辑，但 member 不需要这些
⚠️ **后置处理问题**：`run()` 会调用 `set_next_run()`，需要拦截

**推荐方案**: 临时设置 `user_status=member` + 拦截 `set_next_run`，调用 `run()`

---

### ✅ Exploration member 模式接口

**源码**: `tasks/Exploration/solo.py`

**调用方式**:
```python
# run() 方法根据 user_status 分发
def run(self):
    match self._config.exploration_config.user_status:
        case 'leader':
            self.run_leader()
        case 'member':
            self.run_member()
```

**run_member() 行为**:
- 不需要进入探索界面（由 leader 发起）
- 等待邀请并接受：`check_then_accept()` → 进入战斗
- 处理探索战斗场景（BATTLE, BOSS, etc.）
- 完成后退出

**结论**: 
✅ **方式 A 可行**：设置 `user_status=member` 后调用 `run()`，会自动进入 `run_member()` 流程
⚠️ **加成管理**: 需要确认探索经验加成在哪里开启（可能在 `run()` 前置处理中）

**推荐方案**: 临时设置 `user_status=member` + 拦截 `set_next_run`，调用 `run()`

---

### ✅ WantedQuests cooperation_only 模式

**源码**: `tasks/WantedQuests/script_task.py`

**调用方式**:
```python
# run() 方法检查 cooperation_only
if (self.get_config()).cooperation_only:
    preSuc = self.pre_work_cooperation_only()
```

**pre_work_cooperation_only() 行为**:
- 打开悬赏封印界面
- 检查是否有协作邀请（`I_WQ_INVITE_1/2/3`）
- 如果没有协作邀请，返回 `False` 并退出
- 如果有协作邀请，进入协作流程

**结论**: 
✅ **cooperation_only 模式已存在**：设置 `cooperation_only=True` 后调用 `run()`，会进入纯协作模式
⚠️ **需要确认**: 协作完成后是否会调用 `set_next_run()`（需要拦截）

**推荐方案**: 临时设置 `cooperation_only=True` + 拦截 `set_next_run`，调用 `run()`

---

### ✅ 加成管理机制

**源码**: `tasks/Component/GeneralBuff/general_buff.py`

#### 御魂加成

**调用流程**:
```python
# 在 Orochi.run() 中
if config.orochi_config.soul_buff_enable:
    self.open_buff()           # 打开加成界面
    self.soul(is_open=True)    # 开启御魂加成
    self.close_buff()          # 关闭加成界面

# 任务完成后关闭
if config.orochi_config.soul_buff_enable:
    self.open_buff()
    self.soul(is_open=False)   # 关闭御魂加成
    self.close_buff()
```

**soul() 方法行为**:
- 检测御魂加成按钮位置（`I_SOUL` 图像识别）
- 检查当前开关状态：
  - `I_OPEN_YELLOW`: 加成已开启（黄色开关）
  - `I_CLOSE_RED`: 加成已关闭（红色开关）
- 根据 `is_open` 参数点击切换
- 循环直到状态正确

**资产**:
- `I_SOUL`: 御魂加成图标（用于定位）
- `I_OPEN_YELLOW`: 黄色开关（表示已开启）
- `I_CLOSE_RED`: 红色开关（表示已关闭）

#### 探索经验加成

**源码**: `tasks/Exploration/base.py`

**调用流程**:
```python
# 在探索预处理中
con = self.config.exploration.exploration_config
if con.buff_exp_50_click or con.buff_exp_100_click:
    self.ui_goto(page_main)
    self.open_buff()
    if con.buff_exp_50_click:
        self.exp_50()          # 50%经验加成
    if con.buff_exp_100_click:
        self.exp_100()         # 100%经验加成
    self.close_buff()
```

**结论**:
✅ **加成管理已封装**：`GeneralBuff` 提供了统一的加成管理接口
✅ **状态检测完善**：通过 `I_OPEN_YELLOW` 和 `I_CLOSE_RED` 检测开关状态，避免重复点击
✅ **独立控制**：可以在被动响应任务中独立调用 `open_buff()` + `soul()/exp_50()` + `close_buff()`

**被动响应任务加成管理方案**:
```python
# 在 _execute_orochi_member() 中
if passive_cfg.buff_enable:
    self.open_buff()
    self.soul(is_open=True)
    self.close_buff()

# 执行御魂 member 流程
runner.run()

# 任务完成后关闭（可选）
if passive_cfg.buff_enable:
    self.open_buff()
    self.soul(is_open=False)
    self.close_buff()
```

---

### 🔍 加成管理调研（待补充）

**需要确认**:
1. ~~御魂加成在 `run()` 的哪个位置开启？~~ ✅ 已确认
   - 在 `run()` 开始时开启，结束时关闭
   - 通过 `GeneralBuff.soul(is_open)` 方法控制
2. ~~探索经验加成在哪里开启？~~ ✅ 已确认
   - 在探索预处理 `pre_process()` 中开启
   - 通过 `GeneralBuff.exp_50()` / `exp_100()` 方法控制

---

### 📋 待解决问题

1. **加成状态指示器资产**: 需要在 `tasks/Orochi/assets/` 和 `tasks/Exploration/assets/` 中查找加成相关资产
2. **邀请弹窗超时处理**: 建议固定 90 秒（与现有 `wait_time` 配置对齐），轮询间隔 1 秒
3. **加成开启时机**: 需要确认是否可以在 member 流程中独立控制加成（不依赖 `run()` 前置处理）

---

**Status**: Ready for implementation (Phase 1)
**Next**: 创建 `tasks.md`，细化 Phase 1 的实现任务
