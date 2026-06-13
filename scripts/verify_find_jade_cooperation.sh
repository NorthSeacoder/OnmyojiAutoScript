#!/bin/bash
# Verification script for FindJade cooperation path
# Usage on Windows (Git Bash or WSL): bash scripts/verify_find_jade_cooperation.sh
# Note: Sync this script to Windows before running

set -e

MAIN_CONFIG="config/oas_main.json"
SMALL_CONFIG="config/oas_findjade.json"
MAIN_BACKUP="config/oas_main.before_cooperation_verification.json"
SMALL_BACKUP="config/oas_findjade.before_cooperation_verification.json"

echo "=== FindJade Cooperation Path Verification ==="
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Environment: Windows (C:\Users\64638\OnmyojiAutoScript)"
echo ""

# Backup configs
echo "1. Backing up configs..."
cp "$MAIN_CONFIG" "$MAIN_BACKUP"
cp "$SMALL_CONFIG" "$SMALL_BACKUP"
echo "   Main config backup: $MAIN_BACKUP"
echo "   Small config backup: $SMALL_BACKUP"
echo ""

# Configure main account for cooperation_only mode
echo "2. Configuring main account WantedQuests (cooperation_only)..."
python scripts/check_wanted_quests_main.py --config "$MAIN_CONFIG" --fix

# Manually set cooperation_only (add this feature to helper script later)
cat <<EOF

Manual step required:
Edit $MAIN_CONFIG and set:
  "wanted_quests": {
    "wanted_quests_config": {
      "cooperation_only": true
    },
    "scheduler": {
      "enable": true
    }
  }

This allows main account to accept cooperation invites without searching its own quests.

EOF

# Configure small account with FindJade sub-task
echo "3. Configuring SubAccountRotation with FindJade..."
python scripts/configure_subaccount_rotation.py \
  --config "$SMALL_CONFIG" \
  --sub-task FindJade \
  --max-accounts-per-run 1 \
  --enable \
  --run-now \
  --disable-find-jade

echo ""
echo "=== Configuration Applied ==="
echo "Main account ($MAIN_CONFIG):"
echo "  - wanted_quests.scheduler.enable: true"
echo "  - wanted_quests.wanted_quests_config.cooperation_only: true (manual)"
echo ""
echo "Small account ($SMALL_CONFIG):"
echo "  - SubAccountRotation.enabled_sub_tasks: FindJade"
echo "  - SubAccountRotation.max_accounts_per_run: 1"
echo "  - FindJade: disabled (to avoid old loop)"
echo ""

# Verification checklist
cat <<EOF
=== Verification Checklist ===

Before running:
  [ ] Connected via SSH to Windows PC (ssh win)
  [ ] Main account emulator ready (127.0.0.1:5555) and logged in
  [ ] Small account emulator ready (127.0.0.1:5557)
  [ ] Main config has cooperation_only=true set manually
  [ ] Small account has cooperation quests available (jade/cat food/dog food)

Expected behavior:
  1. Small account: SubAccountRotation starts
  2. Small account: Switch to small account
  3. Small account: Enter WantedQuests, find cooperation quest
  4. Small account: Send cooperation invite to main account (不知庭院)
  5. Main account: Accept cooperation popup
  6. Main account: BaseTask._burst() triggers WantedQuests immediately
  7. Main account: WantedQuests runs in cooperation_only mode
  8. Both accounts: Complete cooperation battle
  9. Small account: Log "SubAccountRotation captured WantedQuests next_run"
  10. SubAccountRotation ends

Critical validation (Issue #2 fix):
  - Verify WantedQuests.set_next_run is intercepted by SubAccountRotation
  - Verify main WantedQuests scheduler not modified by small account run
  - Verify FindJade history updated for small account

After running:
  [ ] Check small log: "SubAccountRotation captured WantedQuests next_run from FindJade"
  [ ] Verify wanted_quests.scheduler.next_run unchanged in main config
  [ ] Check sub_account_rotation.history_list for new FindJade entry in small config
  [ ] Record timestamp, success/failure, and any errors in acceptance.md

To restore configs:
  cp "$MAIN_BACKUP" "$MAIN_CONFIG"
  cp "$SMALL_BACKUP" "$SMALL_CONFIG"

To run OAS:
  Main: venv\Scripts\python.exe server.py --config oas_main --host 0.0.0.0 --port 22270
  Small: venv\Scripts\python.exe server.py --config oas_findjade --host 0.0.0.0 --port 22271

EOF

echo "=== Ready to Run ==="
echo "After manual cooperation_only setup, start both OAS instances"
echo ""
