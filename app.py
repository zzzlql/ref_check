"""
AI 生成文献检测与规范系统 — Streamlit Web 界面 v2.0
启动：streamlit run app.py
"""

import io
import streamlit as st
from ref_checker.parser import parse_reference
from ref_checker.verifier import verify, STATUS_REAL, STATUS_UNCERTAIN, STATUS_SUSPICIOUS
from ref_checker.splitter import split_references
from ref_checker.formatter import format_reference, get_supported_styles

# ─── 页面配置 ───────────────────────────────────────────────
st.set_page_config(
    page_title="RefCheck - AI 文献检测",
    page_icon="🔍",
    layout="wide",
)

# ─── 自定义 CSS ─────────────────────────────────────────────
st.markdown("""
<style>
    /* ===== 全局 ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    .block-container { padding-top: 1.5rem; max-width: 1060px; }
    html, body, [class*="css"] { font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif; }

    /* ===== 顶部 Hero ===== */
    .hero {
        text-align: center; padding: 2.5rem 1rem 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 18px; margin-bottom: 1.8rem;
        box-shadow: 0 8px 30px rgba(102,126,234,0.25);
    }
    .hero h1 {
        color: #fff; font-size: 2.6rem; font-weight: 700;
        margin: 0; letter-spacing: -0.5px;
    }
    .hero .subtitle {
        color: rgba(255,255,255,0.88); font-size: 1.08rem;
        margin-top: 0.4rem; font-weight: 400;
    }
    .hero .tagline {
        display: inline-block; margin-top: 0.9rem;
        background: rgba(255,255,255,0.18); color: #fff;
        padding: 6px 18px; border-radius: 20px; font-size: 0.82rem;
        backdrop-filter: blur(4px);
    }

    /* ===== 工具栏（格式选择 + 按钮行） ===== */
    .toolbar {
        display: flex; align-items: center; gap: 12px;
        margin-bottom: 0.6rem;
    }

    /* ===== 统计卡片行 ===== */
    .stat-row { display: flex; gap: 14px; margin: 1.2rem 0 0.5rem; }
    .stat-card {
        flex: 1; text-align: center; padding: 20px 10px;
        border-radius: 14px; font-weight: 700; font-size: 2rem;
        line-height: 1.1; transition: transform 0.15s;
    }
    .stat-card:hover { transform: translateY(-2px); }
    .stat-card small {
        display: block; font-weight: 500; font-size: 0.82rem;
        margin-top: 6px; opacity: 0.85;
    }
    .stat-total     { background: linear-gradient(135deg,#e8eaf6,#c5cae9); color: #283593; }
    .stat-real      { background: linear-gradient(135deg,#c8e6c9,#a5d6a7); color: #1b5e20; }
    .stat-uncertain { background: linear-gradient(135deg,#fff9c4,#fff176); color: #f57f17; }
    .stat-fake      { background: linear-gradient(135deg,#ffcdd2,#ef9a9a); color: #b71c1c; }

    /* ===== 结果卡片 ===== */
    .ref-card {
        border-radius: 14px; padding: 20px 24px; margin-bottom: 16px;
        border-left: 6px solid; background: #fff;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        transition: box-shadow 0.2s;
    }
    .ref-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
    .ref-card-real       { border-color: #43a047; }
    .ref-card-uncertain  { border-color: #ffa000; }
    .ref-card-suspicious { border-color: #e53935; }

    /* 状态徽章 */
    .badge {
        display: inline-block; padding: 3px 12px; border-radius: 20px;
        font-size: 0.78rem; font-weight: 600; margin-right: 8px;
        letter-spacing: 0.3px;
    }
    .badge-real       { background: #e8f5e9; color: #2e7d32; }
    .badge-uncertain  { background: #fff8e1; color: #e65100; }
    .badge-suspicious { background: #ffebee; color: #c62828; }

    .ref-card .card-idx {
        color: #999; font-size: 0.78rem; font-weight: 500;
    }
    .ref-card .card-title {
        font-weight: 600; font-size: 1rem; margin: 8px 0 6px;
        color: #1a1a2e; line-height: 1.4;
    }
    .ref-card .meta {
        color: #555; font-size: 0.85rem; line-height: 1.7;
    }
    .ref-card .meta b { color: #333; }
    .ref-card .meta a { color: #5c6bc0; text-decoration: none; font-weight: 500; }
    .ref-card .meta a:hover { text-decoration: underline; }

    /* 置信度进度条 */
    .conf-bar-wrap {
        display: flex; align-items: center; gap: 8px;
        margin-top: 6px;
    }
    .conf-bar {
        flex: 1; max-width: 180px; height: 6px;
        background: #e0e0e0; border-radius: 3px; overflow: hidden;
    }
    .conf-bar-fill {
        height: 100%; border-radius: 3px;
        transition: width 0.4s ease;
    }
    .conf-bar-fill-real       { background: linear-gradient(90deg,#66bb6a,#43a047); }
    .conf-bar-fill-uncertain  { background: linear-gradient(90deg,#ffca28,#ffa000); }
    .conf-bar-fill-suspicious { background: linear-gradient(90deg,#ef5350,#c62828); }
    .conf-label { font-size: 0.8rem; font-weight: 600; min-width: 36px; }

    /* ===== 格式化输出框 ===== */
    .fmt-box {
        background: linear-gradient(135deg,#f5f7ff,#eef1fb);
        border: 1px solid #d1d9e6; border-radius: 10px;
        padding: 14px 18px; margin-top: 10px;
        font-size: 0.88rem; line-height: 1.65;
        color: #24292e; word-break: break-word;
    }
    .fmt-box .fmt-label {
        font-weight: 600; color: #5c6bc0; font-size: 0.78rem;
        text-transform: uppercase; letter-spacing: 0.5px;
    }

    /* ===== 汇总复制区 ===== */
    .copy-header {
        display: flex; align-items: center; gap: 8px;
        margin-bottom: 0.3rem;
    }
    .copy-header h3 { margin: 0; }

    /* ===== 侧边栏美化 ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fe 0%, #eef0f8 100%);
    }
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #3f51b5; font-size: 1rem;
    }

    /* ===== 输入框美化 ===== */
    .stTextArea textarea {
        border-radius: 12px !important;
        border: 2px solid #e0e0e0 !important;
        font-size: 0.92rem !important;
        transition: border-color 0.2s;
    }
    .stTextArea textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102,126,234,0.15) !important;
    }

    /* ===== 按钮美化 ===== */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        border: none !important; border-radius: 10px !important;
        font-weight: 600 !important; letter-spacing: 0.3px;
        transition: transform 0.15s, box-shadow 0.15s;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(102,126,234,0.35) !important;
    }
    .stButton > button[kind="secondary"] {
        border-radius: 10px !important; font-weight: 500 !important;
    }

    /* ===== 提示框圆角 ===== */
    .stAlert { border-radius: 12px !important; }

    /* ===== 文件上传区美化 ===== */
    [data-testid="stFileUploader"] {
        border: 2px dashed #c5cae9 !important;
        border-radius: 14px !important;
        background: #f8f9fe !important;
        transition: border-color 0.2s, background 0.2s;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #667eea !important;
        background: #f0f2ff !important;
    }
    /* Tab 样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: #f0f2f6;
        border-radius: 12px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 9px !important;
        font-weight: 500 !important;
        padding: 6px 18px !important;
    }
    .stTabs [aria-selected="true"] {
        background: #fff !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.1) !important;
    }
    /* 文件信息徽章 */
    .file-badge {
        display: inline-flex; align-items: center; gap: 6px;
        background: #e8f5e9; color: #2e7d32;
        border-radius: 20px; padding: 4px 14px;
        font-size: 0.82rem; font-weight: 600;
        margin-bottom: 0.6rem;
    }

    /* ===== 隐藏默认元素 ===== */
    footer { visibility: hidden; }
    .stDeployButton { display: none; }
    #MainMenu { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─── Hero 标题区 ─────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🔍 RefCheck</h1>
    <p class="subtitle">AI 生成文献检测与规范系统</p>
    <span class="tagline">粘贴参考文献 → 一键检测真伪 → 自动规范格式</span>
</div>
""", unsafe_allow_html=True)

