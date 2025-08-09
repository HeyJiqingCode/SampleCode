# AI 图像分类系统

基于 Azure OpenAI 的智能图像分类系统，支持单张图片分类和批量处理，自动计算准确率评估。

## 🚀 功能特性

- **单张图片分类**: 快速处理单个图片 URL
- **批量处理**: 从 CSV 文件读取多个图片进行批量分类  
- **准确率评估**: 自动计算分类准确率和详细对比
- **智能错误处理**: 妥善处理图片加载失败等异常情况
- **结果导出**: 将分类结果保存为 CSV 格式
- **环境变量配置**: 使用 `.env` 文件安全管理配置信息

## ⚙️ 环境配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填入你的 Azure OpenAI 配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# Azure OpenAI 配置
AZURE_OPENAI_ENDPOINT=https://your-resource-name.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_API_VERSION=2025-04-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-5-mini
REASONING_EFFORT=low
REASONING_SUMMARY=auto
```

## 📖 使用方法

### 单张图片分类

```bash
python src/image_classifier.py <image_url>
```

**示例：**
```bash
python src/image_classifier.py "https://example.com/image.jpg"
```

### 批量处理

```bash
python src/image_classifier.py --batch
```

这个命令会：
- 从 `data/samples.csv` 读取输入数据
- 处理每张图片进行分类
- 将结果保存到 `output/results.csv`
- 显示详细的准确率统计

## 📊 输入文件格式

`data/samples.csv` 应包含以下列：

```csv
tags,image_url
火药,https://upload.wikimedia.org/wikipedia/commons/thumb/e/ee/Black_Powder-1.JPG/1920px-Black_Powder-1.JPG
射钉弹,https://img.ltwebstatic.com/images3_spmp/2024/12/23/e2/17349237599ec3884f14bec9acc4ea8bdef13306bd_square.jpg
```

## 📈 输出文件格式

`output/results.csv` 包含以下列：

```csv
tags,image_url,result
火药,https://upload.wikimedia.org/wikipedia/commons/thumb/e/ee/Black_Powder-1.JPG/1920px-Black_Powder-1.JPG,火药
射钉弹,https://img.ltwebstatic.com/images3_spmp/2024/12/23/e2/17349237599ec3884f14bec9acc4ea8bdef13306bd_square.jpg,射钉弹
```

## 🎯 准确率评估

批处理完成后，系统会自动计算并显示：

- **总体准确率**：正确分类数 / 成功处理数
- **详细对比**：预期分类 vs 实际分类的逐项对比
- **处理统计**：成功/失败的图片数量

**示例输出：**
```
Processing Complete.
Results saved to: output/results.csv
Total processed: 6 images
Successfully processed: 4 images
Failed to process: 2 images
Accuracy: 3/4 (75.0%)

Detailed Results:
  ✓ Expected: 火药 | Detected: 火药
  ✗ Expected: 火药 | Detected: Failed
  ✓ Expected: 射钉弹 | Detected: 射钉弹
```

## 🛠️ 技术特性

- **智能图片下载**：自动处理各种图片 URL 格式
- **Base64 转换**：将图片转换为 Azure OpenAI 支持的格式
- **JSON 结果解析**：从 AI 响应中智能提取分类结果
- **CSV 编码处理**：支持 BOM 和多种编码格式
- **错误容错**：单个图片失败不影响整体处理流程

## ⚠️ 注意事项

1. **API 配置**：确保 Azure OpenAI 服务已正确配置并有足够配额
2. **图片访问**：某些图片 URL 可能因权限限制无法访问
3. **处理时间**：大量图片处理需要较长时间，请耐心等待
4. **网络稳定**：建议在稳定的网络环境下运行批处理
5. **数据格式**：确保输入 CSV 文件格式正确且图片 URL 有效

## 🔧 故障排除

**常见问题：**

- **403 错误**：图片 URL 访问被拒绝，系统会标记为处理失败
- **网络超时**：检查网络连接或重试
- **API 配额不足**：检查 Azure OpenAI 服务配额
- **文件路径错误**：确保 `data/samples.csv` 文件存在且格式正确