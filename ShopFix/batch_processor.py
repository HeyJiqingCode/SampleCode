#!/usr/bin/env python3
"""
批量处理工具：用于处理多个JSON文件的店铺名称匹配
"""

import os
import glob
import json
from typing import List
from shop_name_matcher import ShopNameMatcher
import argparse

def batch_process_files(input_dir: str, output_dir: str, csv_file: str, 
                       lev_threshold: float = 0.8, jw_threshold: float = 0.85):
    """
    批量处理目录中的所有JSON文件
    
    Args:
        input_dir: 输入目录路径
        output_dir: 输出目录路径
        csv_file: 标准店铺名称CSV文件路径
        lev_threshold: Levenshtein相似度阈值
        jw_threshold: Jaro-Winkler相似度阈值
    """
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建匹配器实例
    matcher = ShopNameMatcher(
        csv_file=csv_file,
        levenshtein_threshold=lev_threshold,
        jaro_winkler_threshold=jw_threshold
    )
    
    # 查找所有JSON文件
    json_files = glob.glob(os.path.join(input_dir, "*.json"))
    
    if not json_files:
        print(f"在目录 {input_dir} 中没有找到JSON文件")
        return
    
    print(f"找到 {len(json_files)} 个JSON文件")
    
    total_replacements = 0
    all_reports = []
    
    for json_file in json_files:
        filename = os.path.basename(json_file)
        name_without_ext = os.path.splitext(filename)[0]
        
        output_file = os.path.join(output_dir, f"{name_without_ext}_matched.json")
        report_file = os.path.join(output_dir, f"{name_without_ext}_report.json")
        
        print(f"\n处理文件: {filename}")
        
        try:
            # 处理单个文件
            matcher.process_json_file(
                input_json_file=json_file,
                output_json_file=output_file,
                report_file=report_file
            )
            
            # 读取报告并统计
            with open(report_file, 'r', encoding='utf-8') as f:
                report = json.load(f)
                file_replacements = report['summary']['total_replacements']
                total_replacements += file_replacements
                
                # 添加文件信息到报告
                report['file_info'] = {
                    'input_file': filename,
                    'output_file': os.path.basename(output_file)
                }
                
                all_reports.append(report)
                
                print(f"  替换数量: {file_replacements}")
        
        except Exception as e:
            print(f"  处理失败: {e}")
    
    # 生成汇总报告
    summary_report = {
        "batch_summary": {
            "total_files_processed": len(json_files),
            "total_replacements_across_all_files": total_replacements,
            "levenshtein_threshold": lev_threshold,
            "jaro_winkler_threshold": jw_threshold
        },
        "individual_reports": all_reports
    }
    
    summary_file = os.path.join(output_dir, "batch_summary_report.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_report, f, ensure_ascii=False, indent=2)
    
    print(f"\n批量处理完成！")
    print(f"总文件数: {len(json_files)}")
    print(f"总替换数: {total_replacements}")
    print(f"汇总报告: {summary_file}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='批量处理JSON文件中的店铺名称匹配')
    parser.add_argument('--input-dir', '-i', required=True, help='输入目录路径')
    parser.add_argument('--output-dir', '-o', required=True, help='输出目录路径')
    parser.add_argument('--csv', '-c', default='standard_shop_name.csv', help='标准店铺名称CSV文件路径')
    parser.add_argument('--lev-threshold', type=float, default=0.8, help='Levenshtein相似度阈值')
    parser.add_argument('--jw-threshold', type=float, default=0.85, help='Jaro-Winkler相似度阈值')
    
    args = parser.parse_args()
    
    batch_process_files(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        csv_file=args.csv,
        lev_threshold=args.lev_threshold,
        jw_threshold=args.jw_threshold
    )

if __name__ == "__main__":
    main()