# ─── 侧边栏 ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ 输出设置")

    style_names = get_supported_styles()
    style_keys = ["gbt7714", "apa", "mla", "chicago", "ieee"]
    style_map = dict(zip(style_names, style_keys))
    selected_style_name = st.selectbox(
        "引用格式",
        style_names,
        index=0,
        help="验证为真实的文献将自动转为所选格式",
    )
    selected_style = style_map[selected_style_name]

    st.markdown("---")
    st.markdown("### 📖 使用说明")
    st.markdown("""
**方式一：粘贴文本**
1. 切换到「✏️ 粘贴文本」选项卡
2. 直接粘贴，支持每行一条或 `[1]` 编号

**方式二：上传文件**
1. 切换到「📂 上传文件」选项卡
2. 上传 `.txt` 文件（支持 UTF-8 / GBK 编码）
3. 文件内容自动导入，点击 **开始检测**

**共同步骤**
- 侧边栏选择输出格式
- 真实文献自动生成规范格式
- 底部可 **一键复制**
    """)

    st.markdown("---")
    st.markdown("### 🏷️ 判定说明")
    st.markdown("""
- ✅ **真实** — CrossRef 验证通过
- ⚠️ **待确认** — 需人工二次核查
- ❌ **可疑** — 大概率 AI 编造
    """)

    st.markdown("---")
    st.markdown(
        "<small style='color:#999'>数据源: CrossRef API（免费开放）<br>"
        "中文文献覆盖有限，「待确认」建议<br>在知网 / 万方 / Google Scholar 核查</small>",
        unsafe_allow_html=True,
    )

