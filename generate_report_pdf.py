#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成版式优化的《实验报告.pdf》（中文报告风格，≤5 页 A4）。"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent
OUT_PDF = ROOT / "实验报告.pdf"
OUTPUTS = ROOT / "outputs"

# 宋体：正文；加粗用 Songti.ttc 索引 1（通常为 Bold）
pdfmetrics.registerFont(
    TTFont("Songti", "/System/Library/Fonts/Supplemental/Songti.ttc", subfontIndex=0)
)
pdfmetrics.registerFont(
    TTFont("SongtiBold", "/System/Library/Fonts/Supplemental/Songti.ttc", subfontIndex=1)
)

ACCENT = colors.HexColor("#2F5D9F")
ACCENT_LIGHT = colors.HexColor("#EAF0F8")
TEXT = colors.HexColor("#222222")
MUTED = colors.HexColor("#555555")
GRID = colors.HexColor("#B8C0CC")


class NumberedCanvas(pdfcanvas.Canvas):
    """页脚：第 x 页 / 共 n 页"""

    def __init__(self, *args, **kwargs):
        pdfcanvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        n = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_footer(n)
            pdfcanvas.Canvas.showPage(self)
        pdfcanvas.Canvas.save(self)

    def _draw_footer(self, page_count: int):
        page = self._pageNumber
        self.setStrokeColor(colors.HexColor("#CCCCCC"))
        self.setLineWidth(0.4)
        y = 13 * mm
        self.line(1.5 * cm, y + 5, A4[0] - 1.5 * cm, y + 5)
        self.setFont("Songti", 8)
        self.setFillColor(MUTED)
        self.drawCentredString(A4[0] / 2, y - 1, f"第 {page} 页 / 共 {page_count} 页")


def styles():
    ss = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "CNTitle",
            parent=ss["Title"],
            fontName="SongtiBold",
            fontSize=15,
            leading=20,
            alignment=TA_CENTER,
            textColor=TEXT,
            spaceAfter=2,
        ),
        "meta": ParagraphStyle(
            "CNMeta",
            parent=ss["Normal"],
            fontName="Songti",
            fontSize=10,
            leading=14,
            alignment=TA_CENTER,
            textColor=TEXT,
            spaceAfter=1,
        ),
        "h1_inner": ParagraphStyle(
            "CNH1Inner",
            parent=ss["Normal"],
            fontName="SongtiBold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#1A3358"),
        ),
        "h2": ParagraphStyle(
            "CNH2",
            parent=ss["Heading2"],
            fontName="SongtiBold",
            fontSize=10,
            leading=13,
            spaceBefore=5,
            spaceAfter=2,
            textColor=TEXT,
        ),
        # 中文常规：左对齐 + 首行缩进两字符，避免 justify 中英混排大空隙
        "body": ParagraphStyle(
            "CNBody",
            parent=ss["Normal"],
            fontName="Songti",
            fontSize=9.5,
            leading=14,
            alignment=TA_LEFT,
            firstLineIndent=19,
            spaceAfter=4,
            textColor=TEXT,
        ),
        "body_noindent": ParagraphStyle(
            "CNBodyNoIndent",
            parent=ss["Normal"],
            fontName="Songti",
            fontSize=9,
            leading=13,
            alignment=TA_LEFT,
            firstLineIndent=0,
            spaceAfter=3,
            textColor=TEXT,
        ),
        "caption": ParagraphStyle(
            "CNCaption",
            parent=ss["Normal"],
            fontName="Songti",
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
            spaceBefore=1,
            spaceAfter=3,
            textColor=MUTED,
        ),
        "note": ParagraphStyle(
            "CNNote",
            parent=ss["Normal"],
            fontName="Songti",
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
            textColor=MUTED,
            spaceBefore=2,
        ),
        "cell": ParagraphStyle(
            "CNCell",
            parent=ss["Normal"],
            fontName="Songti",
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
            textColor=TEXT,
        ),
        "cell_l": ParagraphStyle(
            "CNCellL",
            parent=ss["Normal"],
            fontName="Songti",
            fontSize=8,
            leading=10,
            alignment=TA_LEFT,
            textColor=TEXT,
        ),
        "cell_h": ParagraphStyle(
            "CNCellH",
            parent=ss["Normal"],
            fontName="SongtiBold",
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
            textColor=TEXT,
        ),
    }


