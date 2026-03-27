"""
AI 生成文献检测与规范系统 - 命令行入口
用法：
  python main.py                → 交互模式（默认 GB/T 7714 格式）
  python main.py --demo         → 运行内置示例
  python main.py --style apa    → 指定输出格式（gbt7714 / apa）
"""

import sys
import io

# 解决 Windows 终端 GBK 编码无法输出 emoji 的问题
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')

from ref_checker.parser import parse_reference
from ref_checker.verifier import verify, VerifyResult, STATUS_REAL, STATUS_UNCERTAIN, STATUS_SUSPICIOUS
from ref_checker.splitter import split_references
from ref_checker.formatter import format_reference, get_supported_styles

# 三级状态的显示映射
STATUS_DISPLAY = {
    STATUS_REAL: "✅ 真实",
    STATUS_UNCERTAIN: "⚠️  待确认",
    STATUS_SUSPICIOUS: "❌ 可疑",
}


def check_one(index: int, text: str, style: str) -> VerifyResult:
    """检测单条参考文献，打印结果，真实文献额外输出规范格式"""
    print(f"\n{'─'*60}")
    print(f"  [{index}] {text[:80]}{'...' if len(text) > 80 else ''}")
    print(f"{'─'*60}")

    ref = parse_reference(text)
    print(f"  解析 → 标题: {ref.title or '未识别'}  |  年份: {ref.year or '?'}  |  DOI: {ref.doi or '无'}")

    result = verify(ref)
    status = STATUS_DISPLAY.get(result.status, "?")
    print(f"  结果 → {status}  (置信度 {result.confidence:.0%})")
    print(f"  说明 → {result.message}")
    if result.evidence_doi:
        print(f"  DOI  → {result.evidence_doi}")
    if result.evidence_url:
        print(f"  链接 → {result.evidence_url}")

    # 真实文献：输出规范格式
    if result.is_real and result.crossref_item:
        item = result.crossref_item
        # 补全：CrossRef 有时返回空标题，用 evidence_title 或原始解析回填
        if not item.get("title", [""])[0]:
            fallback_title = result.evidence_title or ref.title or ""
            item["title"] = [fallback_title]
        formatted = format_reference(item, style)
        if formatted:
            print(f"\n  📝 {style.upper()} 规范格式:")
            print(f"     {formatted}")

    return result


def print_summary(total: int, real_count: int, uncertain_count: int, fake_count: int,
                  formatted_refs: list[str], style: str):
    """打印汇总统计 + 汇总的规范格式文献列表"""
    print(f"\n{'='*60}")
    print(f"  📊 检测汇总")
    print(f"{'='*60}")
    print(f"  总计:     {total} 条")
    print(f"  真实:     {real_count} 条  ✅")
    print(f"  待确认:   {uncertain_count} 条  ⚠️")
    print(f"  可疑:     {fake_count} 条  ❌")
    if fake_count > 0:
        print(f"\n  ❌ 标记为「可疑」的文献大概率是 AI 编造的，建议删除或替换。")
    if uncertain_count > 0:
        print(f"  ⚠️  标记为「待确认」的文献建议在知网/万方/Google Scholar 手动核查。")
    if fake_count == 0 and uncertain_count == 0:
        print(f"\n  🎉 所有文献均通过验证！")

    # 汇总输出所有规范格式的文献（方便直接复制）
    if formatted_refs:
        print(f"\n{'='*60}")
        print(f"  📋 规范格式参考文献（{style.upper()}）- 可直接复制")
        print(f"{'='*60}")
        for i, ref in enumerate(formatted_refs, 1):
            print(f"  [{i}] {ref}")

    print(f"{'='*60}")


def batch_check(refs: list[str], style: str = "gbt7714"):
    """批量检测一组文献"""
    total = len(refs)
    print(f"\n共识别到 {total} 条参考文献，开始逐条验证...")
    print(f"输出格式: {style.upper()}\n")

    real_count = 0
    uncertain_count = 0
    fake_count = 0
    formatted_refs = []  # 收集规范格式的文献

    for i, text in enumerate(refs, 1):
        result = check_one(i, text, style)
        if result.status == STATUS_REAL:
            real_count += 1
            if result.crossref_item:
                # check_one 已经补全了 title，直接格式化
                formatted = format_reference(result.crossref_item, style)
                if formatted:
                    formatted_refs.append(formatted)
        elif result.status == STATUS_UNCERTAIN:
            uncertain_count += 1
        else:
            fake_count += 1

    print_summary(total, real_count, uncertain_count, fake_count, formatted_refs, style)


def interactive_mode(style: str):
    """交互模式：用户粘贴文献，按空行结束输入"""
    print(f"🔍 AI 生成文献检测与规范系统 v0.4")
    print("─" * 60)
    print(f"输出格式: {style.upper()}  (支持: {', '.join(get_supported_styles())})")
    print("请粘贴参考文献（支持多条），输入完毕后：")
    print("  - 连按两次回车 结束输入")
    print("  - 输入 q 退出程序")
    print("─" * 60)

    while True:
        print("\n📋 请粘贴参考文献：")
        lines = []
        empty_count = 0

        while True:
            try:
                line = input()
            except EOFError:
                break

            if line.strip().lower() == 'q' and not lines:
                print("再见！")
                return

            if line.strip() == '':
                empty_count += 1
                if empty_count >= 2:
                    break
                lines.append(line)
            else:
                empty_count = 0
                lines.append(line)

        text = '\n'.join(lines).strip()
        if not text:
            print("未检测到输入，请重试。")
            continue

        refs = split_references(text)
        if not refs:
            print("未能识别出有效的参考文献，请检查格式。")
            continue

        batch_check(refs, style)


def demo_mode(style: str):
    """运行内置示例"""
    print(f"🔍 AI 生成文献检测与规范系统 v0.4 (示例模式)")

    samples = [
        '[1] Vaswani A, Shazeer N, Parmar N, et al. "Attention is all you need." Advances in neural information processing systems, 2017.',
        '[2] Devlin J, Chang M W, Lee K, et al. BERT: Pre-training of deep bidirectional transformers for language understanding. DOI: 10.18653/v1/N19-1423',
        '[3] Zhang W, Li X, Wang H. "Deep Learning Approaches for Universal Knowledge Synthesis in Multi-Modal Reasoning Systems." Journal of Advanced AI Research, 2023, 45(3): 112-128.',
        '[4] Smith J, Brown A. "Quantum-Enhanced Neural Architecture Search for Autonomous Decision Making." Nature Machine Intelligence, 2024, 12(1): 34-51.',
    ]

    refs = split_references('\n'.join(samples))
    batch_check(refs, style)


def _parse_style_arg() -> str:
    """从命令行参数解析格式名称"""
    if '--style' in sys.argv:
        idx = sys.argv.index('--style')
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
    return "gbt7714"


if __name__ == "__main__":
    style = _parse_style_arg()
    if '--demo' in sys.argv:
        demo_mode(style)
    else:
        interactive_mode(style)
