"""
批量文献拆分模块
将用户粘贴的一大段参考文献文本，拆分成单条文献列表
"""

import re


def split_references(text: str) -> list[str]:
    """
    将多条参考文献文本拆分为单条列表。
    支持的格式：
    1. 每行一条（最常见）
    2. [1] [2] ... 编号开头
    3. 1. 2. 3. 数字+点号开头
    """
    lines = text.strip().splitlines()

    # 先过滤空行，合并被意外换行打断的同一条文献
    merged = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # 如果这行以编号开头（如 [1] 或 1. 或 (1)），视为新的一条
        if re.match(r'^\s*(\[\d+\]|\(\d+\)|\d+[.)、])\s*', stripped):
            merged.append(stripped)
        # 否则如果上一行存在且当前行不像新条目，拼接到上一行
        elif merged and not _looks_like_new_entry(stripped):
            merged[-1] += ' ' + stripped
        else:
            merged.append(stripped)

    # 清理每条文献的编号前缀
    results = []
    for item in merged:
        cleaned = re.sub(r'^\s*(\[\d+\]|\(\d+\)|\d+[.)、])\s*', '', item).strip()
        if cleaned:
            results.append(cleaned)

    return results


def _looks_like_new_entry(line: str) -> bool:
    """判断一行文本是否看起来像一条新的参考文献的开头"""
    # 以大写字母开头（英文作者姓），或以中文字符开头（中文作者）
    if re.match(r'^[A-Z\u4e00-\u9fff]', line):
        return True
    return False
