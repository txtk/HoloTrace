"""
Author: mjxv mjxvtxtk1@gmail.com
Date: 2025-12-22 17:41:07
LastEditors: mjxv mjxvtxtk1@gmail.com
LastEditTime: 2025-12-25 10:27:39
FilePath: /align_to_attribute/src/utils/string_operate/string_match.py
Description: 两个字符串之间的匹配
Copyright (c) 2025 by ${git_name_email}, All Rights Reserved.
"""


from __future__ import annotations

from typing import Dict, List


class StringMatcher:
    """Collection of static helpers for string similarity."""

    @staticmethod
    def normalize(text: str) -> str:
        """Normalize text for comparison by stripping and lowering."""

        return " ".join(text.strip().lower().split()) if text else ""

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Split normalized text into tokens while collapsing multiple spaces."""

        return StringMatcher.normalize(text).split()

    @staticmethod
    def contains_each_other(a: str, b: str) -> bool:
        """Check whether either normalized string fully contains the other."""

        norm_a, norm_b = StringMatcher.normalize(a), StringMatcher.normalize(b)
        if not norm_a or not norm_b:
            return False
        return norm_a in norm_b or norm_b in norm_a

    @staticmethod
    def longest_common_substring_length(a: str, b: str) -> int:
        """Compute the length of the longest common substring via DP."""

        norm_a, norm_b = StringMatcher.normalize(a), StringMatcher.normalize(b)
        if not norm_a or not norm_b:
            return 0

        len_a, len_b = len(norm_a), len(norm_b)
        prev = [0] * (len_b + 1)
        best = 0
        for i in range(1, len_a + 1):
            curr = [0] * (len_b + 1)
            for j in range(1, len_b + 1):
                if norm_a[i - 1] == norm_b[j - 1]:
                    curr[j] = prev[j - 1] + 1
                    if curr[j] > best:
                        best = curr[j]
            prev = curr
        return best

    @staticmethod
    def levenshtein_distance(a: str, b: str) -> int:
        """Compute the standard Levenshtein edit distance."""

        norm_a, norm_b = StringMatcher.normalize(a), StringMatcher.normalize(b)
        len_a, len_b = len(norm_a), len(norm_b)

        if len_a == 0:
            return len_b
        if len_b == 0:
            return len_a

        previous = list(range(len_b + 1))
        for i in range(1, len_a + 1):
            current = [i] + [0] * len_b
            ca = norm_a[i - 1]
            for j in range(1, len_b + 1):
                cb = norm_b[j - 1]
                cost = 0 if ca == cb else 1
                current[j] = min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + cost,
                )
            previous = current
        return previous[-1]

    @staticmethod
    def token_overlap_ratio(a: str, b: str) -> float:
        """Compute simple token level Jaccard overlap."""

        tokens_a = set(StringMatcher._tokenize(a))
        tokens_b = set(StringMatcher._tokenize(b))
        if not tokens_a or not tokens_b:
            return 0.0
        intersection = len(tokens_a & tokens_b)
        union = len(tokens_a | tokens_b)
        return intersection / union if union else 0.0

    @staticmethod
    def compare_strings(
        text_a: str,
        text_b: str,
        *,
        max_edit_ratio: float = 0.2,
    ) -> Dict[str, float | int | bool | str]:
        """Compare two strings and capture heuristics."""

        normalized_a = StringMatcher.normalize(text_a)
        normalized_b = StringMatcher.normalize(text_b)
        containment = StringMatcher.contains_each_other(text_a, text_b)

        lcs_len = StringMatcher.longest_common_substring_length(text_a, text_b)
        shorter_len = max(1, min(len(normalized_a), len(normalized_b)))
        lcs_ratio = lcs_len / shorter_len

        edit_dist = StringMatcher.levenshtein_distance(text_a, text_b)
        longer_len = max(1, max(len(normalized_a), len(normalized_b)))
        edit_ratio = edit_dist / longer_len

        overlap = StringMatcher.token_overlap_ratio(text_a, text_b)

        same_entity = any(
            [
                containment,
                lcs_ratio >= 0.9,
                edit_ratio <= max_edit_ratio,
                overlap >= 0.6,
            ]
        )

        return {
            "normalized_a": normalized_a,
            "normalized_b": normalized_b,
            "containment": containment,
            "lcs_length": lcs_len,
            "lcs_ratio": lcs_ratio,
            "edit_distance": edit_dist,
            "edit_ratio": edit_ratio,
            "token_overlap": overlap,
            "same_entity": same_entity,
        }

    @staticmethod
    def describes_same_entity(text_a: str, text_b: str, *, max_edit_ratio: float = 0.2) -> bool:
        """Public helper returning only the boolean decision."""

        return StringMatcher.compare_strings(text_a, text_b, max_edit_ratio=max_edit_ratio)["same_entity"]


def compare_strings(
    text_a: str,
    text_b: str,
    *,
    max_edit_ratio: float = 0.2,
) -> Dict[str, float | int | bool | str]:
    """Module-level wrapper for convenient access."""

    return StringMatcher.compare_strings(text_a, text_b, max_edit_ratio=max_edit_ratio)


def describes_same_entity(text_a: str, text_b: str, *, max_edit_ratio: float = 0.2) -> bool:
    """Module-level wrapper returning only the boolean decision."""

    return StringMatcher.describes_same_entity(text_a, text_b, max_edit_ratio=max_edit_ratio)