def P(text: str, style):
    return Paragraph(text.replace("\n", "<br/>"), style)


def section_title(text: str, s) -> Table:
    """一级标题：浅底 + 左侧色条。"""
    inner = Table(
        [[P(text, s["h1_inner"])]],
        colWidths=[17.2 * cm],
    )
    inner.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), ACCENT_LIGHT),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LINEBEFORE", (0, 0), (0, -1), 2.8, ACCENT),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    wrap = Table([[inner]], colWidths=[17.4 * cm])
    wrap.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return wrap


def make_table(data, col_widths):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "SongtiBold"),
                ("FONTNAME", (0, 1), (-1, -1), "Songti"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT_LIGHT),
                ("TEXTCOLOR", (0, 0), (-1, -1), TEXT),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.35, GRID),
                ("TOPPADDING", (0, 0), (-1, -1), 2.2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
                ("LEFTPADDING", (0, 0), (-1, -1), 2.5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2.5),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F8FAFC")],
                ),
            ]
        )
    )
    return t


def fig(path: Path, width_cm: float, height_cm: float | None = None):
    if not path.exists():
        return None
    if height_cm is None:
        # 按常见宽高比估算，避免过大留白
        height_cm = width_cm * 0.48
    im = Image(str(path), width=width_cm * cm, height=height_cm * cm)
    im.hAlign = "CENTER"
    return im


