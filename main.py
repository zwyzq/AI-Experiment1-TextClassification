"""
实验一：新闻文本 10 分类
流程：加载数据 -> 划分验证集 -> TF-IDF -> 多模型训练与调参 -> 选最优模型预测测试集
"""

import re
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix

# ---------- 固定随机种子，保证可复现 ----------
RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "outputs"
OUT_DIR.mkdir(exist_ok=True)


def clean_text(text: str) -> str:
    """简单清洗：去掉邮件头噪声、多余空白，保留正文语义。"""
    text = str(text)
    # 去掉常见邮件头行（From/Subject 等仍可能含主题词，这里只去 Organization/Lines 等元数据）
    lines = []
    for line in text.splitlines():
        if re.match(r"^(Organization|Lines|NNTP-Posting-Host|X-Newsreader|Path):", line, re.I):
            continue
        lines.append(line)
    text = " ".join(lines)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_data():
    train_df = pd.read_csv(DATA_DIR / "train_data.csv")
    test_df = pd.read_csv(DATA_DIR / "test_data_unlabeled.csv")
    X_train = [clean_text(t) for t in train_df["text"].astype(str).tolist()]
    y_train = train_df["target"].values
    X_test = [clean_text(t) for t in test_df["text"].astype(str).tolist()]
    return X_train, y_train, X_test


def evaluate(y_true, y_pred, name: str):
    acc = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average="macro")
    print(f"[{name}] accuracy={acc:.4f}  macro-F1={macro_f1:.4f}")
    return {"name": name, "accuracy": float(acc), "macro_f1": float(macro_f1)}