# ─── 常量 ────────────────────────────────────────────────────
SAMPLE_TEXT = """[1] Vaswani A, Shazeer N, Parmar N, et al. "Attention is all you need." Advances in neural information processing systems, 2017.
[2] Devlin J, Chang M W, Lee K, et al. BERT: Pre-training of deep bidirectional transformers for language understanding. DOI: 10.18653/v1/N19-1423
[3] Zhang W, Li X, Wang H. "Deep Learning Approaches for Universal Knowledge Synthesis in Multi-Modal Reasoning Systems." Journal of Advanced AI Research, 2023, 45(3): 112-128.
[4] Smith J, Brown A. "Quantum-Enhanced Neural Architecture Search for Autonomous Decision Making." Nature Machine Intelligence, 2024, 12(1): 34-51.
[5] He K, Zhang X, Ren S, et al. "Deep residual learning for image recognition." Proceedings of the IEEE conference on computer vision and pattern recognition, 2016."""

MAX_FILE_SIZE_MB = 2  # 上传文件大小限制

# ─── session state 初始化 ─────────────────────────────────────
if "ref_text" not in st.session_state:
    st.session_state["ref_text"] = ""
if "file_info" not in st.session_state:
    st.session_state["file_info"] = None   # {"name": str, "lines": int}


def _decode_txt(raw_bytes: bytes) -> str:
    """
    自动识别 .txt 编码：依次尝试 UTF-8、UTF-8-BOM、GBK/GB18030、Latin-1。
    返回解码后的字符串，失败则抛出 ValueError。
    """
    for enc in ("utf-8-sig", "utf-8", "gb18030", "gbk", "latin-1"):
        try:
            return raw_bytes.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    raise ValueError("无法识别文件编码，请将文件转换为 UTF-8 格式后重试。")


# ─── 输入区（Tab 布局） ──────────────────────────────────────
tab_paste, tab_upload = st.tabs(["✏️  粘贴文本", "📂  上传文件 (.txt)"])

# ── Tab 1：粘贴文本 ──────────────────────────────────────────
with tab_paste:
    # 不使用 key=，完全由 value= + ref_text 驱动内容
    # 这样按钮只需更新 ref_text 再 rerun，text_area 就会同步显示新内容
    user_input_paste = st.text_area(
        "粘贴参考文献",
        value=st.session_state["ref_text"],
        height=200,
        placeholder=(
            "在此粘贴参考文献...\n\n"
            "支持格式：\n"
            "  · 每行一条\n"
            "  · [1] [2] ... 编号格式\n"
            "  · 带 DOI 的文献自动精确匹配"
        ),
        label_visibility="collapsed",
    )
    # 用户手动输入时同步回 ref_text
    st.session_state["ref_text"] = user_input_paste

    col_run1, col_demo, col_clear, _ = st.columns([1.2, 1, 1, 3])
    with col_run1:
        run_btn_paste = st.button("🚀 开始检测", use_container_width=True,
                                  type="primary", key="run_paste")
    with col_demo:
        demo_btn = st.button("📋 加载示例", use_container_width=True, key="demo")
    with col_clear:
        clear_btn = st.button("🗑️ 清空", use_container_width=True, key="clear")

    if demo_btn:
        st.session_state["ref_text"]  = SAMPLE_TEXT
        st.session_state["file_info"] = None
        st.rerun()
    if clear_btn:
        st.session_state["ref_text"]  = ""
        st.session_state["file_info"] = None
        st.rerun()

