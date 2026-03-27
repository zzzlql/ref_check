"""
扩展验证测试：8 条文献（4 真 + 4 假），覆盖多种场景
判定标准：
  - 真实文献 → 期望 real 或 uncertain（不应误判为 suspicious）
  - 虚假文献 → 期望 suspicious（不应误判为 real）
"""
import sys, io
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from ref_checker.parser import parse_reference
from ref_checker.verifier import verify, STATUS_REAL, STATUS_UNCERTAIN, STATUS_SUSPICIOUS

STATUS_DISPLAY = {STATUS_REAL: "✅ 真实", STATUS_UNCERTAIN: "⚠️  待确认", STATUS_SUSPICIOUS: "❌ 可疑"}

# ====== 真实文献 ======
REAL = [
    'Vaswani A, Shazeer N, Parmar N, et al. "Attention is all you need." Advances in neural information processing systems, 2017.',
    'Devlin J, Chang M W, Lee K, et al. BERT: Pre-training of deep bidirectional transformers for language understanding. DOI: 10.18653/v1/N19-1423',
    'He K, Zhang X, Ren S, et al. "Deep residual learning for image recognition." Proceedings of the IEEE conference on computer vision and pattern recognition, 2016.',
    '张伟, 李明. "基于深度学习的中文文本分类研究综述." 计算机学报, 2020, 43(9): 1615-1642.',
]

# ====== AI 编造的假文献 ======
FAKE = [
    'Zhang W, Li X, Wang H. "Deep Learning Approaches for Universal Knowledge Synthesis in Multi-Modal Reasoning Systems." Journal of Advanced AI Research, 2023, 45(3): 112-128.',
    'Smith J, Brown A. "Quantum-Enhanced Neural Architecture Search for Autonomous Decision Making." Nature Machine Intelligence, 2024, 12(1): 34-51.',
    '王小明, 赵刚. "融合知识图谱的多模态跨域情感迁移学习框架." 中国人工智能学报, 2023, 15(2): 89-105.',
    'LeCun Y, Bengio Y. "Gradient-Based Optimization for Universal Deep Neural Network Training." IEEE Transactions on Pattern Analysis, 2019, 41(5): 1023-1040.',
]

if __name__ == "__main__":
    print("=" * 60)
    print("  扩展验证测试：4 条真实 + 4 条虚假")
    print("=" * 60)

    correct = 0
    total = 0

    for label, refs, acceptable in [
        ("真实", REAL, {STATUS_REAL, STATUS_UNCERTAIN}),   # 真文献：real 或 uncertain 都算对
        ("虚假", FAKE, {STATUS_SUSPICIOUS}),                # 假文献：必须是 suspicious
    ]:
        expect_desc = "/".join(STATUS_DISPLAY[s] for s in acceptable)
        print(f"\n--- {label}文献 (期望: {expect_desc}) ---")
        for i, text in enumerate(refs, 1):
            ref = parse_reference(text)
            result = verify(ref)
            status = STATUS_DISPLAY.get(result.status, "?")
            hit = result.status in acceptable
            correct += hit
            total += 1
            mark = "√" if hit else "✗ 误判!"
            print(f"\n  [{label[0]}{i}] {text[:70]}...")
            print(f"       标题: {ref.title or '未识别'}")
            print(f"       结果: {status}  置信度 {result.confidence:.0%}  [{mark}]")
            print(f"       说明: {result.message}")

    print(f"\n{'=' * 60}")
    print(f"  准确率: {correct}/{total} ({correct/total:.0%})")
    print(f"{'=' * 60}")
