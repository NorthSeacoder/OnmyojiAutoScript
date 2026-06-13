#!/bin/bash
# Verification script for AreaBoss adapter
# Usage on Windows (Git Bash or WSL): bash scripts/verify_area_boss.sh
# Note: Sync this script to Windows before running

set -e

CONFIG_FILE="config/oas_findjade.json"
BACKUP_FILE="config/oas_findjade.before_area_boss_verification.json"

echo "=== AreaBoss Verification ==="
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Environment: Windows (C:\Users\64638\OnmyojiAutoScript)"
echo ""

# Check time window
current_hour=$(date '+%H')
if [ "$current_hour" -lt 6 ]; then
  echo "❌ AreaBoss time window check failed"
  echo "   Current time: $(date '+%H:%M:%S')"
  echo "   Valid window: 06:00-24:00"
  echo "   Please run this script after 06:00"
  exit 1
fi

echo "✓ Time window check passed (current: ${current_hour}:xx, valid: 06:00-24:00)"
echo ""

# Backup config
echo "1. Backing up config..."
cp "$CONFIG_FILE" "$BACKUP_FILE"
echo "   Backup saved to: $BACKUP_FILE"
echo ""

# Configure SubAccountRotation with AreaBoss only
echo "2. Configuring SubAccountRotation..."
python scripts/configure_subaccount_rotation.py \
  --config "$CONFIG_FILE" \
  --sub-task AreaBoss \
  --max-accounts-per-run 1 \
  --enable \
  --run-now \
  --disable-find-jade

echo ""
echo "=== Configuration Applied ==="
echo "SubAccountRotation:"
echo "  - enabled_sub_tasks: AreaBoss"
echo "  - max_accounts_per_run: 1"
echo "  - scheduler.enable: true"
echo "  - scheduler.next_run: now"
echo ""
echo "FindJade: disabled (to avoid interference)"
echo ""

# Verification checklist
cat <<EOF
=== Verification Checklist ===

Before running:
  [ ] Connected via SSH to Windows PC (ssh win)
  [ ] Main account emulator ready (127.0.0.1:5555)
  [ ] Small account emulator ready (127.0.0.1:5557)
  [ ] Main account logged in and idle
  [ ] Time window: 06:00-24:00 ✓
  [ ] AreaBoss tickets available for small account

Expected behavior:
  1. SubAccountRotation starts
  2. Switch to small account (最后的黄泉 or 破晓的森林)
  3. Enter AreaBoss (地域鬼王/封魔之时)
  4. AreaBoss task forces lock_team_enable = False (upstream behavior)
  5. Complete AreaBoss battle
  6. Log: "SubAccountRotation captured AreaBoss next_run"
  7. Config restoration: area_boss.general_battle.lock_team_enable restored to original value
  8. SubAccountRotation ends

Critical validation (Issue #1 fix):
  - Verify lock_team_enable is restored even when TaskEnd is raised
  - Check that original lock_team_enable value is preserved after run

After running:
  [ ] Check log: "SubAccountRotation captured AreaBoss next_run"
  [ ] Verify area_boss.scheduler.next_run unchanged in config
  [ ] Verify area_boss.general_battle.lock_team_enable restored to original value
  [ ] Check sub_account_rotation.history_list for new AreaBoss entry
  [ ] Record timestamp, success/failure, and any errors in acceptance.md

To restore config:
  cp "$BACKUP_FILE" "$CONFIG_FILE"

To run OAS server:
  venv\Scripts\python.exe server.py --host 0.0.0.0 --port 22270

EOF

echo "=== Ready to Run ==="
echo "Start OAS with config: $CONFIG_FILE"
echo ""
