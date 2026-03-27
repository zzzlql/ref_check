"""
解析器格式覆盖测试
验证 extract_title 在 10 种引用格式下能正确识别标题
"""
import sys, io
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from ref_checker.parser import parse_reference, _detect_format

CASES = [
    # (格式名, 输入文本, 期望标题关键词)
    ("ACS",
     "Vaswani, A.; Shazeer, N.; Parmar, N.; Uszkoreit, J.; Jones, L.; Gomez, A. N.; Kaiser, L.; Polosukhin, I. Attention Is All You Need. Adv. Neural Inf. Process. Syst. 2017, 30, 5998-6008.",
     "Attention Is All You Need"),

    ("ACS (多作者 et al.)",
     "Riedinger, D. J.; Hassenruck, C.; Herlemann, D.; Labrenz, M. Global Distribution and Predictive Modeling of Vibrio vulnificus Abundance. Commun. Earth Environ. 2025, 6, 210.",
     "Global Distribution and Predictive Modeling"),

    ("APA 7th",
     "Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2019). BERT: Pre-training of deep bidirectional transformers for language understanding. Proceedings of NAACL-HLT, 4171-4186.",
     "BERT"),

    ("APA 7th (期刊)",
     "He, K., Zhang, X., Ren, S., & Sun, J. (2016). Deep residual learning for image recognition. CVPR, 770-778.",
     "Deep residual learning for image recognition"),

    ("GB/T 7714 [J]",
     "张伟, 李明. 基于深度学习的中文文本分类研究综述[J]. 计算机学报, 2020, 43(9): 1615-1642.",
     "基于深度学习的中文文本分类研究综述"),

    ("GB/T 7714 英文",
     "LECUN Y, BENGIO Y, HINTON G. Deep learning[J]. Nature, 2015, 521(7553): 436-444.",
     "Deep learning"),

    ("Vancouver/NLM",
     "LeCun Y, Bengio Y, Hinton G. Deep learning. Nature. 2015;521(7553):436-44.",
     "Deep learning"),

    ("Vancouver (多作者)",
     "Raghunath P, Karunasagar I, Karunasagar I. Improved isolation and detection of pathogenic Vibrio parahaemolyticus from seafood using a new enrichment broth. Int J Food Microbiol. 2009;129(2):200-3.",
     "Improved isolation and detection"),

    ("Nature/Science",
     "LeCun, Y., Bengio, Y. & Hinton, G. Deep learning. Nature 521, 436-440 (2015).",
     "Deep learning"),

    ("Harvard",
     "Vaswani, A., Shazeer, N. and Parmar, N. (2017) 'Attention is all you need', Advances in Neural Information Processing Systems, 30, pp. 5998-6008.",
     "Attention is all you need"),

    ("IEEE (引号)",
     'A. Vaswani et al., "Attention is all you need," Advances in Neural Information Processing Systems, vol. 30, pp. 5998-6008, 2017.',
     "Attention is all you need"),

    ("MLA 9th (引号)",
     'Vaswani, Ashish, et al. "Attention Is All You Need." Advances in Neural Information Processing Systems, vol. 30, 2017, pp. 5998-6008.',
     "Attention Is All You Need"),

    ("Chicago (引号)",
     'LeCun, Yann, Yoshua Bengio, and Geoffrey Hinton. "Deep Learning." Nature 521, no. 7553 (2015): 436-440.',
     "Deep Learning"),

    ("BibTeX",
     '@article{vaswani2017attention, title={Attention is all you need}, author={Vaswani, Ashish and Shazeer, Noam}, journal={NeurIPS}, year={2017}}',
     "Attention is all you need"),

    ("带DOI混合格式",
     "Devlin J, Chang MW, Lee K, et al. BERT: Pre-training of deep bidirectional transformers for language understanding. DOI: 10.18653/v1/N19-1423",
     "BERT"),

    ("编号前缀 [1]",
     "[1] He K, Zhang X, Ren S, et al. Deep residual learning for image recognition. CVPR 2016.",
     "Deep residual learning for image recognition"),

    ("编号前缀 (3)",
     "(3) Brauge, T.; Mougin, J.; Ells, T.; Midelet, G. Sources and Contamination Routes of Seafood with Human Pathogenic Vibrio spp. CRFSFS. 2024, 23(1).",
     "Sources and Contamination Routes"),
]

if __name__ == "__main__":
    print("=" * 72)
    print("  解析器格式覆盖测试")
    print("=" * 72)

    passed = 0
    failed_list = []

    for fmt, text, expected_kw in CASES:
        ref = parse_reference(text)
        detected_fmt = _detect_format(text)
        title = ref.title or ""
        ok = expected_kw.lower() in title.lower()
        passed += ok
        mark = "√" if ok else "✗"

        print(f"\n  [{mark}] {fmt}  (识别为: {detected_fmt})")
        print(f"      期望含: {expected_kw}")
        print(f"      解析得: {title or '(空)'}")

        if not ok:
            failed_list.append((fmt, expected_kw, title))

    total = len(CASES)
    rate = passed / total
    print(f"\n{'=' * 72}")
    print(f"  通过: {passed}/{total} ({rate:.0%})")
    print(f"{'=' * 72}")

    if failed_list:
        print(f"\n  ── 失败详情 ──")
        for fmt, expected, got in failed_list:
            print(f"  [{fmt}] 期望含「{expected}」，实际得「{got}」")