# ── Tab 2：上传文件 ──────────────────────────────────────────
with tab_upload:
    st.markdown(
        "<p style='color:#666;font-size:0.9rem;margin-bottom:0.8rem;'>"
        "支持 <b>.txt</b> 格式，编码自动识别（UTF-8 / GBK / GB18030），"
        f"文件大小 ≤ {MAX_FILE_SIZE_MB} MB。</p>",
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "拖拽或点击选择 .txt 文件",
        type=["txt"],
        label_visibility="collapsed",
        key="file_uploader",
    )

    # 处理上传的文件
    if uploaded_file is not None:
        # 检查文件大小
        file_bytes = uploaded_file.read()
        size_mb = len(file_bytes) / 1024 / 1024

        if size_mb > MAX_FILE_SIZE_MB:
            st.error(f"文件过大（{size_mb:.1f} MB），请上传 {MAX_FILE_SIZE_MB} MB 以内的文件。")
        else:
            try:
                file_text = _decode_txt(file_bytes)
                line_count = len([l for l in file_text.splitlines() if l.strip()])
                # 更新 session state
                st.session_state["ref_text"] = file_text
                st.session_state["file_info"] = {
                    "name": uploaded_file.name,
                    "lines": line_count,
                    "size_kb": round(len(file_bytes) / 1024, 1),
                }
            except ValueError as e:
                st.error(str(e))

    # 显示已加载文件信息
    if st.session_state["file_info"]:
        info = st.session_state["file_info"]
        st.markdown(
            f'<div class="file-badge">'
            f'📄 {info["name"]} &nbsp;·&nbsp; {info["lines"]} 行 &nbsp;·&nbsp; {info["size_kb"]} KB'
            f'</div>',
            unsafe_allow_html=True,
        )
        # 预览（前 10 行）
        preview_lines = [l for l in st.session_state["ref_text"].splitlines() if l.strip()][:10]
        with st.expander(f"预览文件内容（前 {len(preview_lines)} 行）", expanded=False):
            st.code("\n".join(preview_lines), language=None)

        col_run2, col_discard, _ = st.columns([1.2, 1, 4])
        with col_run2:
            run_btn_file = st.button("🚀 开始检测", use_container_width=True,
                                     type="primary", key="run_file")
        with col_discard:
            if st.button("✖ 移除文件", use_container_width=True, key="discard_file"):
                st.session_state["ref_text"] = ""
                st.session_state["file_info"] = None
                st.rerun()
    else:
        run_btn_file = False
        if uploaded_file is None:
            st.markdown(
                "<div style='text-align:center;color:#bbb;padding:1.5rem 0;font-size:0.88rem;'>"
                "尚未上传文件</div>",
                unsafe_allow_html=True,
            )

# ─── 统一触发逻辑 ─────────────────────────────────────────────
# 两个 Tab 都能触发检测，共用同一份 ref_text
# run_btn_file 仅在文件已加载时才被定义，其余情况为 False
_file_btn = run_btn_file if isinstance(run_btn_file, bool) else False
run_btn   = run_btn_paste or _file_btn
user_input = st.session_state["ref_text"]

# ─── 状态配置 ───────────────────────────────────────────────
STATUS_CONFIG = {
    STATUS_REAL:       {"label": "✅ 真实文献", "card": "real",       "badge": "real"},
    STATUS_UNCERTAIN:  {"label": "⚠️ 待确认",   "card": "uncertain",  "badge": "uncertain"},
    STATUS_SUSPICIOUS: {"label": "❌ 可疑文献", "card": "suspicious", "badge": "suspicious"},
}


