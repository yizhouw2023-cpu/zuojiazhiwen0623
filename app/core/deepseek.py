"""DeepSeek API client for article appreciation (文章赏析)."""
from __future__ import annotations
import httpx

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"
REQUEST_TIMEOUT = 90.0  # seconds

SYSTEM_PROMPT = """你是一位资深的中国文学评论家，拥有深厚的文学理论功底和敏锐的审美洞察力。请你根据提供的两位作家的文本分析数据，撰写一篇专业的比较文学赏析评论。

要求：
1. **写作风格对比**：从句式结构（平均句长）、用词偏好（高频词汇差异）角度分析两位作家的语言特点
2. **主题倾向分析**：从高频词推断每位作者关注的主题领域和精神世界
3. **修辞与语言特色**：评价词汇丰富度、句式节奏感、语言张力
4. **情感基调判断**：从用词推断文本的情感色彩和氛围
5. **综合对比总结**：两位作家的异同点，各自的独特魅力，可能的相互影响

格式要求：
- 有一个文学性的标题（如"双峰并峙：鲁迅与沈从文的文字世界"）
- 正文 600-900 字
- 分段清晰，语言优美但不浮夸
- 用中文撰写
- 最后附一句话总结（金句）"""


async def generate_appreciation(
    result_a_json: dict,
    result_b_json: dict,
    comparison_json: dict,
    text_a_sample: str = "",
    text_b_sample: str = "",
    api_key: str = "",
) -> str:
    """Generate a comparative literary commentary using DeepSeek API.

    Args:
        result_a_json: AnalysisResult as dict for author A
        result_b_json: AnalysisResult as dict for author B
        comparison_json: ComparisonResult as dict
        text_a_sample: First ~1000 chars of author A's text
        text_b_sample: First ~1000 chars of author B's text
        api_key: DeepSeek API key

    Returns:
        Generated appreciation text (markdown format)

    Raises:
        ValueError: If no API key is provided
        httpx.HTTPError: On API communication errors
    """
    if not api_key:
        raise ValueError("未配置 DeepSeek API Key，请在设置中填入或设置环境变量 DEEPSEEK_API_KEY")

    # Build user message with analysis data
    def fmt_top_words(top_words: list) -> str:
        return ", ".join(f"{w}({c}次)" for w, c in top_words)

    result_a = result_a_json
    result_b = result_b_json
    comp = comparison_json

    user_message = f"""请根据以下分析数据，撰写一篇比较文学赏析评论：

--- 作家 A：{result_a.get('author_name', '未知')} ---
• 总词数：{result_a.get('total_words', 0):,}
• 总句数：{result_a.get('total_sentences', 0):,}
• 平均句长：{result_a.get('avg_sentence_length', 0)} 词/句
• 独有内容词数：{result_a.get('unique_content_words', 0):,}
• 前10高频实词：{fmt_top_words(result_a.get('top_words', []))}

--- 作家 B：{result_b.get('author_name', '未知')} ---
• 总词数：{result_b.get('total_words', 0):,}
• 总句数：{result_b.get('total_sentences', 0):,}
• 平均句长：{result_b.get('avg_sentence_length', 0)} 词/句
• 独有内容词数：{result_b.get('unique_content_words', 0):,}
• 前10高频实词：{fmt_top_words(result_b.get('top_words', []))}

--- 对比数据 ---
• Jaccard 词汇相似度：{comp.get('jaccard_similarity', 0):.4f}
• 共享高频词：{'、'.join(comp.get('shared_top_words', [])) if comp.get('shared_top_words') else '（无）'}
• 作家 A 独有词数：{comp.get('unique_a_count', 0):,}
• 作家 B 独有词数：{comp.get('unique_b_count', 0):,}
• 共用词汇数：{comp.get('shared_vocabulary_count', 0):,}
• 词汇并集大小：{comp.get('total_vocabulary_union', 0):,}
• 平均句长比 (A/B)：{comp.get('sentence_length_ratio', 0):.2f}"""

    if text_a_sample:
        user_message += f"\n\n--- 作家 A 文本片段（前 1000 字）---\n{text_a_sample[:1000]}"
    if text_b_sample:
        user_message += f"\n\n--- 作家 B 文本片段（前 1000 字）---\n{text_b_sample[:1000]}"

    user_message += "\n\n请开始你的文学赏析评论："

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.8,
        "max_tokens": 2048,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.post(DEEPSEEK_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
