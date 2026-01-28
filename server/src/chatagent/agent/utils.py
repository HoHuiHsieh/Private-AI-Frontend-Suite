import re
from typing import Union, List


def estimate_tokens(text: Union[str, List[str]]) -> int:
    """
    Estimate the number of tokens in the input text.

    Handles both English and Traditional Chinese text.
    Uses different estimation strategies based on character types:
    - English/ASCII: ~1 token per 4 characters (based on GPT tokenization)
    - Chinese characters (CJK): ~1 token per 1-2 characters
    - Mixed content: Combines both strategies

    Args:
        text: Single string or list of strings to estimate tokens for

    Returns:
        Estimated token count
    """
    if isinstance(text, list):
        return sum(estimate_tokens(t) for t in text)

    if not text:
        return 0

    # Count different character types
    # CJK Unified Ideographs (most common Chinese characters)
    cjk_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]')
    cjk_chars = len(cjk_pattern.findall(text))

    # Count ASCII/Latin characters (excluding spaces)
    ascii_pattern = re.compile(r'[a-zA-Z0-9]')
    ascii_chars = len(ascii_pattern.findall(text))

    # Count spaces and punctuation separately
    total_chars = len(text)
    other_chars = total_chars - cjk_chars - ascii_chars

    # Token estimation:
    # - CJK characters: ~1.5 tokens per character (conservative estimate)
    # - ASCII words: ~1 token per 4 characters
    # - Other characters (punctuation, spaces): ~1 token per 6 characters
    cjk_tokens = int(cjk_chars * 1.5)
    ascii_tokens = max(1, ascii_chars // 4)
    other_tokens = max(0, other_chars // 6)

    total_tokens = cjk_tokens + ascii_tokens + other_tokens

    # Ensure at least 1 token for non-empty text
    return max(1, total_tokens)