def render_card(index: int, raw: str, ref, result, style: str):
    """渲染单条检测结果卡片（带置信度条）"""
    cfg = STATUS_CONFIG[result.status]

    # 元数据行
    meta_parts = []
    if ref.title:
        meta_parts.append(f"<b>标题:</b> {ref.title}")
    if ref.year:
        meta_parts.append(f"<b>年份:</b> {ref.year}")
    if result.evidence_doi:
        meta_parts.append(
            f'<b>DOI:</b> <a href="https://doi.org/{result.evidence_doi}" target="_blank">'
            f'{result.evidence_doi}</a>'
        )
    elif ref.doi:
        meta_parts.append(f"<b>DOI:</b> {ref.doi}")
    meta_parts.append(f"<b>说明:</b> {result.message}")
    meta_html = "<br>".join(meta_parts)

    # 置信度条
    pct = int(result.confidence * 100)
    bar_cls = f"conf-bar-fill conf-bar-fill-{cfg['card']}"
    conf_html = f"""
    <div class="conf-bar-wrap">
        <span class="conf-label" style="color:#333;">置信度</span>
        <div class="conf-bar">
            <div class="{bar_cls}" style="width:{pct}%"></div>
        </div>
        <span class="conf-label">{pct}%</span>
    </div>
    """

    card_html = f"""
    <div class="ref-card ref-card-{cfg['card']}">
        <span class="badge badge-{cfg['badge']}">{cfg['label']}</span>
        <span class="card-idx">#{index}</span>
        <div class="card-title">{raw[:150]}{'...' if len(raw) > 150 else ''}</div>
        <div class="meta">{meta_html}</div>
        {conf_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    # 格式化输出
    if result.is_real and result.crossref_item:
        item = result.crossref_item
        if not item.get("title", [""])[0]:
            item["title"] = [result.evidence_title or ref.title or ""]
        formatted = format_reference(item, style)
        if formatted:
            st.markdown(
                f'<div class="fmt-box">'
                f'<span class="fmt-label">📝 {selected_style_name}</span><br>'
                f'{formatted}</div>',
                unsafe_allow_html=True,
            )
            return formatted
    return None


def run_check(text: str, style: str):
    """执行批量检测"""
    refs_text = split_references(text)
    if not refs_text:
        st.warning("未识别出有效的参考文献，请检查输入格式。")
        return

    total = len(refs_text)
    counts = {STATUS_REAL: 0, STATUS_UNCERTAIN: 0, STATUS_SUSPICIOUS: 0}
    formatted_list = []

    # 进度条
    progress = st.progress(0, text="🔍 正在检测中...")

    for i, raw in enumerate(refs_text):
        ref = parse_reference(raw)
        result = verify(ref)
        counts[result.status] += 1

        fmt = render_card(i + 1, raw, ref, result, style)
        if fmt:
            formatted_list.append(fmt)

        progress.progress((i + 1) / total, text=f"🔍 已检测 {i + 1}/{total} 条")

    progress.empty()

    # ── 统计卡片 ──
    st.markdown("---")
    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-card stat-total">{total}<small>📊 总计</small></div>
        <div class="stat-card stat-real">{counts[STATUS_REAL]}<small>✅ 真实</small></div>
        <div class="stat-card stat-uncertain">{counts[STATUS_UNCERTAIN]}<small>⚠️ 待确认</small></div>
        <div class="stat-card stat-fake">{counts[STATUS_SUSPICIOUS]}<small>❌ 可疑</small></div>
    </div>
    """, unsafe_allow_html=True)

    # ── 汇总复制区 ──
    if formatted_list:
        st.markdown("---")
        st.markdown(f"### 📋 规范格式参考文献（{selected_style_name}）")
        st.caption("可直接全选复制下方内容到论文中")

        copy_text = ""
        for i, ref in enumerate(formatted_list, 1):
            copy_text += f"[{i}] {ref}\n"

        st.code(copy_text.strip(), language=None)

    # ── 底部提示 ──
    if counts[STATUS_SUSPICIOUS] > 0:
        st.error(
            f"🚨 发现 **{counts[STATUS_SUSPICIOUS]} 条可疑文献**，大概率是 AI 编造的，建议删除或替换为真实文献。"
        )
    if counts[STATUS_UNCERTAIN] > 0:
        st.warning(
            f"⚠️ **{counts[STATUS_UNCERTAIN]} 条文献待确认**，建议在知网 / 万方 / Google Scholar 手动核查。"
        )
    if counts[STATUS_SUSPICIOUS] == 0 and counts[STATUS_UNCERTAIN] == 0:
        st.success("🎉 所有文献均通过验证！可直接复制上方规范格式使用。")
    elif formatted_list:
        st.info(f"💡 已为 {len(formatted_list)} 条真实文献生成 {selected_style_name} 规范格式。")


# ─── 触发检测 ───────────────────────────────────────────────
if run_btn and user_input.strip():
    run_check(user_input, selected_style)
elif run_btn:
    st.info("👆 请先粘贴参考文献，或点击「加载示例」试用。")

# ─── 底部 Footer ────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#aaa;font-size:0.78rem;padding:0.5rem 0 1rem;'>"
    "RefCheck v2.1 · 数据源 CrossRef API · "
    "支持格式: GB/T 7714 · APA · MLA · Chicago · IEEE · 支持 .txt 文件上传"
    "</div>",
    unsafe_allow_html=True,
)
