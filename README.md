# 实验一：新闻文本分类

当代人工智能实验课 - 文本分类（TF-IDF + 经典机器学习）

## 环境

建议 Python ≥ 3.8，已用 Anaconda 验证：

```bash
conda create -n project1 python=3.10 -y
conda activate project1
pip install -r requirements.txt
```

若本机已有 `numpy` / `pandas` / `scikit-learn`，可直接运行。

## 数据

将官方数据包中的 CSV 放到 `data/`：

- `data/train_data.csv`
- `data/test_data_unlabeled.csv`

## 运行

在项目根目录执行：

```bash
python main.py
```

脚本会：

1. 清洗文本并按 8:2 分层划分训练/验证集  
2. 仅用训练集拟合 TF-IDF  
3. 比较 MultinomialNB / LogisticRegression / LinearSVC / MLP 在验证集上的表现并调参  
4. 用最优配置在全部有标签数据上重训，对测试集预测  
5. 生成 `predictions.csv` 与 `outputs/experiment_summary.json`

## 提交物

- `predictions.csv`：每行一个类别预测（无表头）  
- 实验报告 PDF（开头附本仓库链接）  
- 本仓库代码

## 随机种子

`RANDOM_STATE = 42`，保证结果可复现。
