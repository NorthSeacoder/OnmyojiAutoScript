#!/usr/bin/env python3
"""Fix orochi layer configuration for SubAccountRotation verification"""

import json
from pathlib import Path

def main():
    config_path = Path("config/oas_findjade.json")

    print(f"Reading {config_path}...")
    with config_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Check current value
    current_layer = data["orochi"]["orochi_config"]["layer"]
    print(f"Current layer: {current_layer}")

    # Fix layer value
    if current_layer != "拾层":
        data["orochi"]["orochi_config"]["layer"] = "拾层"
        print("Fixing layer: 魂十 -> 拾层")

        # Write back
        with config_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Verify
        with config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"Verified layer: {data['orochi']['orochi_config']['layer']}")
    else:
        print("Layer already correct, no changes needed")

    print("\nCurrent Orochi configuration:")
    print(f"  soul_zones_type: {data['orochi']['orochi_config']['soul_zones_type']}")
    print(f"  layer: {data['orochi']['orochi_config']['layer']}")
    print(f"  friend_1: {data['orochi']['invite_config']['friend_1']}")

if __name__ == "__main__":
    main()
