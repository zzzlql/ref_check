<<<<<<< HEAD
# RefCheck — AI 生成文献检测与规范系统

> 粘贴参考文献，一键检测真伪，自动输出规范格式。

---

## 项目背景

学生使用 AI 写作论文时，AI 经常产生两类问题：

1. **幻觉文献**：AI 编造看似合理但实际不存在的参考文献
2. **格式混乱**：真实文献的引用格式不符合学术规范

RefCheck 通过 CrossRef API 对文献进行真实性验证，并支持将真实文献自动转换为多种标准引用格式。

---

## 功能特性

| 功能 | 说明 |
|------|------|
| 🔍 **真伪检测** | 接入 CrossRef 数据库，验证文献是否真实存在 |
| 📊 **三级判定** | 真实 / 待确认 / 可疑，每条附置信度与证据链接 |
| 📝 **格式规范** | 支持 GB/T 7714、APA、MLA、Chicago、IEEE 五种格式 |
| 📦 **批量处理** | 支持一次粘贴多条文献，自动拆分逐条验证 |
| 🌐 **Web 界面** | Streamlit 网页，粘贴即检测，结果可一键复制 |
| 📂 **文件上传** | 直接上传 `.txt` 文件，自动识别 UTF-8 / GBK 编码 |
| 💻 **命令行** | 也支持终端交互模式和 demo 模式 |

---

## 环境要求

- Python 3.10+
- 网络连接（调用 CrossRef API，免费无需注册）

---

## 安装步骤

```bash
# 1. 克隆或下载项目
cd project1

# 2. 安装依赖
pip install -r requirements.txt
```

`requirements.txt` 内容：

```
requests>=2.28.0
streamlit>=1.30.0
```

---

## 启动方式

### 方式一：Web 界面（推荐）

```bash
streamlit run app.py
```

浏览器访问 `http://localhost:8501`

### 方式二：命令行交互模式

```bash
python main.py
```

指定输出格式：

```bash
python main.py --style apa
python main.py --style ieee
```

### 方式三：内置示例演示

```bash
python main.py --demo
python main.py --demo --style chicago
```

---

## Web 界面使用流程

```
1. 打开浏览器，访问 http://localhost:8501
2. 在侧边栏选择引用格式（默认 GB/T 7714）
3. 在文本框粘贴参考文献
4. 点击「开始检测」
5. 查看每条文献的检测结果（真实 / 待确认 / 可疑）
6. 底部汇总区直接复制规范格式文献列表
```

**快捷操作：**
- 点击「加载示例」可快速体验功能
- 点击「清空」清除输入框

---

## 支持的输入格式

RefCheck 内置格式识别引擎，**自动检测**引用格式，无需手动指定，支持 10 种主流格式：

| 格式 | 典型模式 | 示例 |
|------|----------|------|
| **ACS** | `Lastname, F. M.; Lastname, F. M. Title.` | `Vaswani, A.; Shazeer, N. Attention Is All You Need. NeurIPS 2017.` |
| **APA 7th** | `Lastname, F. M. (Year). Title.` | `LeCun, Y. (2015). Deep learning. Nature, 521, 436.` |
| **GB/T 7714** | `作者. 标题[J]. 期刊, 年份.` | `张伟, 李明. 深度学习综述[J]. 计算机学报, 2020.` |
| **Vancouver/NLM** | `Lastname AB, Lastname CD. Title. J.` | `LeCun Y, Bengio Y. Deep learning. Nature. 2015;521:436.` |
| **Nature/Science** | `Lastname, F. & Lastname, F. Title. Journal Vol (Year).` | `LeCun, Y. & Hinton, G. Deep learning. Nature 521, 436 (2015).` |
| **Harvard** | `Lastname, F. (Year) 'Title', Journal.` | `Vaswani, A. (2017) 'Attention is all you need', NeurIPS.` |
| **IEEE** | `F. M. Lastname, "Title," Journal.` | `A. Vaswani et al., "Attention is all you need," NeurIPS, 2017.` |
| **MLA 9th** | `Lastname, Firstname. "Title." Journal.` | `Vaswani, Ashish. "Attention Is All You Need." NeurIPS, 2017.` |
| **Chicago 17th** | `Lastname, Firstname. "Title." Journal Vol.` | `LeCun, Yann. "Deep Learning." Nature 521 (2015): 436.` |
| **BibTeX** | `@article{key, title={Title}, ...}` | `@article{v2017, title={Attention is all you need}, ...}` |

**通用特性（所有格式均支持）：**
- 带编号前缀：`[1]`、`(1)`、`1.` 自动去除
- 带 DOI：`DOI: 10.xxxx/xxx` 自动提取，优先精确匹配
- 多条批量输入：自动按行或按编号拆分

---

## 检测结果说明

