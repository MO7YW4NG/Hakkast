from pathlib import Path
import sys
import os

# 模擬 config.py 的路徑計算
config_file = Path("c:/Users/yuniverse30/Hakkast/backend/app/core/config.py")
env_path = config_file.parent.parent.parent / ".env"

print(f"Config 文件位置: {config_file}")
print(f"計算的 .env 路徑: {env_path}")
print(f".env 文件是否存在: {env_path.exists()}")

# 檢查所有可能的 .env 文件
possible_paths = [
    Path("c:/Users/yuniverse30/Hakkast/.env"),
    Path("c:/Users/yuniverse30/Hakkast/backend/.env"),
    env_path
]

print("\n所有可能的 .env 文件:")
for path in possible_paths:
    exists = "✅ 存在" if path.exists() else "❌ 不存在"
    print(f"  {path}: {exists}")