def build():
    s = styles()
    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.8 * cm,
        title="实验一：文本分类 - 钟尉",
        author="钟尉",
    )
    story = []

    # ---- 封面信息 ----
    story.append(P("当代人工智能实验课 · 实验一：文本分类", s["title"]))
    story.append(P("姓名：钟尉　　学号：10245501461", s["meta"]))
    story.append(
        P("<b>GitHub 仓库：</b>（待补充：上传代码后填入仓库 URL）", s["meta"])
    )
    story.append(Spacer(1, 3))
    story.append(
        HRFlowable(
            width="100%",
            thickness=0.8,
            color=ACCENT,
            spaceBefore=1,
            spaceAfter=4,
        )
    )

    # 1
    story.append(section_title("1. 问题与目标", s))
    story.append(
        P(
            "本实验对英文新闻文本进行 <b>10 类分类</b>。给定带标签训练集与无标签测试集，"
            "需完成文本预处理、特征提取、至少两种分类算法的训练与超参数调优，并在验证集上选出最优模型，"
            "对测试集输出 <font face='Courier'>predictions.csv</font>。"
            "代码将托管于 GitHub，本报告开头保留仓库链接占位，上传后补全。",
            s["body"],
        )
    )

    # 2
    story.append(section_title("2. 数据与划分", s))
    story.append(
        make_table(
            [
                [P("数据集", s["cell_h"]), P("规模", s["cell_h"]), P("说明", s["cell_h"])],
                [
                    P("train_data.csv", s["cell"]),
                    P("7368 条", s["cell"]),
                    P("text + target（0–9），各类约 705–747，基本均衡", s["cell_l"]),
                ],
                [
                    P("test_data_unlabeled.csv", s["cell"]),
                    P("2457 条", s["cell"]),
                    P("仅文本，需输出类别预测", s["cell_l"]),
                ],
            ],
            [4.0 * cm, 2.4 * cm, 11.0 * cm],
        )
    )
    story.append(Spacer(1, 2))
    story.append(
        P(
            "划分策略：随机种子 <b>42</b>，按标签 <b>分层抽样</b>，验证集比例 <b>20%</b>"
            "（训练约 5894、验证 1474）。分层保证各类比例与总体一致；测试集不参与调参，"
            "仅用最优模型一次性预测。",
            s["body"],
        )
    )

    # 3
    story.append(section_title("3. 预处理与 TF-IDF 特征", s))
    story.append(P("3.1 文本清洗", s["h2"]))
    story.append(
        P(
            "原始文本含邮件/新闻头元数据（如 Organization、Lines 等）。"
            "实验中用正则去除常见头字段行并规范空白，降低与主题无关的噪声对词袋特征的干扰。",
            s["body"],
        )
    )
    story.append(P("3.2 TF-IDF 向量化", s["h2"]))
    story.append(
        P(
            "采用 TfidfVectorizer：<b>max_features=20000</b>；"
            "<b>ngram_range=(1,2)</b>（unigram+bigram）；"
            "<b>min_df=2</b>；<b>sublinear_tf=True</b>；"
            "<b>stop_words='english'</b>。"
            "得到高维稀疏特征。新闻类别常由少量区分性词/短语决定，稀疏 TF-IDF 与线性分类器匹配良好。",
            s["body"],
        )
    )

    # 4
    story.append(section_title("4. 模型与调参", s))
    story.append(
        P(
            "在同一 TF-IDF 特征上比较四类算法，均在验证集上选超参（随机种子 42）：",
            s["body"],
        )
    )
    story.append(
        make_table(
            [
                [
                    P("算法", s["cell_h"]),
                    P("调参范围", s["cell_h"]),
                    P("最优 Acc", s["cell_h"]),
                    P("最优 Macro-F1", s["cell_h"]),
                ],
                [
                    P("MultinomialNB", s["cell"]),
                    P("α∈{0.01,0.1,0.5,1.0}", s["cell"]),
                    P("0.9213 (α=0.01)", s["cell"]),
                    P("0.9222", s["cell"]),
                ],
                [
                    P("LogisticRegression", s["cell"]),
                    P("C∈{0.1,1,10,20}", s["cell"]),
                    P("0.9417 (C=20)", s["cell"]),
                    P("0.9419", s["cell"]),
                ],
                [
                    P("LinearSVC", s["cell"]),
                    P("C∈{0.1,1,5,10}", s["cell"]),
                    P("<b>0.9444 (C=1.0)</b>", s["cell"]),
                    P("<b>0.9445</b>", s["cell"]),
                ],
                [
                    P("MLPClassifier", s["cell"]),
                    P("(100,)/(200,)/(100,50)+α", s["cell"]),
                    P("0.9403 (h=200)", s["cell"]),
                    P("0.9407", s["cell"]),
                ],
            ],
            [3.5 * cm, 5.0 * cm, 4.4 * cm, 4.5 * cm],
        )
    )
    story.append(Spacer(1, 2))
    story.append(
        P(
            "<b>最终选用 LinearSVC(C=1.0)</b>。用全部训练集在同一向量器上重训后，"
            "对无标签测试集写出 predictions.csv（2457 行）。",
            s["body"],
        )
    )

    # 5
    story.append(section_title("5. 结果与分析", s))
    story.append(P("5.1 模型对比与现象解释", s["h2"]))
    story.append(
        P(
            "验证集上 LinearSVC 略优于逻辑回归与 MLP，显著优于朴素贝叶斯。"
            "<b>稀疏高维文本为何线性模型好？</b> 类别近似线性可分，决策由特征权重直接构成；"
            "参数少、正则清晰，不易像 MLP 那样拟合噪声 n-gram。"
            "SVM 间隔最大化对高维噪声较鲁棒。C=1.0 附近最优，C=5/10 时验证集略降，"
            "说明过强拟合训练噪声会损害泛化。"
            "逻辑回归随 C 增大精度上升，C=20 接近 SVM 但仍低约 0.3 个百分点。"
            "MLP 单隐层 200 维约 94.0%，两层 (100,50) 反而略差，体现参数量增大带来的"
            "<b>过拟合风险</b>——本任务上深层非线性并非必要。",
            s["body"],
        )
    )
    story.append(P("5.2 最优模型各类表现", s["h2"]))
    story.append(
        P(
            "LinearSVC(C=1.0) 验证集 overall accuracy <b>94.44%</b>，macro-F1 <b>94.45%</b>。"
            "类别 5/4/9/8/6 表现最好（F1 多在 0.97+，类 5 近乎完美）；"
            "类 2（F1≈0.86）与类 7（F1≈0.88）相对较弱。"
            "混淆矩阵显示 <b>类 2 与类 7 相互误分最多</b>（2→7 计 8 例，7→2 计 12 例），"
            "提示主题词重叠或文体相近；其余类对角占优。",
            s["body"],
        )
    )

    img_cmp = OUTPUTS / "model_comparison.png"
    img_svm = OUTPUTS / "svm_c_curve.png"
    img_lr = OUTPUTS / "lr_c_curve.png"
    img_cm = OUTPUTS / "confusion_matrix.png"

    # 图1：与 5.3 标题绑在一起，避免标题孤悬在页末
    block = [P("5.3 实验图表", s["h2"])]
    im = fig(img_cmp, 14.8, 5.2)
    if im:
        block.append(im)
        block.append(P("图1　各模型验证集准确率对比（取各算法最优超参）", s["caption"]))
    story.append(KeepTogether(block))

    # 图2：两条 C 曲线并排
    row = []
    im_svm = fig(img_svm, 7.8, 4.5)
    im_lr = fig(img_lr, 7.8, 4.5)
    if im_svm and im_lr:
        t = Table([[im_svm, im_lr]], colWidths=[8.4 * cm, 8.4 * cm])
        t.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 1),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 1),
                ]
            )
        )
        story.append(KeepTogether([
            t,
            P("图2　LinearSVC 的 C 曲线（左）与逻辑回归的 C 曲线（右）", s["caption"]),
        ]))

    # 图3：混淆矩阵（缩小，避免末页空洞）
    im = fig(img_cm, 8.2, 6.8)
    if im:
        story.append(KeepTogether([
            im,
            P("图3　最优模型 LinearSVC(C=1.0) 验证集混淆矩阵", s["caption"]),
        ]))

    # 6
    story.append(section_title("6. 误差分析与思考题", s))
    story.append(
        P(
            "<b>误差原因：</b>(1) 近类主题共享术语，bigram 仍不足；(2) 清洗后仍可能残留签名/引用；"
            "(3) TF-IDF 忽略深层语义与篇章结构。"
            "<b>思考题：</b>"
            "① 线性模型常优于复杂 MLP——高维稀疏、近似线性可分，MLP 易过拟合；"
            "② 稀疏特征下线性模型与稀疏矩阵乘高效，正则可抑制无关维；"
            "③ 应在验证集上选参，分层划分更公平，过大 C/过深网络未必提升泛化。",
            s["body"],
        )
    )

    # 7
    story.append(section_title("7. 结论与局限", s))
    story.append(
        P(
            "本实验完成清洗 + TF-IDF(1–2 gram) + 多模型对比，最终 "
            "<b>LinearSVC(C=1.0)</b> 验证准确率约 <b>94.4%</b>，并生成测试集预测。"
            "局限：未用预训练语言模型；近类（2 与 7）仍易混；未做交叉验证。"
            "后续可尝试字符 n-gram、特征选择、集成或小型 Transformer 微调，并深入近类错误案例。",
            s["body"],
        )
    )
    story.append(
        P(
            "实验环境：Python / scikit-learn；随机种子 42。图表见 outputs/，预测见 predictions.csv。",
            s["note"],
        )
    )

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Wrote {OUT_PDF}")


if __name__ == "__main__":
    build()
