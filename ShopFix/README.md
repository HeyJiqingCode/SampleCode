# 快速入门指南

## 1. 环境设置

确保您已经安装了Python 3.7+，然后安装依赖：

```bash
pip install -r requirements.txt
```

## 2. 准备文件

确保您有以下文件：

- `standard_shop_name.csv` - 标准店铺名称列表（每行一个店铺名称）
- 您的Azure AI Content Understanding JSON结果文件

## 3. 基本使用

### 处理单个文件

```bash
python shop_name_matcher.py \
    --input your_original_results.json \
    --output your_matched_results.json \
    --report matching_report.json
```

### 批量处理多个文件

```bash
python batch_processor.py \
    --input-dir ./input_folder \
    --output-dir ./output_folder
```

## 4. 调整参数

根据您的需求调整相似度阈值：

```bash
python shop_name_matcher.py \
    --input your_file.json \
    --output matched_file.json \
    --lev-threshold 0.85 \
    --jw-threshold 0.90
```

- **提高阈值** (0.9+): 更严格的匹配，减少误匹配
- **降低阈值** (0.7-): 更宽松的匹配，可能增加误匹配

## 5. 查看结果

程序会生成：

1. **匹配后的JSON文件** - 与原文件结构相同，但店铺名称已被标准化
2. **替换报告** - 显示所有替换的详细信息