| 状态 | 含义 | 建议操作 |
|------|------|----------|
| ✅ **真实** | CrossRef 验证通过，置信度高 | 可直接使用，已自动生成规范格式 |
| ⚠️ **待确认** | CrossRef 未能明确匹配（常见于中文文献） | 在知网 / 万方 / Google Scholar 手动核查 |
| ❌ **可疑** | 相似度过低，大概率为 AI 编造 | 建议删除或替换为真实文献 |

> **注意**：CrossRef 主要收录英文期刊文献，中文文献覆盖率较低，中文文献出现「待确认」属正常情况。

---

## 支持的输出格式

| 格式 | 示例 |
|------|------|
| **GB/T 7714** | `VASWANI A, SHAZEER N, et al. Attention is all you need[J]. NeurIPS, 2017, 30: 5998-6008.` |
| **APA 7th** | `Vaswani, A., Shazeer, N., ... & Polosukhin, I. (2017). Attention is all you need. *NeurIPS*, *30*, 5998–6008.` |
| **MLA 9th** | `Vaswani, Ashish, et al. "Attention Is All You Need." *NeurIPS*, vol. 30, 2017, pp. 5998-6008.` |
| **Chicago 17th** | `Vaswani, Ashish, et al. "Attention Is All You Need." *NeurIPS* 30 (2017): 5998-6008.` |
| **IEEE** | `A. Vaswani et al., "Attention is all you need," *NeurIPS*, vol. 30, pp. 5998-6008, 2017.` |

---

## 项目结构

```
project1/
├── app.py                    # Streamlit Web 界面 v2.0
├── main.py                   # 命令行入口
├── requirements.txt          # 依赖列表
├── README.md                 # 使用说明
├── test_verify.py            # 真伪判定测试（4 真 + 4 假）
├── test_real_refs.py         # 真实文献压力测试（27 条 ACS 格式）
├── test_parser.py            # 解析器格式覆盖测试（10 种格式 × 17 用例）
└── ref_checker/
    ├── __init__.py
    ├── parser.py             # 文献解析（格式识别 + 10 种专用提取器）
    ├── verifier.py           # CrossRef API 验证，三维相似度算法
    ├── formatter.py          # 五种格式化输出
    └── splitter.py           # 批量文献拆分
```

---

## 验证效果

| 测试集 | 通过率 |
|--------|--------|
| 格式解析覆盖（10 种格式，17 用例） | 17/17 (100%) |
| 真实文献检测（27 条 ACS 格式） | 27/27 (100%) |
| 真伪判定（4 条真实 + 4 条 AI 虚假） | 8/8 (100%) |

---

## 常见问题

**Q：检测速度较慢？**
A：每条文献需调用 CrossRef API，网络延迟约 1-3 秒/条，10 条文献约需 15-30 秒，属正常情况。

**Q：中文文献全部显示「待确认」？**
A：CrossRef 主要收录英文文献，中文文献建议在知网（cnki.net）或万方数据库二次核查。

**Q：某条明明真实的文献被判为「可疑」？**
A：可能原因：①标题拼写与数据库不一致；②该文献未被 CrossRef 收录（部分小众期刊）；③标题提取失败。可尝试在文献中手动添加 DOI 后重新检测（DOI 验证精确度为 99%+）。

**Q：Windows 下运行出现乱码？**
A：`main.py` 已内置 GBK→UTF-8 转换，如仍有问题可在终端执行 `chcp 65001` 后再运行。

---

## 技术栈

- **后端**：Python 3.10+，requests
- **API**：CrossRef REST API（免费，无需注册）
- **解析引擎**：格式自动识别 + 10 种专用提取器（ACS / APA / GB/T / Vancouver / Nature / Harvard / IEEE / MLA / Chicago / BibTeX）
- **相似度算法**：SequenceMatcher (50%) + 关键词 Jaccard (40%) + 长度惩罚 (10%)
- **前端**：Streamlit 1.30+

---

## 版本历史

| 版本 | 主要功能 |
|------|----------|
| v0.1 | 核心检测功能，单条验证 |
| v0.2 | 批量检测，splitter 模块，三级判定 |
| v0.3 | 优化相似度算法，新增 APA 格式规范 |
| v0.4 | 新增 MLA / Chicago / IEEE 格式；Streamlit Web 界面 v2.0；修复 ACS 格式解析 |
| v0.5 | 解析器重构：新增 Vancouver、Nature/Science、Harvard、BibTeX 格式；引入格式自动识别引擎；格式解析准确率 100% (17/17) |
| v0.6 | 新增 .txt 文件上传功能；输入区改为 Tab 布局（粘贴 / 上传）；自动识别 UTF-8 / GBK / GB18030 编码；文件预览、大小限制、一键移除 |
=======
# ref_check
针对AI生成文献进行检测以及输出格式规范矫正
>>>>>>> origin/main
