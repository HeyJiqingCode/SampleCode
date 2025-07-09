#!/usr/bin/env python3
"""
Azure AI Content Understanding 店铺名称匹配器
使用 Levenshtein 和 Jaro-Winkler 算法来匹配OCR识别的店铺名称与标准店铺名称
"""

import json
import csv
import textdistance
from typing import Dict, List, Tuple, Optional, Any
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
        
        # 检查是否是 SHEIN 的大小写变体，如果是则不进行处理
        if ocr_name.lower() == 'shein':
            return None  # SHEIN 的任何大小写变体都不进行替换
        
        # 尝试大小写不敏感的完全匹配
        ocr_name_lower = ocr_name.lower()
        for standard_name in self.standard_shop_names:
            if standard_name.lower() == ocr_name_lower:
                return (standard_name, 1.0, "Case-insensitive exact match")
        
        # 特殊处理1：精确匹配 SHEIN GLOWMODE -> glowmode
        if ocr_name_lower == 'shein glowmode':
            for standard_name in self.standard_shop_names:
                if standard_name.lower() == 'glowmode':
                    return (standard_name, 1.0, "Special case: SHEIN GLOWMODE -> glowmode")
        
        # 特殊处理2：精确匹配 Leisure -> SHEIN Leisure
        if ocr_name_lower == 'leisure':
            for standard_name in self.standard_shop_names:
                if standard_name.lower() == 'shein leisure':
                    return (standard_name, 1.0, "Special case: Leisure -> SHEIN Leisure")
        
        # 特殊处理3：如果OCR名称以SHEIN开头，尝试匹配不含SHEIN的部分
        if ocr_name_lower.startswith('shein '):
            # 去掉SHEIN前缀后的部分
            ocr_suffix = ocr_name[6:].strip()
            
            # 检查这个后缀是否能完全匹配标准名称（大小写不敏感）
            for standard_name in self.standard_shop_names:
                if standard_name.lower() == ocr_suffix.lower():
                    return (standard_name, 1.0, "SHEIN-prefix removed exact match")
        
        # 特殊处理4：如果OCR名称与某个标准名称的后缀完全匹配（大小写不敏感）
        # 例如: Leisure -> SHEIN Leisure
        for standard_name in self.standard_shop_names:
            standard_lower = standard_name.lower()
            if standard_lower.startswith('shein '):
                standard_suffix = standard_lower[6:].strip()
                if standard_suffix == ocr_name_lower:
                    return (standard_name, 1.0, "SHEIN-prefix added exact match")
        
        # 对所有标准名称计算相似度
        for standard_name in self.standard_shop_names:
            standard_lower = standard_name.lower()
            
            # 特殊处理：比较OCR名称与标准名称的SHEIN后缀
            current_lev_similarity = 0
            current_jw_similarity = 0
            
            # 情况1：两者都以SHEIN开头，比较后缀
            if ocr_name_lower.startswith('shein ') and standard_lower.startswith('shein '):
                ocr_suffix = ocr_name_lower[6:].strip()
                standard_suffix = standard_lower[6:].strip()
                
                # 计算后缀之间的相似度
                suffix_lev = self.levenshtein.normalized_similarity(ocr_suffix, standard_suffix)
                suffix_jw = self.jaro_winkler.normalized_similarity(ocr_suffix, standard_suffix)
                
                # 提高后缀相似度匹配的权重
                suffix_lev = min(1.0, suffix_lev * 1.1)  # 提高10%的权重，但不超过1.0
                suffix_jw = min(1.0, suffix_jw * 1.1)
                
                if suffix_lev > current_lev_similarity:
                    current_lev_similarity = suffix_lev
                
                if suffix_jw > current_jw_similarity:
                    current_jw_similarity = suffix_jw
            
            # 情况2：OCR以SHEIN开头，标准名称不以SHEIN开头
            elif ocr_name_lower.startswith('shein ') and not standard_lower.startswith('shein '):
                ocr_suffix = ocr_name_lower[6:].strip()
                
                # 比较OCR的后缀与完整的标准名称
                suffix_lev = self.levenshtein.normalized_similarity(ocr_suffix, standard_lower)
                suffix_jw = self.jaro_winkler.normalized_similarity(ocr_suffix, standard_lower)
                
                # 提高从OCR名称移除SHEIN前缀后匹配的权重
                suffix_lev = min(1.0, suffix_lev * 1.2)  # 提高20%的权重
                suffix_jw = min(1.0, suffix_jw * 1.2)
                
                if suffix_lev > current_lev_similarity:
                    current_lev_similarity = suffix_lev
                
                if suffix_jw > current_jw_similarity:
                    current_jw_similarity = suffix_jw
            
            # 情况3：OCR不以SHEIN开头，标准名称以SHEIN开头
            elif not ocr_name_lower.startswith('shein ') and standard_lower.startswith('shein '):
                standard_suffix = standard_lower[6:].strip()
                
                # 比较完整的OCR与标准名称的后缀
                suffix_lev = self.levenshtein.normalized_similarity(ocr_name_lower, standard_suffix)
                suffix_jw = self.jaro_winkler.normalized_similarity(ocr_name_lower, standard_suffix)
                
                # 提高向OCR名称添加SHEIN前缀后匹配的权重
                suffix_lev = min(1.0, suffix_lev * 1.15)  # 提高15%的权重
                suffix_jw = min(1.0, suffix_jw * 1.15)
                
                if suffix_lev > current_lev_similarity:
                    current_lev_similarity = suffix_lev
                
                if suffix_jw > current_jw_similarity:
                    current_jw_similarity = suffix_jw
            
            # 常规比较：全名比较（大小写敏感和不敏感）
            lev_similarity = self.levenshtein.normalized_similarity(ocr_name, standard_name)
            jw_similarity = self.jaro_winkler.normalized_similarity(ocr_name, standard_name)
            
            lev_similarity_ci = self.levenshtein.normalized_similarity(ocr_name.lower(), standard_name.lower())
            jw_similarity_ci = self.jaro_winkler.normalized_similarity(ocr_name.lower(), standard_name.lower())
            
            # 使用大小写不敏感相似度的更高值
            full_lev = max(lev_similarity, lev_similarity_ci)
            full_jw = max(jw_similarity, jw_similarity_ci)
            
            if full_lev > current_lev_similarity:
                current_lev_similarity = full_lev
            
            if full_jw > current_jw_similarity:
                current_jw_similarity = full_jw
            
            # 更新最佳匹配
            if current_lev_similarity >= self.levenshtein_threshold and current_lev_similarity > best_similarity:
                best_match = standard_name
                best_similarity = current_lev_similarity
                
                if ocr_name_lower.startswith('shein ') and standard_lower.startswith('shein '):
                    best_algorithm = "Levenshtein (SHEIN-suffix)"
                elif ocr_name_lower.startswith('shein ') and not standard_lower.startswith('shein '):
                    best_algorithm = "Levenshtein (SHEIN-removed)"
                elif not ocr_name_lower.startswith('shein ') and standard_lower.startswith('shein '):
                    best_algorithm = "Levenshtein (SHEIN-added)"
                else:
                    best_algorithm = "Levenshtein" if lev_similarity >= lev_similarity_ci else "Levenshtein (case-insensitive)"
            
            if current_jw_similarity >= self.jaro_winkler_threshold and current_jw_similarity > best_similarity:
                best_match = standard_name
                best_similarity = current_jw_similarity
                
                if ocr_name_lower.startswith('shein ') and standard_lower.startswith('shein '):
                    best_algorithm = "Jaro-Winkler (SHEIN-suffix)"
                elif ocr_name_lower.startswith('shein ') and not standard_lower.startswith('shein '):
                    best_algorithm = "Jaro-Winkler (SHEIN-removed)"
                elif not ocr_name_lower.startswith('shein ') and standard_lower.startswith('shein '):
                    best_algorithm = "Jaro-Winkler (SHEIN-added)"
                else:
                    best_algorithm = "Jaro-Winkler" if jw_similarity >= jw_similarity_ci else "Jaro-Winkler (case-insensitive)"
        
        if best_match:
            return (best_match, best_similarity, best_algorithm)
        
        return None
    
    def process_comma_separated_shop_names(self, shop_names_str: str) -> Tuple[str, List[Dict]]:
        """
        处理逗号分隔的店铺名称字符串
        
        Args:
            shop_names_str: 逗号分隔的店铺名称字符串
            
        Returns:
            元组 (处理后的字符串, 替换记录列表)
        """
        if not shop_names_str or not shop_names_str.strip():
            return shop_names_str, []
        
        # 按逗号分割店铺名称
        shop_names = [name.strip() for name in shop_names_str.split(',')]
        processed_names = []
        replacement_records = []
        
        for original_name in shop_names:
            if not original_name:
                continue
                
            match_result = self.find_best_match(original_name)
            if match_result:
                standard_name, similarity, algorithm = match_result
                processed_names.append(standard_name)
                replacement_records.append({
                    "original": original_name,
                    "replaced": standard_name,
                    "similarity": similarity,
                    "algorithm": algorithm
                })
                logger.info(f"替换: '{original_name}' -> '{standard_name}' (相似度: {similarity:.3f}, 算法: {algorithm})")
            else:
                processed_names.append(original_name)
        
        # 重新组合为逗号分隔的字符串
        processed_str = ', '.join(processed_names)
        return processed_str, replacement_records
    
    def process_json_data(self, json_data: Any) -> Tuple[Any, List[Dict]]:
        """
        处理JSON数据，替换匹配的店铺名称
        专门处理 result.contents.fields.shopname.valueString 和 
        result.contents.fields.shopname_in_search_bar.valueString 字段
        
        Args:
            json_data: 原始JSON数据
            
        Returns:
            元组 (处理后的JSON数据, 替换记录列表)
        """
        processed_data = json.loads(json.dumps(json_data))  # 深拷贝
        replacement_records = []
        
        # 处理数组中的每个项目
        if isinstance(processed_data, list):
            for item_index, item in enumerate(processed_data):
                if isinstance(item, dict) and 'result' in item:
                    result = item['result']
                    if isinstance(result, dict) and 'contents' in result:
                        contents = result['contents']
                        if isinstance(contents, list):
                            for content_index, content in enumerate(contents):
                                if isinstance(content, dict) and 'fields' in content:
                                    fields = content['fields']
                                    
                                    # 处理 shopname 字段
                                    if 'shopname' in fields and isinstance(fields['shopname'], dict):
                                        if 'valueString' in fields['shopname']:
                                            original_value = fields['shopname']['valueString']
                                            processed_value, records = self.process_comma_separated_shop_names(original_value)
                                            fields['shopname']['valueString'] = processed_value
                                            
                                            # 添加路径信息到记录
                                            for record in records:
                                                record['path'] = f"[{item_index}].result.contents[{content_index}].fields.shopname.valueString"
                                                record['field'] = 'shopname'
                                                replacement_records.append(record)
                                    
                                    # 处理 shopname_in_search_bar 字段
                                    if 'shopname_in_search_bar' in fields and isinstance(fields['shopname_in_search_bar'], dict):
                                        if 'valueString' in fields['shopname_in_search_bar']:
                                            original_value = fields['shopname_in_search_bar']['valueString']
                                            processed_value, records = self.process_comma_separated_shop_names(original_value)
                                            fields['shopname_in_search_bar']['valueString'] = processed_value
                                            
                                            # 添加路径信息到记录
                                            for record in records:
                                                record['path'] = f"[{item_index}].result.contents[{content_index}].fields.shopname_in_search_bar.valueString"
                                                record['field'] = 'shopname_in_search_bar'
                                                replacement_records.append(record)
        
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
                # 按字段分组统计
                field_stats = {}
                for record in replacement_records:
                    field = record.get('field', 'unknown')
                    if field not in field_stats:
                        field_stats[field] = 0
                    field_stats[field] += 1
                
                with open(report_file, 'w', encoding='utf-8') as file:
                    json.dump({
                        "summary": {
                            "total_replacements": len(replacement_records),
                            "field_statistics": field_stats,
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
