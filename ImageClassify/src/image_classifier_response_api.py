import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv
from openai import AzureOpenAI

# 加载环境变量
load_dotenv()

# 初始化客户端
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)

# 加载系统提示词/指令
def load_instructions() -> str:
    instructions_path = Path(__file__).with_name("instructions.txt")
    return instructions_path.read_text(encoding="utf-8").strip()

# 从 GPT 响应中提取分类结果
def extract_result_from_response(response: Dict) -> str:
    try:
        for item in response.get('output', []):
            if item.get('type') == 'message' and item.get('role') == 'assistant':
                for content_item in item.get('content', []):
                    if content_item.get('type') == 'output_text':
                        text = content_item.get('text', '').strip()
                        try:
                            result_json = json.loads(text)
                            return result_json.get('result', '无')
                        except json.JSONDecodeError:
                            return text or '无'
        return '无'
    except Exception:
        return '无'

# 调用 Azure OpenAI 进行图像分类
def invoke_azure_openai(url: str) -> Dict:
    try:
        response = client.responses.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            prompt_cache_key="shein_test_0814",
            instructions=load_instructions(),
            reasoning={"effort": os.getenv("REASONING_EFFORT"), "summary": os.getenv("REASONING_SUMMARY")},
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_image", "image_url": url},
                ],
            }],
            
        )
        return response
    except Exception as e:
        if len(sys.argv) <= 1 or sys.argv[1] != "--batch":
            if "Failed to load image" in str(e):
                raise SystemExit("Failed to load image. Please check the URL")
        raise e

# 计算并显示分类准确率和详细结果
def calculate_and_display_accuracy(results: List[Dict]) -> None:
    valid_results = [r for r in results if r['result'] != "Failed"]
    
    def is_match(expected: str, detected: str) -> bool:
        if detected == "Failed":
            return False
        return expected in detected
    
    correct = sum(1 for r in valid_results if is_match(r['tags'], r['result']))
    failed_count = len(results) - len(valid_results)
    
    print(f"Successfully processed: {len(valid_results)} images")
    print(f"Failed to process: {failed_count} images")
    
    if valid_results:
        accuracy = correct / len(valid_results) * 100
        print(f"Accuracy: {correct}/{len(valid_results)} ({accuracy:.1f}%)")
        
        print("\nDetailed Results:")
        for result in results:
            tags, detected = result['tags'], result['result']
            status = "✓" if is_match(tags, detected) else "✗"
            print(f"  {status} Expected: {tags} | Detected: {detected}")
    else:
        print("No valid results to calculate accuracy.")

# 处理单张图片
def process_single_image(url: str) -> None:
    if not url:
        url = os.getenv("IMAGE_URL")
    
    if not url:
        print("Usage:")
        print("  Single image: python src/call_gpt_5_nano.py <image_url>")
        print("  Batch process: python src/call_gpt_5_nano.py --batch")
        print("  Or set IMAGE_URL environment variable")
        sys.exit(1)

    response = invoke_azure_openai(url)
    print(response.model_dump_json(indent=2))

# 批量处理 CSV 文件中的图片
def process_csv_batch() -> None:
    workspace_path = Path(__file__).parent.parent
    samples_path = workspace_path / "data" / "sample_images.csv"
    results_path = workspace_path / "output" / "results.csv"
    
    results_path.parent.mkdir(exist_ok=True)
    if not samples_path.exists():
        raise SystemExit(f"Input file not found: {samples_path}")
    
    results = []
    
    with open(samples_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tags, image_url = row.get('tags', ''), row.get('image_url', '')
            
            if not image_url:
                print(f"Skipping row with empty image_url: {row}")
                continue
                
            print(f"Processing: {image_url}")
            
            try:
                response = invoke_azure_openai(image_url)
                result = extract_result_from_response(response.model_dump())
                print(f"Result: {result}\n")
            except Exception as e:
                print(f"Error: {e}\n")
                result = "Failed"

            results.append({
                'tags': tags,
                'image_url': image_url,
                'result': result
            })
    
    with open(results_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['tags', 'image_url', 'result'])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\nProcessing Complete.")
    print(f"Results saved to: {results_path}")
    print(f"Total processed: {len(results)} images")
    
    calculate_and_display_accuracy(results)

# 主函数：根据参数选择处理模式
def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--batch":
        process_csv_batch()
    else:
        image_url = sys.argv[1] if len(sys.argv) > 1 else None
        process_single_image(image_url)

if __name__ == "__main__":
    main()