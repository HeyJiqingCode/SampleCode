#!/usr/bin/env python3
"""
Azure AI Content Understanding 店铺名称匹配器
使用 Levenshtein 和 Jaro-Winkler 算法来匹配OCR识别的店铺名称与标准店铺名称
"""

import json
import csv
import textdistance
from typing import Dict, List, Tuple, Optional
import argparse
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ShopNameMatcher:
    def __init__(self, csv_file: str, levenshtein_threshold: float = 0.8, jaro_winkler_threshold: float = 0.85):
        """
        初始化店铺名称匹配器
        
        Args:
            csv_file: 标准店铺名称CSV文件路径
            levenshtein_threshold: Levenshtein相似度阈值 (0-1)
            jaro_winkler_threshold: Jaro-Winkler相似度阈值 (0-1)
        """
        self.levenshtein_threshold = levenshtein_threshold
        self.jaro_winkler_threshold = jaro_winkler_threshold
        self.standard_shop_names = self._load_standard_names(csv_file)
        
        # 初始化距离计算器
        self.levenshtein = textdistance.levenshtein
        self.jaro_winkler = textdistance.jaro_winkler
        
        logger.info(f"已加载 {len(self.standard_shop_names)} 个标准店铺名称")
        logger.info(f"Levenshtein阈值: {levenshtein_threshold}")
        logger.info(f"Jaro-Winkler阈值: {jaro_winkler_threshold}")
    
    def _load_standard_names(self, csv_file: str) -> List[str]:
        """
        从CSV文件加载标准店铺名称
        
        Args:
            csv_file: CSV文件路径
            
        Returns:
            标准店铺名称列表
        """
        shop_names = []
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                # 假设CSV文件只有一列，每行一个店铺名称
                reader = csv.reader(file)
                for row in reader:
                    if row and row[0].strip():  # 忽略空行
                        shop_names.append(row[0].strip())
        except Exception as e:
            logger.error(f"读取CSV文件失败: {e}")
            raise
        
        return shop_names
    
    def find_best_match(self, ocr_name: str) -> Optional[Tuple[str, float, str]]:
        """
        为OCR识别的店铺名称找到最佳匹配
        
        Args:
            ocr_name: OCR识别的店铺名称
            
        Returns:
            元组 (匹配的标准名称, 相似度, 算法名称) 或 None
        """
        if not ocr_name or not ocr_name.strip():
            return None
        
        ocr_name = ocr_name.strip()
        best_match = None
        best_similarity = 0
        best_algorithm = ""
        
        # 首先检查是否有完全匹配
        if ocr_name in self.standard_shop_names:
            return None  # 完全匹配，无需替换
        
        for standard_name in self.standard_shop_names:
            # 计算 Levenshtein 相似度
            lev_similarity = self.levenshtein.normalized_similarity(ocr_name, standard_name)
            
            # 计算 Jaro-Winkler 相似度
            jw_similarity = self.jaro_winkler.normalized_similarity(ocr_name, standard_name)
            
            # 检查是否超过阈值
            if lev_similarity >= self.levenshtein_threshold and lev_similarity > best_similarity:
                best_match = standard_name
                best_similarity = lev_similarity
                best_algorithm = "Levenshtein"
            
            if jw_similarity >= self.jaro_winkler_threshold and jw_similarity > best_similarity:
                best_match = standard_name
                best_similarity = jw_similarity
                best_algorithm = "Jaro-Winkler"
        
        if best_match:
            return (best_match, best_similarity, best_algorithm)
        
        return None
    
    def process_json_data(self, json_data: Dict) -> Tuple[Dict, List[Dict]]:
        """
        处理JSON数据，替换匹配的店铺名称
        
        Args:
            json_data: 原始JSON数据
            
        Returns:
            元组 (处理后的JSON数据, 替换记录列表)
        """
        processed_data = json.loads(json.dumps(json_data))  # 深拷贝
        replacement_records = []
        
        def process_text_content(obj, path=""):
            """递归处理JSON中的文本内容"""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if isinstance(value, str):
                        # 检查是否是店铺名称（可能需要根据具体JSON结构调整）
                        match_result = self.find_best_match(value)
                        if match_result:
                            standard_name, similarity, algorithm = match_result
                            obj[key] = standard_name
                            replacement_records.append({
                                "path": current_path,
                                "original": value,
                                "replaced": standard_name,
                                "similarity": similarity,
                                "algorithm": algorithm
                            })
                            logger.info(f"替换: '{value}' -> '{standard_name}' (相似度: {similarity:.3f}, 算法: {algorithm})")
                    else:
                        process_text_content(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    current_path = f"{path}[{i}]" if path else f"[{i}]"
                    process_text_content(item, current_path)
        
        process_text_content(processed_data)
        
        return processed_data, replacement_records
    
    def process_json_file(self, input_json_file: str, output_json_file: str, report_file: Optional[str] = None) -> None:
        """
        处理JSON文件
        
        Args:
            input_json_file: 输入JSON文件路径
            output_json_file: 输出JSON文件路径
            report_file: 替换报告文件路径（可选）
        """
        try:
            # 读取原始JSON文件
            with open(input_json_file, 'r', encoding='utf-8') as file:
                original_data = json.load(file)
            
            logger.info(f"已读取原始JSON文件: {input_json_file}")
            
            # 处理数据
            processed_data, replacement_records = self.process_json_data(original_data)
            
            # 写入处理后的JSON文件
            with open(output_json_file, 'w', encoding='utf-8') as file:
                json.dump(processed_data, file, ensure_ascii=False, indent=2)
            
            logger.info(f"已写入处理后的JSON文件: {output_json_file}")
            logger.info(f"总共替换了 {len(replacement_records)} 个店铺名称")
            
            # 生成替换报告
            if report_file:
                with open(report_file, 'w', encoding='utf-8') as file:
                    json.dump({
                        "summary": {
                            "total_replacements": len(replacement_records),
                            "levenshtein_threshold": self.levenshtein_threshold,
                            "jaro_winkler_threshold": self.jaro_winkler_threshold
                        },
                        "replacements": replacement_records
                    }, file, ensure_ascii=False, indent=2)
                
                logger.info(f"已生成替换报告: {report_file}")
        
        except Exception as e:
            logger.error(f"处理JSON文件时发生错误: {e}")
            raise

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Azure AI Content Understanding 店铺名称匹配器')
    parser.add_argument('--input', '-i', required=True, help='输入JSON文件路径')
    parser.add_argument('--output', '-o', required=True, help='输出JSON文件路径')
    parser.add_argument('--csv', '-c', default='standard_shop_name.csv', help='标准店铺名称CSV文件路径')
    parser.add_argument('--report', '-r', help='替换报告文件路径')
    parser.add_argument('--lev-threshold', type=float, default=0.8, help='Levenshtein相似度阈值 (默认: 0.8)')
    parser.add_argument('--jw-threshold', type=float, default=0.85, help='Jaro-Winkler相似度阈值 (默认: 0.85)')
    
    args = parser.parse_args()
    
    # 创建匹配器实例
    matcher = ShopNameMatcher(
        csv_file=args.csv,
        levenshtein_threshold=args.lev_threshold,
        jaro_winkler_threshold=args.jw_threshold
    )
    
    # 处理JSON文件
    matcher.process_json_file(
        input_json_file=args.input,
        output_json_file=args.output,
        report_file=args.report
    )

if __name__ == "__main__":
    main()
