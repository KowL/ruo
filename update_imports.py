#!/usr/bin/env python3
"""
批量更新导入路径脚本
Update Import Paths Script
"""
import os
import re
from pathlib import Path

# 定义导入路径映射
IMPORT_MAPPINGS = {
    r'from agent\.': 'from app.llm_agent.agents.',
    r'from tools\.': 'from app.services.',
    r'from graph\.': 'from app.llm_agent.graphs.',
    r'from utils\.': 'from app.core.',
    r'from state\.': 'from app.llm_agent.state.',
    r'import agent\.': 'import app.llm_agent.agents.',
    r'import tools\.': 'import app.services.',
    r'import graph\.': 'import app.llm_agent.graphs.',
    r'import utils\.': 'import app.core.',
    r'import state\.': 'import app.llm_agent.state.',
}

def update_imports_in_file(file_path: Path) -> int:
    """更新单个文件中的导入语句"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        changes = 0

        # 应用所有映射
        for old_pattern, new_pattern in IMPORT_MAPPINGS.items():
            new_content, count = re.subn(old_pattern, new_pattern, content)
            content = new_content
            changes += count

        # 如果有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 更新: {file_path} ({changes} 处修改)")
            return changes

        return 0
    except Exception as e:
        print(f"❌ 错误: {file_path} - {e}")
        return 0

def main():
    """主函数"""
    backend_dir = Path('backend/app')
    total_changes = 0
    files_updated = 0

    # 遍历所有 Python 文件
    for py_file in backend_dir.rglob('*.py'):
        changes = update_imports_in_file(py_file)
        if changes > 0:
            total_changes += changes
            files_updated += 1

    print(f"\n📊 更新完成:")
    print(f"   - 文件数: {files_updated}")
    print(f"   - 总修改数: {total_changes}")

if __name__ == '__main__':
    main()
