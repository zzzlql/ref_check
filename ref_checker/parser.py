"""
参考文献解析模块
从一段文献文本中提取关键字段：标题、作者、年份、DOI 等

支持的引用格式：
  - ACS       : Lastname, F. M.; Lastname, F. M. Title. Journal Year, Vol, Pages.
  - APA 7th   : Lastname, F. M. (Year). Title. Journal, Vol(Issue), Pages.
  - GB/T 7714 : LASTNAME FM, et al. 标题[J]. 期刊, 年份, 卷(期): 页码.
  - Vancouver : Lastname AB, Lastname CD. Title. J Abbrev. Year;Vol(Issue):Pages.
  - Nature    : Lastname, F. M. & Lastname, F. M. Title. Nature Vol, Pages (Year).
  - Harvard   : Lastname, F. (Year) 'Title', Journal, Vol(Issue), pp. Pages.
  - IEEE      : F. M. Lastname et al., "Title," Journal, vol. X, Year.  [引号]
  - MLA 9th   : Lastname, Firstname, et al. "Title." Journal, Year.     [引号]
  - Chicago   : Lastname, Firstname. "Title." Journal Vol (Year): Pages. [引号]
  - BibTeX    : @article{key, title={Title}, ...}
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Reference:
    """解析后的参考文献结构"""
    raw: str                          # 原始文本
    title: Optional[str] = None       # 论文标题
    authors: list[str] = field(default_factory=list)  # 作者列表
    year: Optional[str] = None        # 发表年份
    doi: Optional[str] = None         # DOI 号
    journal: Optional[str] = None     # 期刊名


# ─── 工具函数 ─────────────────────────────────────────────────

def extract_doi(text: str) -> Optional[str]:
    """从文本中提取 DOI（格式如 10.xxxx/xxxxx）"""
    match = re.search(r'10\.\d{4,9}/[^\s,;}\]]+', text)
    return match.group(0).rstrip('.') if match else None


def extract_year(text: str) -> Optional[str]:
    """提取 4 位年份（1900-2099）"""
    match = re.search(r'(?:19|20)\d{2}', text)
    return match.group(0) if match else None


def _preprocess(text: str) -> str:
    """预处理：去掉编号、DOI、URL、多余空白"""
    # 去掉开头序号 [1]、(1)、1.、1)
    text = re.sub(r'^\s*(\[\d+\]|\(\d+\)|\d+[.)、])\s*', '', text)
    # 去掉 DOI 及后面内容（防止干扰）
    text = re.sub(r'\bDOI\s*:\s*10\.\S+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'https?://doi\.org/\S+', '', text)
    # 合并多余空白
    return re.sub(r'\s+', ' ', text).strip()


def _clean_title(s: str) -> str:
    """清理候选标题：去掉首尾标点和多余空白"""
    return s.strip().strip('.,;:[]()。，；：').strip()


def _is_author_block(text: str) -> bool:
    """
    判断一段文本是否是作者列表块（而非标题）。
    综合多种格式的作者特征：
      - ACS        : Lastname, F. M.; ...（含分号 + 姓名缩写模式）
      - APA/Chicago: Lastname, F. M., & ...
      - Vancouver  : Lastname AB, Lastname CD（无点号的大写缩写）
      - Nature     : Lastname, F. M. & ...
      - GB/T 7714  : LASTNAME FM, et al.（全大写姓名）
      - IEEE       : F. M. Lastname, ...（名首字母在前）
    """
    text = text.strip()

    # ① 含分号且有"姓, 名首字母."模式 → ACS
    if ';' in text and re.search(r'[A-Z][a-z]+,\s*[A-Z]\.', text):
        return True

    # ② 含 "et al" → 作者列表结尾
    if re.search(r'\bet\s+al\b', text, re.IGNORECASE):
        return True

    # ③ 含 "&" 且紧跟姓名缩写 → APA/Nature 风格
    if re.search(r'&\s+[A-Z][a-z]+,?\s+[A-Z]\.', text):
        return True

    # ④ Vancouver 无点缩写：多个"Lastname AB," 模式
    vancouver_pattern = re.findall(r'[A-Z][a-z]+\s+[A-Z]{1,4}(?=\s*,|\s*$)', text)
    if len(vancouver_pattern) >= 2:
        return True

    # ⑤ IEEE 风格：多个"F. M. Lastname"模式
    ieee_pattern = re.findall(r'\b[A-Z]\.\s+[A-Z][a-z]+', text)
    if len(ieee_pattern) >= 2:
        return True

    # ⑥ 大量单字母缩写（名首字母）
    initials = re.findall(r'\b[A-Z]\.', text)
    if len(initials) >= 3 and len(text) < 100:
        return True

    # ⑦ 多个"姓 首字母"连续出现，且占文本较大比例
    name_chunks = re.findall(r'[A-Z][a-z]{1,15}(?:\s+[A-Z]\.)+', text)
    if len(name_chunks) >= 2:
        covered = sum(len(c) for c in name_chunks)
        if covered / max(len(text), 1) > 0.4:
            return True

    return False


def _is_journal_fragment(text: str) -> bool:
    """
    判断是否是期刊/出版信息片段（卷期页码、年份等）。
    这类片段通常很短，或以大写缩写+数字为主。
    """
    text = text.strip()
    # 很短的片段（期刊缩写等）
    if len(text) < 12:
        return True
    # 纯数字+字母组合（如 "45 (3), 100-110" 或 "2023;45:100"）
    if re.match(r'^[\d\s()\[\],;:–\-–/]+$', text):
        return True
    # 形如 "vol. X, no. Y, pp. Z"
    if re.search(r'\bvol\.?\s*\d|\bno\.?\s*\d|\bpp\.?\s*\d', text, re.IGNORECASE):
        return True
    return False


# ─── 格式识别 ─────────────────────────────────────────────────

def _detect_format(text: str) -> str:
    """
    识别引用格式，用于选择最合适的标题提取策略。
    返回格式标识符：bibtex / ris / apa / gbt / acs / vancouver / nature / harvard / generic
    """
    # BibTeX: @article{...}
    if re.match(r'^\s*@\w+\s*\{', text):
        return 'bibtex'
    # RIS: TY  - / TI  -
    if re.search(r'^TY\s+- ', text, re.MULTILINE):
        return 'ris'
    # Harvard: 单引号包裹标题（在年份之后）
    if re.search(r'\((?:19|20)\d{2}\)\s+\'[^\']{10,}\'', text):
        return 'harvard'
    # GB/T 7714: [J] [M] [C] [D] [G] 文献类型标记
    if re.search(r'\[J\]|\[M\]|\[C\]|\[D\]|\[G\]|\[N\]', text):
        return 'gbt'
    # ACS: 分号分隔作者 "Lastname, F. M.;"
    if re.search(r'[A-Z][a-z]+,\s*[A-Z]\.\s*[A-Z]?\.?\s*;', text):
        return 'acs'
    # Nature/Science: 年份在末尾 "(Year)." 且作者用 "&" 连接
    # 注意：需在 APA 之前检测，因为 Nature 末尾的 (Year) 也能匹配 APA 模式
    if (re.search(r'&\s+[A-Z][a-z]', text) and
            re.search(r'\((?:19|20)\d{2}\)\.?\s*$', text.rstrip())):
        return 'nature'
    # APA: (Year). 标题. — 年份在括号中且不在末尾
    year_match = re.search(r'\((?:19|20)\d{2}\)\.', text)
    if year_match:
        # 年份必须不在文本末尾（末尾是期刊/卷期信息，不是标题）
        tail = text[year_match.end():].strip()
        if len(tail) > 5:  # 年份后还有内容（标题+期刊）
            return 'apa'
    # Vancouver: "Lastname AB," 无点缩写连续出现
    if re.search(r'[A-Z][a-z]+\s+[A-Z]{1,4},\s+[A-Z][a-z]+\s+[A-Z]{1,4}', text):
        return 'vancouver'
    return 'generic'


# ─── 格式专用提取器 ──────────────────────────────────────────

def _extract_bibtex(text: str) -> Optional[str]:
    """BibTeX: title={Title} 或 title = "Title" """
    m = re.search(r'\btitle\s*=\s*[{"](.*?)[}"]', text, re.IGNORECASE | re.DOTALL)
    if m:
        return _clean_title(m.group(1))
    return None


def _extract_ris(text: str) -> Optional[str]:
    """RIS 格式: TI  - Title"""
    m = re.search(r'^TI\s+-\s+(.+)$', text, re.MULTILINE)
    if m:
        return _clean_title(m.group(1))
    return None


def _extract_apa(text: str) -> Optional[str]:
    """
    APA 7th: Lastname, F. M. (Year). Title. Journal, Vol(Issue), Pages.
    关键特征：(Year). 之后紧跟标题
    """
    m = re.search(r'\((?:19|20)\d{2}\)\.\s+(.+?)(?:\.\s+[A-Z*_]|\.$|,\s+\d)', text)
    if m:
        candidate = _clean_title(m.group(1))
        if len(candidate) > 10:
            return candidate
    return None


def _extract_gbt(text: str) -> Optional[str]:
    """
    GB/T 7714: AUTHOR. Title[J]. Journal, Year, Vol(Issue): Pages.
    关键特征：标题后紧跟 [J] [M] 等文献类型标记
    """
    m = re.search(r'([^.。]{10,})\s*\[[JMCDGN]\]', text)
    if m:
        candidate = _clean_title(m.group(1))
        # 去掉可能混入的作者部分（取最后一个". "之后的内容）
        parts = re.split(r'\.\s+', candidate)
        if len(parts) > 1:
            candidate = _clean_title(parts[-1])
        if len(candidate) > 5:
            return candidate
    return None


def _extract_acs(text: str) -> Optional[str]:
    """
    ACS: Lastname, F. M.; Lastname, F. M. Title. Journal Year, Vol, Pages.
    关键特征：分号分隔作者列表，最后一个分号后是"末尾作者. 标题. 期刊..."
    """
    last_semi = text.rfind(';')
    after_semi = text[last_semi + 1:].strip()

    # 按句点+空格拆分 "末尾作者. 标题. 期刊..."
    parts = re.split(r'\.\s+', after_semi)
    # 第一段是最后一个作者名，从第二段开始找标题
    for part in parts[1:]:
        candidate = _clean_title(part)
        if len(candidate) > 15 and not _is_author_block(candidate) and not _is_journal_fragment(candidate):
            return candidate

    # 如果上面没找到，遍历整个文本的句点拆分
    return _extract_generic(text)


def _extract_vancouver(text: str) -> Optional[str]:
    """
    Vancouver/NLM: Lastname AB, Lastname CD. Title. J Abbrev. Year;Vol(Issue):Pages.
    关键特征：作者无点号缩写，用逗号分隔；年份在期刊后以分号出现
    """
    # 去掉首尾编号
    text = _preprocess(text)
    # 按 ". " 拆分，跳过作者块
    parts = re.split(r'\.\s+', text)
    for part in parts:
        candidate = _clean_title(part)
        if len(candidate) < 12:
            continue
        if _is_author_block(candidate):
            continue
        if _is_journal_fragment(candidate):
            continue
        # Vancouver 期刊后有 Year;Vol 或 Year Mon; 特征，跳过这类
        if re.search(r'\d{4}\s*;|\d{4}\s+\w{3}\s*;', candidate):
            continue
        return candidate
    return None


def _extract_nature(text: str) -> Optional[str]:
    """
    Nature/Science: Lastname, F. M., ... & Lastname, F. M. Title. Journal Vol, Pages (Year).
    策略：找到 "&" 后的末尾作者片段，取其后直到 (Year) 之间的第一个句子作为标题。
    例：LeCun, Y., Bengio, Y. & Hinton, G. Deep learning. Nature 521, 436 (2015).
        → 匹配 "& Hinton, G. [Deep learning. Nature 521, 436] (2015)"
        → group(1) = "Deep learning. Nature 521, 436"
        → 取第一段 "Deep learning"
    """
    m = re.search(
        r'(?:&|and)\s+[A-Z][a-z]+,?\s+(?:[A-Z]\.\s*)+'   # & 末尾作者
        r'(.+?)'                                             # 标题+期刊（非贪婪）
        r'\s*\((?:19|20)\d{2}\)',                           # (Year)
        text
    )
    if m:
        rest = m.group(1).strip()
        # rest = "Deep learning. Nature 521, 436-440"，取第一句为标题
        parts = re.split(r'\.\s+', rest)
        candidate = _clean_title(parts[0])
        if len(candidate) > 5:
            return candidate

    # 降级：去掉末尾 (Year) 后用通用策略
    text_no_year = re.sub(r'\s*\((?:19|20)\d{2}\)\.?\s*$', '', text.rstrip())
    return _extract_generic(text_no_year)


def _extract_harvard(text: str) -> Optional[str]:
    """
    Harvard: Lastname, F. (Year) 'Title', Journal, Vol(Issue), pp. Pages.
    关键特征：标题用单引号包裹
    """
    m = re.search(r"'([^']{10,})'", text)
    if m:
        return _clean_title(m.group(1))
    return None


def _extract_generic(text: str) -> Optional[str]:
    """
    通用策略：按句点+空格拆分，跳过作者块和期刊信息片段，取最长候选。
    适用于 GB/T 7714（无标记版）、旧版 APA、混合格式等。
    """
    text = _preprocess(text)
    parts = re.split(r'\.\s+|。\s*', text)
    candidates = []
    for part in parts:
        candidate = _clean_title(part)
        if len(candidate) < 15:
            continue
        if _is_author_block(candidate):
            continue
        if _is_journal_fragment(candidate):
            continue
        candidates.append(candidate)

    if candidates:
        return max(candidates, key=len)
    return None


# ─── 主入口 ──────────────────────────────────────────────────

def extract_title(text: str) -> Optional[str]:
    """
    多策略标题提取，按可靠性降序尝试：

    优先级：
      [最高] 引号包裹（双引号/书名号）  → IEEE, MLA, Chicago
             单引号包裹               → Harvard
             BibTeX title={}          → BibTeX
             RIS TI  -                → RIS
             (Year). 后的内容         → APA
             [J][M] 前的内容          → GB/T 7714
             分号作者后的句子          → ACS
             末尾 (Year) + "&" 作者   → Nature
             无点缩写作者块后的句子    → Vancouver
      [通用] 句点拆分取最长非作者片段  → 其余所有格式
    """
    # ── 双引号 / 书名号 / 《》 ──────────────────────────────────
    quoted = re.findall(r'["""「《](.+?)["""」》]', text)
    if quoted:
        best = max(quoted, key=len).strip()
        if len(best) > 5:
            return _clean_title(best)

    # ── 单引号（Harvard）──────────────────────────────────────
    single_quoted = re.findall(r"'([^']{10,})'", text)
    if single_quoted:
        return _clean_title(max(single_quoted, key=len))

    cleaned = _preprocess(text)

    # ── 格式专用路径 ──────────────────────────────────────────
    fmt = _detect_format(cleaned)

    if fmt == 'bibtex':
        result = _extract_bibtex(cleaned)
        if result:
            return result

    if fmt == 'ris':
        result = _extract_ris(cleaned)
        if result:
            return result

    if fmt == 'apa':
        result = _extract_apa(cleaned)
        if result:
            return result

    if fmt == 'gbt':
        result = _extract_gbt(cleaned)
        if result:
            return result

    if fmt == 'acs':
        result = _extract_acs(cleaned)
        if result:
            return result

    if fmt == 'nature':
        result = _extract_nature(cleaned)
        if result:
            return result

    if fmt == 'vancouver':
        result = _extract_vancouver(cleaned)
        if result:
            return result

    # ── 通用兜底 ─────────────────────────────────────────────
    return _extract_generic(cleaned)


def parse_reference(text: str) -> Reference:
    """解析一条参考文献文本，返回结构化的 Reference 对象"""
    text = text.strip()
    ref = Reference(raw=text)
    ref.doi = extract_doi(text)
    ref.year = extract_year(text)
    ref.title = extract_title(text)
    return ref
