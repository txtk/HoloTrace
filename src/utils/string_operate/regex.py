import re


class Regex:
    remove_symbol_pattern = r"[^\u4e00-\u9fa5a-zA-Z0-9]+"
    sub_tech_pattern = r"(T\d{4})\.\d{3}"

    @staticmethod
    def get_pattern_remove_symbol_except(keep_symbols=[".", "_", "-"]):
        escaped_symbols = re.escape("".join(keep_symbols))
        regex_pattern = rf"[^\u4e00-\u9fa5a-zA-Z0-9{escaped_symbols}]+"
        return regex_pattern

    @staticmethod
    def get_search_result(content, regex):
        return re.search(regex, content)

    @staticmethod
    def get_search_judge(content, regex):
        result = Regex.get_search_result(content, regex)
        return result is not None

    @staticmethod
    def remove(pattern, input_string):
        return re.sub(pattern, "", input_string)

    @staticmethod
    def replace(pattern, replacement, input_string):
        return re.sub(pattern, replacement, input_string)

    @staticmethod
    def findall_num(pattern, input_string):
        return len(re.findall(pattern, input_string))

    @staticmethod
    def get_group_content(pattern, input_string, group_index=1):
        if input_string is None:
            return None
        if not isinstance(input_string, (str, bytes)):
            input_string = str(input_string)
        match = re.search(pattern, input_string)
        if match:
            return match.group(group_index)
        return None

    @staticmethod
    def remove_duplicate_spaces(input_string):
        return re.sub(r"\s+", " ", input_string).strip()
