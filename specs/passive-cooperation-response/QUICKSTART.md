# PassiveCooperationResponse 实机验证指南

**验证时间**: 2026-06-14  
**状态**: 准备就绪

---

## 快速启动步骤

### 1. 准备配置文件

#### 大号配置（被动接受邀请方）

运行以下命令为你的大号配置启用被动响应：

```bash
# 方式 1: 使用配置脚本（推荐）
python3 scripts/enable_passive_response.py <你的大号配置名> --enable-orochi --buff

# 方式 2: 手动修改配置文件
# 编辑 config/<你的大号配置名>.json，添加或修改：
```

```json
{
  "passive_cooperation_response": {
    "scheduler": {
      "enable": true,
      "priority": 999,
      "next_run": "2023-01-01 00:00:00"
    },
    "passive_config": {
      "orochi": {
        "enable": true,
        "max_accept_count": -1,
        "allowed_inviters": [],
        "buff_enable": true
      }
    }
  }
}
```

#### 小号配置（发起邀请方）

确保小号已配置 SubAccountRotation + Orochi：

```json
{
  "sub_account_rotation": {
    "scheduler": {
      "enable": true,
      "priority": 10,
      "next_run": "2023-01-01 00:00:00"
    },
    "rotation_config": {
      "enabled_sub_tasks": ["Orochi"]
    }
  },
  "orochi": {
    "scheduler": {
      "enable": false"
    },
    "orochi_config": {
      "user_status": "leader",
      "limit_count": 3,
      "soul_buff_enable": false,
      "friend_1": "<大号昵称>"
    }
  }
}
```

---

### 2. 启动顺序

1. **先启动大号** OAS：
   ```bash
   # 在大号 OAS 窗口
   python main.py
   # 或使用你的启动方式
   ```

2. **观察大号日志**，确认看到：
   ```
   PassiveCooperationResponse: Start listening for invites
   Listening for: orochi
   ```

3. **再启动小号** OAS：
   ```bash
   # 在小号 OAS 窗口
   python main.py
   ```

4. **等待小号发起邀请**，观察两边日志

---

### 3. 关键日志检查点

#### 大号应该看到的日志：

**检测阶段**:
```
Detected invite popup
Current page for invite inference: [page_name]
Invite detected: type=orochi, inviter=Unknown
Detected orochi invite from Unknown
```

**验证阶段**:
```
Accepting orochi invite from Unknown
```

**接受阶段**:
```
Attempting to accept invite
Clicked accept button
Successfully entered room
```

**执行阶段**:
```
Executing orochi member mode
Orochi member mode: user_status=MEMBER, buff_enable=True
PassiveCooperationResponse captured Orochi set_next_run (ignored)
```

**完成阶段**:
```
Orochi member execution completed successfully
Completed orochi invite (total: 1)
Returning to standby state
Orochi config restored: user_status=leader, buff_enable=False
```

#### 小号应该看到的日志：

```
SubAccountRotation: Executing Orochi sub-task
SubAccountRotation: Orochi invite sent
SubAccountRotation captured Orochi next_run success=False
```

---

### 4. 验证检查清单

**Scenario 1: 单次邀请流程**
- [ ] 大号检测到邀请（日志出现 "Detected orochi invite"）
- [ ] 大号接受邀请（日志出现 "Successfully entered room"）
- [ ] 大号进入战斗并完成
- [ ] 大号战斗后返回主界面（日志出现 "Returning to standby state"）
- [ ] 大号继续监听（没有退出或报错）
- [ ] 配置恢复成功（日志出现 "Orochi config restored"）

**Scenario 6: Scheduler 非污染**
- [ ] 大号 `config/<配置名>.json` 中 `orochi.scheduler.next_run` 未改变
- [ ] 日志出现 "PassiveCooperationResponse captured Orochi set_next_run (ignored)"

**Scenario 2: Buff 管理**
- [ ] 大号游戏画面中御魂加成图标显示为已激活
- [ ] 日志出现 "buff_enable=True"

---

### 5. 常见问题排查

#### 问题 1: 大号检测不到邀请

**可能原因**:
- 资产识别失败
- 邀请弹窗未出现

**排查步骤**:
1. 手动触发一次邀请，观察游戏画面
2. 检查日志是否有 "Detected invite popup"
3. 如果没有，可能是资产不匹配（需要重新截图）

#### 问题 2: 大号检测到但不接受

**可能原因**:
- 验证逻辑拒绝

**排查步骤**:
1. 检查日志中的 "Rejected invite: [reason]"
2. 确认 `passive_config.orochi.enable = true`
3. 确认 `max_accept_count` 未达到限制

#### 问题 3: 大号接受失败

**可能原因**:
- 接受按钮点击失败
- 超时

**排查步骤**:
1. 检查日志 "Clicked accept button" 是否出现
2. 检查日志 "Failed to accept invite after 10 attempts"
3. 手动测试：在邀请弹窗出现时手动点击接受

#### 问题 4: 战斗中断或配置未恢复

**可能原因**:
- 异常未捕获
- finally 块未执行

**排查步骤**:
1. 查看完整异常堆栈
2. 检查日志最后是否有 "Orochi config restored"
3. 验证配置文件中的 `user_status` 值

---

### 6. 成功标志

如果看到以下日志序列，说明基础流程成功：

```
✅ PassiveCooperationResponse: Start listening for invites
✅ Detected orochi invite from Unknown
✅ Accepting orochi invite from Unknown
✅ Successfully entered room
✅ Executing orochi member mode
✅ PassiveCooperationResponse captured Orochi set_next_run (ignored)
✅ Orochi member execution completed successfully
✅ Completed orochi invite (total: 1)
✅ Orochi config restored: user_status=leader, buff_enable=False
✅ Returning to standby state
```

---

## 下一步

**验证成功后**:
1. 在 `specs/passive-cooperation-response/acceptance.md` 记录结果
2. 运行多轮测试（Scenario 3）
3. 测试次数限制（Scenario 4）
4. 测试白名单过滤（Scenario 5）

**验证失败**:
1. 记录错误日志
2. 分析根本原因
3. 修复代码
4. 重新测试

---

## 需要帮助？

如果遇到问题，提供以下信息：
1. 完整日志输出（大号 + 小号）
2. 配置文件内容
3. 错误发生时的游戏截图
4. 期望行为 vs 实际行为

祝测试顺利！🚀