def main():
    print("=== 1. 加载数据 ===")
    X, y, X_test_unlabeled = load_data()
    print(f"训练集: {len(X)}  测试集(无标签): {len(X_test_unlabeled)}")
    print(f"类别分布: {dict(zip(*np.unique(y, return_counts=True)))}")

    print("\n=== 2. 划分训练集 / 验证集 (8:2, 分层) ===")
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    print(f"训练: {len(X_train)}  验证: {len(X_val)}")

    print("\n=== 3. TF-IDF 特征 ===")
    # 仅在训练集上 fit，避免数据泄露
    vectorizer = TfidfVectorizer(
        max_features=20000,
        ngram_range=(1, 2),
        min_df=2,
        sublinear_tf=True,
        stop_words="english",
    )
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_val_tfidf = vectorizer.transform(X_val)
    print(f"特征维度: {X_train_tfidf.shape[1]}")

    results = []

    print("\n=== 4. 模型训练与验证集比较 ===")

    # ---- 朴素贝叶斯：调 alpha ----
    best_nb, best_nb_score = None, -1
    for alpha in [0.01, 0.1, 0.5, 1.0]:
        clf = MultinomialNB(alpha=alpha)
        clf.fit(X_train_tfidf, y_train)
        pred = clf.predict(X_val_tfidf)
        m = evaluate(y_val, pred, f"MultinomialNB(alpha={alpha})")
        results.append(m)
        if m["macro_f1"] > best_nb_score:
            best_nb_score, best_nb = m["macro_f1"], (clf, alpha, m)

    # ---- 逻辑回归：调 C ----
    best_lr, best_lr_score = None, -1
    for C in [0.1, 1.0, 10.0, 20.0]:
        clf = LogisticRegression(
            C=C, max_iter=2000, random_state=RANDOM_STATE, n_jobs=-1
        )
        clf.fit(X_train_tfidf, y_train)
        pred = clf.predict(X_val_tfidf)
        m = evaluate(y_val, pred, f"LogisticRegression(C={C})")
        results.append(m)
        if m["macro_f1"] > best_lr_score:
            best_lr_score, best_lr = m["macro_f1"], (clf, C, m)

    # ---- 线性 SVM：调 C（LinearSVC 比 SVC(kernel=linear) 更快）----
    best_svm, best_svm_score = None, -1
    for C in [0.1, 1.0, 5.0, 10.0]:
        clf = LinearSVC(C=C, max_iter=5000, random_state=RANDOM_STATE)
        clf.fit(X_train_tfidf, y_train)
        pred = clf.predict(X_val_tfidf)
        m = evaluate(y_val, pred, f"LinearSVC(C={C})")
        results.append(m)
        if m["macro_f1"] > best_svm_score:
            best_svm_score, best_svm = m["macro_f1"], (clf, C, m)

    # ---- MLP：少量结构对比（训练较慢）----
    best_mlp, best_mlp_score = None, -1
    mlp_cfgs = [
        {"hidden_layer_sizes": (100,), "alpha": 0.0001},
        {"hidden_layer_sizes": (200,), "alpha": 0.001},
        {"hidden_layer_sizes": (100, 50), "alpha": 0.001},
    ]
    for cfg in mlp_cfgs:
        clf = MLPClassifier(
            max_iter=300,
            random_state=RANDOM_STATE,
            early_stopping=True,
            validation_fraction=0.1,
            **cfg,
        )
        print(f"训练 MLP {cfg} ...")
        clf.fit(X_train_tfidf, y_train)
        pred = clf.predict(X_val_tfidf)
        tag = f"MLP(h={cfg['hidden_layer_sizes']}, alpha={cfg['alpha']})"
        m = evaluate(y_val, pred, tag)
        results.append(m)
        if m["macro_f1"] > best_mlp_score:
            best_mlp_score, best_mlp = m["macro_f1"], (clf, cfg, m)

    candidates = [
        ("MultinomialNB", best_nb[0], {"alpha": best_nb[1]}, best_nb[2]),
        ("LogisticRegression", best_lr[0], {"C": best_lr[1]}, best_lr[2]),
        ("LinearSVC", best_svm[0], {"C": best_svm[1]}, best_svm[2]),
        ("MLPClassifier", best_mlp[0], best_mlp[1], best_mlp[2]),
    ]
    best_name, best_model, best_params, best_metrics = max(
        candidates, key=lambda x: x[3]["macro_f1"]
    )
    print("\n=== 5. 验证集最优 ===")
    print(f"模型: {best_name}  参数: {best_params}")
    print(f"accuracy={best_metrics['accuracy']:.4f}  macro-F1={best_metrics['macro_f1']:.4f}")

    # 详细报告（最优模型在当前验证划分上）
    y_val_pred = best_model.predict(X_val_tfidf)
    report = classification_report(y_val, y_val_pred, digits=4)
    cm = confusion_matrix(y_val, y_val_pred)
    print("\n分类报告:\n", report)

    print("\n=== 6. 用全部有标签数据重训最优配置，预测测试集 ===")
    vectorizer_full = TfidfVectorizer(
        max_features=20000,
        ngram_range=(1, 2),
        min_df=2,
        sublinear_tf=True,
        stop_words="english",
    )
    X_all_tfidf = vectorizer_full.fit_transform(X)
    X_test_tfidf = vectorizer_full.transform(X_test_unlabeled)

    if best_name == "MultinomialNB":
        final_clf = MultinomialNB(alpha=best_params["alpha"])
    elif best_name == "LogisticRegression":
        final_clf = LogisticRegression(
            C=best_params["C"], max_iter=2000, random_state=RANDOM_STATE, n_jobs=-1
        )
    elif best_name == "LinearSVC":
        final_clf = LinearSVC(C=best_params["C"], max_iter=5000, random_state=RANDOM_STATE)
    else:
        final_clf = MLPClassifier(
            max_iter=300,
            random_state=RANDOM_STATE,
            early_stopping=True,
            validation_fraction=0.1,
            **best_params,
        )

    final_clf.fit(X_all_tfidf, y)
    predictions = final_clf.predict(X_test_tfidf)

    pred_path = ROOT / "predictions.csv"
    pd.DataFrame(predictions).to_csv(pred_path, index=False, header=False)
    print(f"已保存预测: {pred_path}  ({len(predictions)} 行)")

    # 保存实验记录，方便写报告
    summary = {
        "random_state": RANDOM_STATE,
        "tfidf": {
            "max_features": 20000,
            "ngram_range": [1, 2],
            "min_df": 2,
            "sublinear_tf": True,
            "stop_words": "english",
        },
        "val_split": 0.2,
        "all_results": results,
        "best_model": best_name,
        "best_params": best_params,
        "best_val_metrics": best_metrics,
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
    }
    with open(OUT_DIR / "experiment_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    with open(OUT_DIR / "classification_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    np.save(OUT_DIR / "confusion_matrix.npy", cm)
    print(f"实验摘要已写入 {OUT_DIR / 'experiment_summary.json'}")
    print("完成。")


if __name__ == "__main__":
    main()
