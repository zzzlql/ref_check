"""
文献真伪验证模块
通过 CrossRef API 检索文献，判断是否真实存在
CrossRef 是免费开放的学术元数据 API，无需注册即可使用
"""

import re
import unicodedata
from difflib import SequenceMatcher
from dataclasses import dataclass
from typing import Optional

import requests
from .parser import Reference


# CrossRef API 基础地址
CROSSREF_API = "https://api.crossref.org/works"

# 请求超时（秒）
TIMEOUT = 15

# 相似度阈值：低于此值判定为「可能虚假」
# 0.70 能有效区分「关键词部分重叠的假文献」和真实匹配
SIMILARITY_THRESHOLD = 0.70

# 英文停用词
STOP_WORDS_EN = {
    'a', 'an', 'the', 'of', 'in', 'on', 'at', 'to', 'for', 'and', 'or',
    'is', 'are', 'was', 'were', 'with', 'by', 'from', 'as', 'its', 'that',
    'this', 'it', 'be', 'has', 'have', 'had', 'not', 'but', 'which', 'their',
    'we', 'our', 'can', 'using', 'based', 'via', 'into', 'between', 'about',
}

# 中文停用词（学术文献中的高频虚词）
STOP_WORDS_ZH = {
    '的', '了', '在', '是', '与', '及', '和', '对', '从', '为', '以',
    '中', '上', '下', '其', '被', '所', '之', '而', '或', '等', '也',
    '一种', '一个', '进行', '通过', '提出', '本文', '研究',
}


# 三级判定状态
STATUS_REAL = "real"          # 真实文献
STATUS_SUSPICIOUS = "suspicious"  # 可疑（大概率虚假）
STATUS_UNCERTAIN = "uncertain"    # 不确定（需人工确认，常见于中文文献）


@dataclass
class VerifyResult:
    """验证结果"""
    status: str = STATUS_SUSPICIOUS     # 三级状态: real / suspicious / uncertain
    confidence: float = 0.0             # 置信度 0~1
    evidence_doi: Optional[str] = None  # 匹配到的 DOI
    evidence_title: Optional[str] = None  # 匹配到的标题
    evidence_url: Optional[str] = None  # 可访问的链接
    message: str = ""                   # 人类可读的说明
    crossref_item: Optional[dict] = None  # CrossRef 原始元数据（供格式化模块使用）

    @property
    def is_real(self) -> bool:
        return self.status == STATUS_REAL


def _is_chinese(text: str) -> bool:
    """判断文本是否以中文为主"""
    cn_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    return cn_chars > len(text) * 0.15


def _normalize(text: str) -> str:
    """
    文本标准化：小写 → 去标点 → 合并空格
    让 "Attention Is All You Need!" 和 "attention is all you need" 能匹配上
    """
    text = text.lower().strip()
    # 去除标点（保留字母、数字、空格、中文字符）
    text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
    # 合并连续空格
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _tokenize_chinese(text: str) -> list[str]:
    """
    简易中文分词：按单字 + 双字组合切分
    不依赖 jieba 等外部库，用 bigram 近似词语边界
    """
    chars = [c for c in text if '\u4e00' <= c <= '\u9fff']
    tokens = list(chars)  # 单字
    for i in range(len(chars) - 1):
        tokens.append(chars[i] + chars[i + 1])  # 双字词
    return tokens


def _get_keywords(text: str) -> set[str]:
    """提取关键词：根据语言选择不同的分词和停用词策略"""
    if _is_chinese(text):
        tokens = _tokenize_chinese(text)
        return {t for t in tokens if t not in STOP_WORDS_ZH and len(t) >= 2}
    else:
        words = _normalize(text).split()
        return {w for w in words if w not in STOP_WORDS_EN and len(w) > 1}


def _similarity(a: str, b: str) -> float:
    """
    综合相似度算法（三个维度加权）：
    1. SequenceMatcher (0.50) — 考虑词序的子序列匹配，对整体结构最敏感
    2. 关键词 Jaccard  (0.40) — 去停用词后比较核心术语重叠，用交并比防止部分重叠虚高
    3. 长度惩罚       (0.10) — 标题长度差异过大时扣分，防止短标题碰巧高分
    旧版的「覆盖率」指标容易被部分重叠的假文献欺骗，改为长度惩罚更稳健
    """
    if not a or not b:
        return 0.0

    norm_a = _normalize(a)
    norm_b = _normalize(b)

    # ① SequenceMatcher：字符级最长公共子序列比率
    seq_score = SequenceMatcher(None, norm_a, norm_b).ratio()

    # ② 关键词 Jaccard：核心术语的交集/并集
    kw_a = _get_keywords(a)
    kw_b = _get_keywords(b)
    if kw_a and kw_b:
        jaccard = len(kw_a & kw_b) / len(kw_a | kw_b)
    else:
        jaccard = 0.0

    # ③ 长度惩罚：两个标题长度差异越大，得分越低
    len_a, len_b = len(norm_a), len(norm_b)
    if max(len_a, len_b) > 0:
        len_ratio = min(len_a, len_b) / max(len_a, len_b)
    else:
        len_ratio = 0.0

    # 加权求和
    final = seq_score * 0.50 + jaccard * 0.40 + len_ratio * 0.10
    return final


