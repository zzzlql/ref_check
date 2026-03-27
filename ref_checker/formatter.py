"""
参考文献格式化模块
将 CrossRef 返回的结构化元数据转换为标准引用格式
支持：GB/T 7714、APA 7th、MLA 9th、Chicago 17th、IEEE
"""

from typing import Optional


def _get_authors(item: dict) -> list[dict]:
    """从 CrossRef 元数据中提取作者列表"""
    return item.get("author", [])


def _format_author_gbt(author: dict) -> str:
    """GB/T 7714 作者格式：姓 名首字母大写，如 VASWANI A"""
    family = author.get("family", "").upper()
    given = author.get("given", "")
    # 取名的每个单词首字母
    initials = " ".join(w[0].upper() for w in given.split() if w)
    return f"{family} {initials}" if initials else family


def _format_author_apa(author: dict) -> str:
    """APA 作者格式：姓, 名首字母.，如 Vaswani, A."""
    family = author.get("family", "")
    given = author.get("given", "")
    initials = " ".join(f"{w[0].upper()}." for w in given.split() if w)
    return f"{family}, {initials}" if initials else family


def _get_year(item: dict) -> str:
    """提取发表年份"""
    date_parts = item.get("published-print", item.get("published-online", item.get("issued", {})))
    parts = date_parts.get("date-parts", [[]])
    if parts and parts[0]:
        return str(parts[0][0])
    return "n.d."


def _get_title(item: dict) -> str:
    """提取论文标题"""
    titles = item.get("title", [])
    return titles[0] if titles else ""


def _get_journal(item: dict) -> str:
    """提取期刊名"""
    names = item.get("container-title", [])
    return names[0] if names else ""


def _get_volume(item: dict) -> str:
    return item.get("volume", "")


def _get_issue(item: dict) -> str:
    return item.get("issue", "")


def _get_pages(item: dict) -> str:
    return item.get("page", "")


def _get_doi(item: dict) -> str:
    return item.get("DOI", "")


def format_gbt7714(item: dict) -> str:
    """
    GB/T 7714-2015 格式（期刊论文）：
    作者. 题名[J]. 期刊名, 年, 卷(期): 页码.
    示例：VASWANI A, SHAZEER N, PARMAR N, et al. Attention is all you need[J]. NeurIPS, 2017, 30: 5998-6008.
    """
    authors = _get_authors(item)
    title = _get_title(item)
    journal = _get_journal(item)
    year = _get_year(item)
    volume = _get_volume(item)
    issue = _get_issue(item)
    pages = _get_pages(item)
    doi = _get_doi(item)

    # 格式化作者（超过3个用 et al）
    if len(authors) > 3:
        author_str = ", ".join(_format_author_gbt(a) for a in authors[:3]) + ", et al"
    elif authors:
        author_str = ", ".join(_format_author_gbt(a) for a in authors)
    else:
        author_str = "佚名"

    # 组装引用
    ref = f"{author_str}. {title}[J]. {journal}"
    if year:
        ref += f", {year}"
    if volume:
        ref += f", {volume}"
    if issue:
        ref += f"({issue})"
    if pages:
        ref += f": {pages}"
    ref += "."

    if doi:
        ref += f" DOI: {doi}."

    return ref


def format_apa(item: dict) -> str:
    """
    APA 第7版格式（期刊论文）：
    作者 (年). 题名. *期刊名*, *卷*(期), 页码. https://doi.org/xxx
    示例：Vaswani, A., Shazeer, N., ... & Polosukhin, I. (2017). Attention is all you need. *NeurIPS*, *30*, 5998–6008.
    """
    authors = _get_authors(item)
    title = _get_title(item)
    journal = _get_journal(item)
    year = _get_year(item)
    volume = _get_volume(item)
    issue = _get_issue(item)
    pages = _get_pages(item)
    doi = _get_doi(item)

    # 格式化作者（APA：超过20个省略，否则全列）
    if len(authors) > 7:
        first_six = ", ".join(_format_author_apa(a) for a in authors[:6])
        last = _format_author_apa(authors[-1])
        author_str = f"{first_six}, ... {last}"
    elif len(authors) > 1:
        all_but_last = ", ".join(_format_author_apa(a) for a in authors[:-1])
        last = _format_author_apa(authors[-1])
        author_str = f"{all_but_last}, & {last}"
    elif authors:
        author_str = _format_author_apa(authors[0])
    else:
        author_str = "Unknown"

    # 组装引用
    ref = f"{author_str} ({year}). {title}. {journal}"
    if volume:
        ref += f", {volume}"
    if issue:
        ref += f"({issue})"
    if pages:
        ref += f", {pages}"
    ref += "."

    if doi:
        ref += f" https://doi.org/{doi}"

    return ref


def _format_author_mla(author: dict) -> str:
    """MLA 作者格式：姓, 名 全拼，如 Vaswani, Ashish"""
    family = author.get("family", "")
    given = author.get("given", "")
    return f"{family}, {given}" if given else family


def _format_author_mla_secondary(author: dict) -> str:
    """MLA 第二作者起用正序：名 姓，如 Noam Shazeer"""
    family = author.get("family", "")
    given = author.get("given", "")
    return f"{given} {family}" if given else family


def _format_author_ieee(author: dict) -> str:
    """IEEE 作者格式：名首字母. 姓，如 A. Vaswani"""
    family = author.get("family", "")
    given = author.get("given", "")
    initials = " ".join(f"{w[0].upper()}." for w in given.split() if w)
    return f"{initials} {family}" if initials else family


