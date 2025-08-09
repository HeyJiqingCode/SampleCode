# SimilarityCheck - 图像相似度检测系统

基于 Azure Computer Vision 和 Azure Cognitive Search 的图像相似度检测系统，能够将图像转换为向量并在向量数据库中搜索相似图像。

## 功能特性

- **图像向量化**：使用 Azure Computer Vision API 将图像转换为1024维向量
- **相似度搜索**：基于向量相似度在 Azure Cognitive Search 中查找最相似的图像
- **安全访问**：自动生成 Azure Blob Storage 的 SAS 令牌，安全访问图像资源
- **可配置结果**：支持自定义返回的相似图像数量

## 文件说明

- `images_05.jpg`：示例查询图片文件
- `images_search.py`：核心图像相似度检测程序
- `requirements.txt`：项目依赖库列表

## 核心功能模块

### 1. 图像向量化 (`vectorize_image`)
- 调用 Azure Computer Vision API
- 将图像转换为1024维特征向量
- 支持多种图像格式

### 2. 相似度搜索 (`search_similar`)
- 在 Azure Cognitive Search 索引中进行向量搜索
- 返回指定数量的最相似图像
- 包含相似度评分信息

### 3. URL 生成 (`generate_blob_url`)
- 为 Azure Blob Storage 中的图像生成安全访问链接
- 自动创建带有过期时间的 SAS 令牌
- 支持中文文件名的 URL 编码

## 环境配置

在项目根目录创建 `.env` 文件，配置以下环境变量：

```env
# Azure Computer Vision
VISION_ENDPOINT=your_vision_endpoint
VISION_KEY=your_vision_key
API_VISION=2024-02-01
MODEL_VERSION=2023-04-15

# Azure Cognitive Search
SEARCH_SERVICE=your_search_service_name
SEARCH_INDEX=your_search_index_name
SEARCH_ADMIN_KEY=your_search_admin_key
API_SEARCH=2024-07-01
VECTOR_FIELD=your_vector_field_name

# Azure Storage
STORAGE_CONNECTION_STRING=your_storage_connection_string
CONTAINER_NAME=your_container_name

# 查询配置
QUERY_IMAGE_PATH=images_05.jpg
TOP_K=3
```

## 使用方法

1. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境变量**：
   创建并配置 `.env` 文件（参考上面的环境配置）

3. **运行程序**：
   ```bash
   python images_search.py
   ```

## 输出示例

```
Top 3 matches
 1. score=0.892
    title: similar_image_1.jpg
    url: https://yourstorageaccount.blob.core.windows.net/container/similar_image_1.jpg?sas_token

 2. score=0.845
    title: similar_image_2.jpg
    url: https://yourstorageaccount.blob.core.windows.net/container/similar_image_2.jpg?sas_token

 3. score=0.821
    title: similar_image_3.jpg
    url: https://yourstorageaccount.blob.core.windows.net/container/similar_image_3.jpg?sas_token
```

## 技术架构

- **Azure Computer Vision**：图像特征提取和向量化
- **Azure Cognitive Search**：向量索引和相似度搜索
- **Azure Blob Storage**：图像文件存储和访问
- **Python**：主要开发语言，使用 requests 和 azure-storage-blob 库

## 适用场景

- 电商产品图像搜索和推荐
- 内容管理系统中的重复图像检测
- 图像版权保护和侵权检测
- 个人相册中的相似照片整理
- 视觉搜索引擎开发

## 注意事项

- 确保 Azure 服务配额充足
- 注意 API 调用频率限制
- SAS 令牌具有时效性，默认1小时过期
- 向量维度必须为1024，与模型版本匹配

## 错误处理

程序包含完整的错误处理机制：
- HTTP 请求错误处理
- 向量维度验证
- 网络超时保护（30秒）