def verify_by_doi(doi: str) -> VerifyResult:
    """通过 DOI 直接查询 CrossRef，DOI 是唯一标识，匹配即为真"""
    try:
        resp = requests.get(f"{CROSSREF_API}/{doi}", timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()["message"]
            title = data.get("title", [""])[0]
            url = data.get("URL", f"https://doi.org/{doi}")
            return VerifyResult(
                status=STATUS_REAL, confidence=0.99,
                evidence_doi=doi, evidence_title=title, evidence_url=url,
                message="DOI 验证通过，文献真实存在",
                crossref_item=data,
            )
        else:
            return VerifyResult(
                status=STATUS_SUSPICIOUS, confidence=0.7,
                message=f"DOI {doi} 在 CrossRef 中未找到，可能是虚假文献"
            )
    except requests.RequestException as e:
        return VerifyResult(
            status=STATUS_UNCERTAIN, confidence=0.3,
            message=f"网络请求失败: {e}"
        )


def verify_by_title(title: str) -> VerifyResult:
    """
    通过标题在 CrossRef 中搜索，比较最佳结果的相似度。
    拉取 5 条候选结果以提升召回率。
    对中文标题做特殊处理（CrossRef 中文覆盖率低，给 uncertain 而非直接判假）。
    """
    is_cn = _is_chinese(title)

    try:
        params = {"query.title": title, "rows": 5}
        resp = requests.get(CROSSREF_API, params=params, timeout=TIMEOUT)
        if resp.status_code != 200:
            return VerifyResult(
                status=STATUS_UNCERTAIN, confidence=0.3,
                message="CrossRef API 请求失败"
            )

        items = resp.json()["message"].get("items", [])
        if not items:
            status = STATUS_UNCERTAIN if is_cn else STATUS_SUSPICIOUS
            msg = "CrossRef 中未找到匹配" + ("（中文文献覆盖率低，建议在知网/万方确认）" if is_cn else "，大概率是虚假文献")
            return VerifyResult(status=status, confidence=0.8, message=msg)

        # 对每条候选计算综合相似度，取最高分
        best_score = 0.0
        best_item = items[0]
        for item in items:
            candidate_title = item.get("title", [""])[0]
            score = _similarity(title, candidate_title)
            if score > best_score:
                best_score = score
                best_item = item

        matched_title = best_item.get("title", [""])[0]
        matched_doi = best_item.get("DOI", "")
        matched_url = best_item.get("URL", "")

        # 生成判定结果
        if best_score >= 0.85:
            level = "高度匹配"
        elif best_score >= SIMILARITY_THRESHOLD:
            level = "较高匹配"
        else:
            level = "低匹配"

        if best_score >= SIMILARITY_THRESHOLD:
            return VerifyResult(
                status=STATUS_REAL, confidence=round(best_score, 2),
                evidence_doi=matched_doi,
                evidence_title=matched_title,
                evidence_url=matched_url,
                message=f"标题{level} ({best_score:.0%})，文献真实存在。最近匹配: 「{matched_title[:50]}」",
                crossref_item=best_item,
            )
        elif is_cn and best_score >= 0.45:
            # 中文文献在 CrossRef 匹配度天然偏低，给 uncertain 而非直接判假
            return VerifyResult(
                status=STATUS_UNCERTAIN, confidence=round(best_score, 2),
                evidence_title=matched_title,
                evidence_url=matched_url,
                message=f"标题{level} ({best_score:.0%})，CrossRef 中文覆盖有限，建议在知网/万方手动确认。最近匹配: 「{matched_title[:50]}」"
            )
        else:
            return VerifyResult(
                status=STATUS_SUSPICIOUS, confidence=round(1 - best_score, 2),
                evidence_title=matched_title,
                evidence_url=matched_url,
                message=f"标题{level} ({best_score:.0%})，文献可能是 AI 编造的。最近匹配: 「{matched_title[:50]}」"
            )

    except requests.RequestException as e:
        return VerifyResult(
            status=STATUS_UNCERTAIN, confidence=0.3,
            message=f"网络请求失败: {e}"
        )


def verify(ref: Reference) -> VerifyResult:
    """
    验证主入口：
    1. 如果有 DOI，优先用 DOI 精确验证
    2. 否则用标题模糊搜索验证
    3. 都没有则无法判断
    """
    if ref.doi:
        return verify_by_doi(ref.doi)

    if ref.title:
        return verify_by_title(ref.title)

    return VerifyResult(
        status=STATUS_UNCERTAIN, confidence=0.0,
        message="无法提取标题或 DOI，请检查输入格式"
    )
