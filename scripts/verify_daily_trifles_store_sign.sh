#!/bin/bash
# Verification script for DailyTriflesStoreSign adapter
# Usage: bash scripts/verify_daily_trifles_store_sign.sh

set -e

CONFIG_FILE="config/oas_findjade.json"
BACKUP_FILE="config/oas_findjade.before_store_sign_verification.json"

echo "=== DailyTriflesStoreSign Verification ==="
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Backup config
echo "1. Backing up config..."
cp "$CONFIG_FILE" "$BACKUP_FILE"
echo "   Backup saved to: $BACKUP_FILE"
echo ""

# Configure SubAccountRotation with DailyTriflesStoreSign only
echo "2. Configuring SubAccountRotation..."
python scripts/configure_subaccount_rotation.py \
  --config "$CONFIG_FILE" \
  --sub-task DailyTriflesStoreSign \
  --max-accounts-per-run 1 \
  --enable \
  --run-now \
  --disable-find-jade

echo ""
echo "=== Configuration Applied ==="
echo "SubAccountRotation:"
echo "  - enabled_sub_tasks: DailyTriflesStoreSign"
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
  [ ] Main account is logged in and idle
  [ ] Small account emulator is ready (127.0.0.1:5557 or configured adb)
  [ ] Check that daily store gift is available (not already claimed today)

Expected behavior:
  1. SubAccountRotation starts
  2. Switch to small account (最后的黄泉 or 破晓的森林)
  3. Enter game → shop → daily gift room
  4. Claim daily gift package (50-day black daruma progress)
  5. Log: "SubAccountRotation completed DailyTriflesStoreSign for <account>"
  6. SubAccountRotation ends
  7. DailyTrifles scheduler remains unchanged (verify next_run not modified)

After running:
  [ ] Check log: "SubAccountRotation captured DailyTrifles next_run"
  [ ] Verify daily_trifles.scheduler.next_run unchanged in config
  [ ] Verify store_sign and buy_sushi_count restored to original values
  [ ] Check sub_account_rotation.history_list for new DailyTriflesStoreSign entry

To restore config:
  cp "$BACKUP_FILE" "$CONFIG_FILE"

EOF

echo "=== Ready to Run ==="
echo "Start OAS with config: $CONFIG_FILE"
echo ""
