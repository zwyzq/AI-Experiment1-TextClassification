#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""根据 experiment_summary.json / confusion_matrix.npy 重画中文标注图表。"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"


def setup_chinese_font() -> str:
    candidates = [
        "PingFang HK",
        "PingFang SC",
        "Hiragino Sans GB",
        "Songti SC",
        "Heiti TC",
        "STHeiti",
        "Arial Unicode MS",
    ]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            plt.rcParams["font.sans-serif"] = [name, "DejaVu Sans"]
            plt.rcParams["axes.unicode_minus"] = False
            print(f"matplotlib font: {name}")
            return name
    # fallback by path
    path_candidates = [
        "/System/Library/Fonts/Supplemental/Songti.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
    ]
    for p in path_candidates:
        if Path(p).exists():
            font_manager.fontManager.addfont(p)
            prop = font_manager.FontProperties(fname=p)
            name = prop.get_name()
            plt.rcParams["font.sans-serif"] = [name, "DejaVu Sans"]
            plt.rcParams["axes.unicode_minus"] = False
            print(f"matplotlib font via path: {name} ({p})")
            return name
    raise RuntimeError("未找到可用中文字体")


def load_summary():
    with open(OUT / "experiment_summary.json", encoding="utf-8") as f:
        return json.load(f)


def plot_model_comparison(summary):
    # 各算法最优
    best = {
        "多项式朴素贝叶斯": 0.9213,
        "逻辑回归": 0.9417,
        "线性SVM": 0.9444,
        "多层感知机": 0.9403,
    }
    # 从 summary 再核对一遍
    mapping = [
        ("多项式朴素贝叶斯", "MultinomialNB(alpha=0.01)"),
        ("逻辑回归", "LogisticRegression(C=20.0)"),
        ("线性SVM", "LinearSVC(C=1.0)"),
        ("多层感知机", "MLP(h=(200,), alpha=0.001)"),
    ]
    names, accs = [], []
    by_name = {r["name"]: r["accuracy"] for r in summary["all_results"]}
    for cn, en in mapping:
        names.append(cn)
        accs.append(by_name.get(en, best[cn]))

    fig, ax = plt.subplots(figsize=(8.2, 3.6), dpi=140)
    colors = ["#7BA3C9", "#5B8DB8", "#2F5D9F", "#8FA9C4"]
    bars = ax.bar(names, accs, color=colors, width=0.62, edgecolor="white", linewidth=0.6)
    ax.set_ylim(0.88, 0.96)
    ax.set_ylabel("验证集准确率")
    ax.set_title("各模型验证集准确率对比（取各算法最优超参）", fontsize=12, pad=10)
    ax.axhline(max(accs), color="#C0392B", linestyle="--", linewidth=0.9, alpha=0.7)
    for b, v in zip(bars, accs):
        ax.text(
            b.get_x() + b.get_width() / 2,
            v + 0.0015,
            f"{v:.4f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle=":", alpha=0.45)
    fig.tight_layout()
    fig.savefig(OUT / "model_comparison.png", bbox_inches="tight")
    plt.close(fig)


def plot_c_curves(summary):
    by_name = {r["name"]: r["accuracy"] for r in summary["all_results"]}

    # LinearSVC
    cs_svm = [0.1, 1.0, 5.0, 10.0]
    acc_svm = [by_name[f"LinearSVC(C={c})"] for c in cs_svm]
    fig, ax = plt.subplots(figsize=(5.2, 3.6), dpi=140)
    ax.plot(cs_svm, acc_svm, "o-", color="#2F5D9F", linewidth=2, markersize=7)
    best_i = int(np.argmax(acc_svm))
    ax.scatter([cs_svm[best_i]], [acc_svm[best_i]], s=90, color="#C0392B", zorder=5, label="最优")
    ax.set_xscale("log")
    ax.set_xticks(cs_svm)
    ax.set_xticklabels([str(c) for c in cs_svm])
    ax.set_xlabel("正则参数 C（对数坐标）")
    ax.set_ylabel("验证集准确率")
    ax.set_title("LinearSVC：C 对验证准确率的影响", fontsize=11, pad=8)
    ax.grid(True, linestyle=":", alpha=0.45)
    ax.legend(frameon=False, loc="lower right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for c, a in zip(cs_svm, acc_svm):
        ax.annotate(f"{a:.4f}", (c, a), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "svm_c_curve.png", bbox_inches="tight")
    plt.close(fig)

    # LogisticRegression
    cs_lr = [0.1, 1.0, 10.0, 20.0]
    acc_lr = [by_name[f"LogisticRegression(C={c})"] for c in cs_lr]
    fig, ax = plt.subplots(figsize=(5.2, 3.6), dpi=140)
    ax.plot(cs_lr, acc_lr, "s-", color="#1A7A5C", linewidth=2, markersize=7)
    best_i = int(np.argmax(acc_lr))
    ax.scatter([cs_lr[best_i]], [acc_lr[best_i]], s=90, color="#C0392B", zorder=5, label="最优")
    ax.set_xscale("log")
    ax.set_xticks(cs_lr)
    ax.set_xticklabels([str(c) for c in cs_lr])
    ax.set_xlabel("正则参数 C（对数坐标）")
    ax.set_ylabel("验证集准确率")
    ax.set_title("逻辑回归：C 对验证准确率的影响", fontsize=11, pad=8)
    ax.grid(True, linestyle=":", alpha=0.45)
    ax.legend(frameon=False, loc="lower right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for c, a in zip(cs_lr, acc_lr):
        ax.annotate(f"{a:.4f}", (c, a), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "lr_c_curve.png", bbox_inches="tight")
    plt.close(fig)


def plot_confusion(summary):
    cm = np.array(summary["confusion_matrix"], dtype=int)
    npy_path = OUT / "confusion_matrix.npy"
    if npy_path.exists():
        cm = np.load(npy_path)

    fig, ax = plt.subplots(figsize=(6.2, 5.4), dpi=140)
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(10))
    ax.set_yticks(range(10))
    ax.set_xticklabels([str(i) for i in range(10)])
    ax.set_yticklabels([str(i) for i in range(10)])
    ax.set_xlabel("预测类别")
    ax.set_ylabel("真实类别")
    ax.set_title("最优模型 LinearSVC(C=1.0) 验证集混淆矩阵", fontsize=11, pad=10)
    for i in range(10):
        for j in range(10):
            v = int(cm[i, j])
            color = "white" if v > cm.max() * 0.55 else "#222222"
            ax.text(j, i, str(v), ha="center", va="center", color=color, fontsize=8)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("样本数")
    fig.tight_layout()
    fig.savefig(OUT / "confusion_matrix.png", bbox_inches="tight")
    plt.close(fig)


def main():
    setup_chinese_font()
    summary = load_summary()
    plot_model_comparison(summary)
    plot_c_curves(summary)
    plot_confusion(summary)
    print("figures written to", OUT)


if __name__ == "__main__":
    main()