def format_mla(item: dict) -> str:
    """
    MLA 第9版格式（期刊论文）：
    姓, 名. "题名." *期刊名*, vol. 卷, no. 期, 年, pp. 页码.
    示例：Vaswani, Ashish, et al. "Attention Is All You Need." NeurIPS, vol. 30, 2017, pp. 5998-6008.
    """
    authors = _get_authors(item)
    title = _get_title(item)
    journal = _get_journal(item)
    year = _get_year(item)
    volume = _get_volume(item)
    issue = _get_issue(item)
    pages = _get_pages(item)
    doi = _get_doi(item)

    # MLA 作者：第一个 姓, 名；后续 名 姓；超过2个用 et al.
    if len(authors) > 2:
        author_str = _format_author_mla(authors[0]) + ", et al."
    elif len(authors) == 2:
        author_str = _format_author_mla(authors[0]) + ", and " + _format_author_mla_secondary(authors[1])
    elif authors:
        author_str = _format_author_mla(authors[0])
    else:
        author_str = "Unknown"

    # MLA 标题用引号包裹，期刊名斜体（纯文本用 * 标记）
    ref = f'{author_str} "{title}." {journal}'
    if volume:
        ref += f", vol. {volume}"
    if issue:
        ref += f", no. {issue}"
    if year:
        ref += f", {year}"
    if pages:
        ref += f", pp. {pages}"
    ref += "."

    if doi:
        ref += f" https://doi.org/{doi}"

    return ref


def format_chicago(item: dict) -> str:
    """
    Chicago 第17版 注释-参考文献格式（期刊论文）：
    姓, 名. "题名." *期刊名* 卷, no. 期 (年): 页码. https://doi.org/xxx.
    示例：Vaswani, Ashish, et al. "Attention Is All You Need." NeurIPS 30 (2017): 5998-6008.
    """
    authors = _get_authors(item)
    title = _get_title(item)
    journal = _get_journal(item)
    year = _get_year(item)
    volume = _get_volume(item)
    issue = _get_issue(item)
    pages = _get_pages(item)
    doi = _get_doi(item)

    # Chicago 作者：第一个 姓, 名；后续 名 姓；超过10个用 et al.
    if len(authors) > 10:
        first_seven = ", ".join(
            _format_author_mla(authors[0]) if i == 0 else _format_author_mla_secondary(authors[i])
            for i in range(7)
        )
        author_str = first_seven + ", et al."
    elif len(authors) > 1:
        parts = [_format_author_mla(authors[0])]
        for a in authors[1:-1]:
            parts.append(_format_author_mla_secondary(a))
        parts.append("and " + _format_author_mla_secondary(authors[-1]))
        author_str = ", ".join(parts)
    elif authors:
        author_str = _format_author_mla(authors[0])
    else:
        author_str = "Unknown"

    ref = f'{author_str}. "{title}." {journal}'
    if volume:
        ref += f" {volume}"
    if issue:
        ref += f", no. {issue}"
    if year:
        ref += f" ({year})"
    if pages:
        ref += f": {pages}"
    ref += "."

    if doi:
        ref += f" https://doi.org/{doi}."

    return ref


def format_ieee(item: dict) -> str:
    """
    IEEE 格式（期刊论文）：
    [N] 名首字母. 姓, "题名," *期刊名*, vol. 卷, no. 期, pp. 页码, 年.
    示例：A. Vaswani et al., "Attention is all you need," NeurIPS, vol. 30, pp. 5998-6008, 2017.
    注意：编号 [N] 由调用方在外部添加，这里只输出引用体。
    """
    authors = _get_authors(item)
    title = _get_title(item)
    journal = _get_journal(item)
    year = _get_year(item)
    volume = _get_volume(item)
    issue = _get_issue(item)
    pages = _get_pages(item)
    doi = _get_doi(item)

    # IEEE 作者：全列（超过6个用 et al.）
    if len(authors) > 6:
        author_str = ", ".join(_format_author_ieee(a) for a in authors[:3]) + " et al."
    elif len(authors) > 1:
        all_but_last = ", ".join(_format_author_ieee(a) for a in authors[:-1])
        last = _format_author_ieee(authors[-1])
        author_str = f"{all_but_last}, and {last}"
    elif authors:
        author_str = _format_author_ieee(authors[0])
    else:
        author_str = "Unknown"

    # IEEE 标题用引号，末尾逗号；期刊名斜体
    ref = f'{author_str}, "{title}," {journal}'
    if volume:
        ref += f", vol. {volume}"
    if issue:
        ref += f", no. {issue}"
    if pages:
        ref += f", pp. {pages}"
    if year:
        ref += f", {year}"
    ref += "."

    if doi:
        ref += f" doi: {doi}."

    return ref


# 格式名称到函数的映射
FORMATTERS = {
    "gbt7714": format_gbt7714,
    "gb/t 7714": format_gbt7714,
    "gb": format_gbt7714,
    "国标": format_gbt7714,
    "apa": format_apa,
    "mla": format_mla,
    "chicago": format_chicago,
    "ieee": format_ieee,
}


def format_reference(item: dict, style: str = "gbt7714") -> Optional[str]:
    """
    格式化入口：传入 CrossRef 元数据 dict + 格式名称
    返回格式化后的引用字符串，格式不支持时返回 None
    """
    formatter = FORMATTERS.get(style.lower().strip())
    if formatter is None:
        return None
    return formatter(item)


def get_supported_styles() -> list[str]:
    """返回支持的格式名称列表（展示用）"""
    return ["GB/T 7714", "APA", "MLA", "Chicago", "IEEE"]
