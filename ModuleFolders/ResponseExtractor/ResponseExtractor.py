import ast
import re
import string
from typing import Dict, List

# 回复解析器
class ResponseExtractor():
    def __init__(self):
        pass



    #处理并正则提取翻译内容
    def text_extraction(self, source_text_dict, response_content, target_language):

        try:
            # 提取译文结果
            translation_result= ResponseExtractor.extract_translation(self,source_text_dict,response_content)

            # 提取术语表结果
            glossary_result= ResponseExtractor.extract_glossary(self,response_content, target_language)

            # 提取禁翻表结果
            NTL_result = NTL_result = ResponseExtractor.extract_ntl(self,response_content)

            return translation_result, glossary_result, NTL_result
        except :
            print("\033[1;33mWarning:\033[0m 回复内容无法正常提取，请反馈\n")
            return {},{},{}

    #处理并正则提取翻译内容(sakura接口专用)
    def text_extraction_sakura(self, source_text_dict,response_content):

        try:
            # 提取译文结果
            textarea_contents = re.findall(r'<textarea.*?>(.*?)</textarea>', response_content, re.DOTALL)
            if not textarea_contents:
                return {}  # 如果没有找到 textarea 标签，返回空字典
            last_content = textarea_contents[-1]

            # 转换成字典
            translation_result = {}
            line_number = 0
            lines = last_content.strip().split("\n")
            for line in lines:
                if line:
                    translation_result[str(line_number)] = line
                    line_number += 1

            if not translation_result:
                return {},{},{} 

            # 计算原文行数
            newlines_in_dict = ResponseExtractor.count_newlines_in_dict_values(self,source_text_dict)

            # 合并调整翻译文本
            translation_result= ResponseExtractor.generate_text_by_newlines(self,newlines_in_dict,translation_result)


            return translation_result,{},{}
        except :
            print("\033[1;33mWarning:\033[0m 回复内容无法正常提取，请反馈\n")
            return {},{},{}

    # 提取翻译结果内容
    def extract_translation(self,source_text_dict,html_string):

        # 提取翻译文本
        text_dict = ResponseExtractor.label_text_extraction(self,html_string)

        if not text_dict:
            return {}  # 如果没有找到标签内容，返回空 JSON

        # 计算原文行数
        newlines_in_dict = ResponseExtractor.count_newlines_in_dict_values(self,source_text_dict)

        # 合并调整翻译文本
        translation_result= ResponseExtractor.generate_text_by_newlines(self,newlines_in_dict,text_dict)

        return translation_result

    # 辅助函数，正则提取标签文本内容
    def label_text_extraction(self, html_string):

        # 只提取最后一个 textarea 标签的内容
        textarea_contents = re.findall(r'<textarea.*?>(.*?)</textarea>', html_string, re.DOTALL)
        if not textarea_contents:
            return {}  # 如果没有找到 textarea 标签，返回空字典
        last_content = textarea_contents[-1]

        # 提取文本存储到字典中
        output_dict = ResponseExtractor.extract_text_to_dict(self,last_content)

        # 从第一个以数字序号开头的行开始，保留之后的所有行(主要是有些AI会在译文内容前面加点说明)
        filtered_dict = {}
        found = False
        # 按行号顺序遍历
        for key in sorted(output_dict.keys(), key=lambda k: int(k)):
            value = output_dict[key]
            if not found:
                if re.match(r'^\d+\.', value):  # 匹配以数字和句点开头的行
                    found = True
                else:
                    continue
            if found:
                filtered_dict[key] = value

        return filtered_dict

    # 提取文本为字典
    def extract_text_to_dict(self, input_string: str) -> Dict[str, str]:
        """
        从特定格式的字符串中提取内容并存入字典 。
        （目前因为AI偶尔会合并翻译，回复的列表块最后一个元素内容是这样的:"3.1."或者"3.1.[换行符]文本内容"，所以后期会检查出换行符不一致）
        Args:
            text: 输入的字符串。

        Returns:
            一个字典，键是'0', '1', '2'...，值是提取到的文本行。
        """
        # 1. 初步分割: 按主序号分割成块
        blocks = re.split(r'\n(?=\d+\.)', input_string.strip())

        extracted_items = []

        # 2. 处理每个块
        for block in blocks:
            block = block.strip()
            if not block:
                continue

            # 3. 尝试匹配列表块模式 (N.[ ... ])
            # re.DOTALL 使 '.' 可以匹配换行符
            list_block_match = re.match(r'^\d+\.\s*\[(.*)\]$', block, re.DOTALL)
            if list_block_match:

                list_content = list_block_match.group(1).strip()
                # 再次判断是否是列表块内容
                if list_content and list_content.startswith('"'):

                    # 4.1 列表块处理
                    items_in_block: List[str] = []
                    current_pos = 0
                    len_content = len(list_content)

                    while current_pos < len_content:
                        # --- 查找列表项的开始 ---
                        # 跳过前导空格和逗号
                        while current_pos < len_content and (list_content[current_pos].isspace() or list_content[current_pos] == ','):
                            current_pos += 1

                        if current_pos >= len_content:
                            break  # 到达内容末尾

                        # 列表项必须以引号开头
                        if list_content[current_pos] != '"':
                            print(f"警告：列表块 '{block[:30]}...' 内在位置 {current_pos} 检测到非预期字符（应为 双引号），内容片段: ...{list_content[current_pos:current_pos + 30]}...")
                            # 决定是跳到下一个可能的逗号还是终止此块的处理
                            next_comma = list_content.find(',', current_pos)
                            if next_comma != -1:
                                current_pos = next_comma + 1
                                continue
                            else:
                                break  # 无法恢复，结束此块

                        start_quote_pos = current_pos

                        # --- 查找对应的结束引号 ---
                        search_pos = start_quote_pos + 1
                        found_end_quote = False
                        while search_pos < len_content:
                            # 查找下一个引号
                            end_quote_pos = list_content.find('"', search_pos)

                            if end_quote_pos == -1:
                                print(f"警告：列表块 '{block[:30]}...' 内检测到未闭合的引号，起始于位置 {start_quote_pos}: ...{list_content[start_quote_pos:start_quote_pos + 50]}...")
                                current_pos = len_content  # 标记为处理完毕（虽然是异常结束）
                                break  # 跳出内部查找循环

                            # 检查这个引号是否是真正的结束引号
                            # 真正的结束引号后面应该是逗号、或者块的结尾（允许中间有空格）
                            next_char_idx = end_quote_pos + 1
                            while next_char_idx < len_content and list_content[next_char_idx].isspace():
                                next_char_idx += 1

                            # 如果是结尾或者后面是逗号，则认为是结束引号
                            if next_char_idx == len_content or list_content[next_char_idx] == ',':
                                # 提取引号之间的内容，并去除首尾可能存在的空白符
                                # 这会保留内部的 N.N. 格式
                                item_content = list_content[start_quote_pos + 1: end_quote_pos].strip()
                                items_in_block.append(item_content)

                                # 移动指针到逗号之后或内容末尾，准备找下一个项
                                current_pos = next_char_idx
                                # 如果后面是逗号，还要跳过逗号
                                if current_pos < len_content and list_content[current_pos] == ',':
                                    current_pos += 1

                                found_end_quote = True
                                break  # 找到了当前项，跳出内部查找循环
                            # 新增：检查是否是下一个编号项的开始（以引号开头且引号后紧跟数字.数字.格式）
                            # 目前发现ds有漏掉引号后逗号的毛病，增强一下健壮性
                            elif (next_char_idx < len_content and list_content[next_char_idx] == '"' and
                                  re.match(r'\"\d+\.\d+\.', list_content[next_char_idx:min(next_char_idx + 12, len_content)])):
                                # 提取当前项内容
                                item_content = list_content[start_quote_pos + 1: end_quote_pos].strip()
                                items_in_block.append(item_content)

                                # 移动指针到下一个引号位置，准备处理下一项
                                current_pos = next_char_idx
                                found_end_quote = True
                                break  # 找到了当前项，跳出内部查找循环
                            else:
                                # 这个引号是内容的一部分（内部引号），继续向后查找
                                search_pos = end_quote_pos + 1
                                # 继续内部 while 循环

                        # 如果内部循环是因为找不到闭合引号或其他错误而结束的
                        if not found_end_quote:
                            break  # 结束外部 while 循环对此块的处理

                    # 将从该列表块中成功提取的所有项添加到总列表中
                    extracted_items.extend(items_in_block)

                else:
                    # 如果方括号内的内容不像带引号列表 (例如 "9.[社团活动后]")
                    # 将整个原始块（包括 N.[...] ）视为一个单独的文本项。
                    extracted_items.append(block)

            else:
                # 4.2 文本块: 不是 N.[...] 格式，直接添加整个块内容
                extracted_items.append(block)

        # 5. 生成最终字典
        result_dict = {str(i): item for i, item in enumerate(extracted_items)}

        return result_dict


    # 辅助函数，统计原文中的换行符
    def count_newlines_in_dict_values(self,source_text_dict):
        """
        统计字典中每个文本值内的换行符数量，并生成一个包含换行符统计结果的新字典。

        Args:
            source_text_dict: 输入字典，键为字符串，值为文本字符串。

        Returns:
            一个字典，键与输入字典相同，值为对应文本字符串中的换行符数量。
            例如：
            {'0': 0, '1': 1, '2': 0}
        """
        newline_counts = {}  # 初始化一个空字典用于存储换行符数量

        for key, text in source_text_dict.items():
            newline_count = text.count('\n')  # 使用字符串的count()方法统计换行符数量
            if newline_count == 0:
                newline_counts[key] = newline_count  # 将统计结果存入新字典，键保持不变
            else:
                newline_counts[key] = newline_count
        return newline_counts

    # 辅助函数，根据换行符数量生成最终译文字典，与原文字典进行一一对应
    def generate_text_by_newlines(self, newline_counts_dict, translation_text_dict):
        """
        根据换行符统计字典和源文本字典生成新的字典，并处理多余内容。

        Args:
            newline_counts_dict: 换行符统计字典，键为字符串序号，值为换行符数量。
            translation_text_dict: 源文本字典，键为字符串序号，值为文本内容。

        Returns:
            一个新的字典，键与 newline_counts_dict 相同，值为根据换行符数量从 translation_text_dict
            中提取并拼接的文本内容。如果 translation_text_dict 内容不足，对应值为空字符串。
            如果 translation_text_dict 有剩余内容，将添加新键值对，键为最大原键加1，值为剩余内容按换行拼接。
        """
        result_dict = {}
        translation_keys_sorted = sorted(translation_text_dict.keys(), key=int)
        translation_index = 0

        # 处理每个预定键的行数需求
        for key, newline_count in newline_counts_dict.items():
            extracted_lines = []
            num_lines_to_extract = newline_count + 1 if newline_count > 0 else 1

            for _ in range(num_lines_to_extract):
                if translation_index < len(translation_keys_sorted):
                    current_key = translation_keys_sorted[translation_index]
                    extracted_lines.append(translation_text_dict[current_key])
                    translation_index += 1
                else:
                    break

            if extracted_lines:
                result_dict[key] = '\n'.join(extracted_lines) if newline_count > 0 else extracted_lines[0]
            else:
                result_dict[key] = ''

        # 添加剩余内容为新键值对
        if translation_index < len(translation_keys_sorted):
            if newline_counts_dict:
                max_key = max(map(int, newline_counts_dict.keys()))
            else:
                max_key = 0
            new_key = str(max_key + 1)
            remaining_texts = [translation_text_dict[k] for k in translation_keys_sorted[translation_index:]]
            result_dict[new_key] = '\n'.join(remaining_texts)

        return result_dict


    # 去除数字序号及括号
    def remove_numbered_prefix(self, source_text_dict, translation_text_dict):

        output_dict = {}
        for key, value in translation_text_dict.items():

            if not isinstance(value, str):
                output_dict[key] = value
                continue
            translation_lines = value.split('\n')
            cleaned_lines = []
            for i, line in enumerate(translation_lines):

                # 去除数字序号 (只匹配 "1.", "1.2." 等，并保留原文中的缩进空格)
                temp_line = re.sub(r'^\s*\d+\.(\d+\.)?', '', line)
                cleaned_lines.append(temp_line)

            processed_text = '\n'.join(cleaned_lines)

            # 移除尾部的 "/n]或者/n] (及其前面的空格)
            final_text = re.sub(r'\s*"?\n\]$', '', processed_text)
            output_dict[key] = final_text
        return output_dict

    # 提取回复中的术语表内容
    def extract_glossary(self, text, target_language):
        """
        从文本中提取<character>标签内的术语表

        参数：
            text (str): 原始文本内容

        返回：
            list[tuple]: 包含(原文, 译文, 备注)的列表，没有匹配内容时返回空列表
        """
        # 匹配完整的character标签内容（支持多行内容）
        glossary_match = re.search(
            r'<character[^>]*>(.*?)</character>',  # 兼容标签属性
            text,
            re.DOTALL | re.IGNORECASE
        )

        if not glossary_match:
            return []

        content = glossary_match.group(1).strip()
        if not content:
            return []

        # 解析具体条目
        entries = []

        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue  # 跳过空行

            # 使用分隔符拆分字段（最多拆分成3个部分）
            parts = [part.strip() for part in line.split('|', 2)]

            # 有效性检查：至少需要原文和译文两个字段
            if len(parts) < 2:
                continue

            original, translation = parts[0], parts[1]
            comment = parts[2] if len(parts) >= 3 else ""



            # 检查并过滤错误内容
            if ResponseExtractor._is_invalid_glossary_entry(self,original, translation, comment, target_language):
                continue
            else:
                entries.append((original, translation, comment))

        return entries

    # 术语表过滤规则
    def _is_invalid_glossary_entry(self, original, translation, info, target_language):
        """判断条目是否需要过滤"""
        # 非空检查
        if not original.strip() :
            return True

        # 过滤表头行
        if original.strip().lower() in ("原文", "原名", "名字", "source", "original", "name"):
            return True

        # 过滤提取错行
        if translation and "|" in translation:
            return True

        # 过滤提取错行
        if info and "|" in info:
            return True

        # 过滤无翻译行
        if original.strip() == translation.strip():
            return True

        # 过滤翻译成罗马音(待改进，可以精简一个输入参数)
        if (target_language != "english") and (ResponseExtractor.is_pure_english_text(self,translation)):
            return True

        # 过滤过长行
        if len(original) > 20 or len(translation) > 20:
            return True

        # 过滤有点无语的东西
        if ResponseExtractor.should_filter(self,original):
            return True

        # 过滤下划线+随机英文+下划线文本内容，像“_HERO_”这样的内容
        if re.fullmatch(r'_([a-zA-Z]+)_', original):
            return True

        # 过滤随机英文+数字，像“P1”这样的内容
        if re.fullmatch(r'[a-zA-Z]\d+', original):
            return True

        # 过滤换行符或制表符
        if original == '\n' or original == '\t' or original == '\r':
            return True

        # 过滤纯数字（匹配整数）
        if re.fullmatch(r'^\d+$', original) :
            return True


        return False
    
    # 检查是否是人称代词
    def should_filter(self,original):
        """
        检查输入的字符串是否在要过滤的列表中。
        (Check if the input string is in the list to be filtered.)
        """

        pronouns_and_others_to_filter = {
            # == 无语的东西 ==
            "俺", "俺たち", "なし", "姉ちゃん", "男性", "彼女", "乙女", "彼", "ト", "僕", "我", "私",
            "你", "他", "她", "主人", # 中文代词也保留

            # == 补充的日语人称代词 ==
            # --- 第一人称 (单数) ---
            "わたくし",  # Watakushi (更正式/谦虚的 "我")
            "あたし",    # Atashi (非正式，通常女性使用)
            "わし",      # Washi (一些老年男性或方言中的 "我")
            "うち",      # Uchi (关西地区常用，有时年轻女性也用)
            "自分",      # Jibun ("自己"，有时用作第一人称)
            "小生",      # Shousei (男性自谦语，多用于书面)
            "我輩",      # Wagahai (较古老、自大的 "吾辈")

            # --- 第一人称 (复数) ---
            "私たち",    # Watashitachi ("我们"，通用)
            "わたくしたち",# Watakushitachi (更正式/谦虚的 "我们")
            "あたしたち",# Atashitachi (非正式，通常女性使用)
            "僕ら",      # Bokura ("我们"，男性，非正式)
            "僕たち",    # Bokutachi ("我们"，男性)
            "俺ら",      # Orera ("我们"，男性，非常非正式)
            # "俺たち" 已经在您的列表中
            "我々",      # Wareware ("我们"，非常正式，演讲、文章中常用)

            # --- 第二人称 (单数) ---
            "あなた",    # Anata ("你"，通用，但有时根据语境可能显得生疏或亲密)
            "あんた",    # Anta (Anata 的不礼貌/非常随意的形式)
            "君",        # Kimi ("你"，通常上级对下级、男性之间、或歌词中使用)
            "お前",      # Omae ("你"，非常随意，可能亲密也可能粗鲁)
            "貴様",      # Kisama ("你"，非常粗鲁，用于骂人)
            "そちら",    # Sochira ("您那边"，较礼貌的指代方式)
            "貴方",      # Anata (あなた 的汉字写法，通用)
            "貴女",      # Anata (あなた 的汉字写法，专指女性)
            "汝",        # Nanji/Nare (古语/文学作品中的 "你")

            # --- 第二人称 (复数) ---
            "あなたたち", # Anatatachi ("你们")
            "あなた方",  # Anatagata ("各位"，比 あなたたち 更礼貌)
            "あんたたち", # Antatachi (非正式的 "你们")
            "君たち",    # Kimitachi ("你们"，对下级或同辈)
            "君ら",      # Kimira (比 Kimitachi 更随意的 "你们")
            "お前たち",  # Omaetachi (随意的 "你们")
            "お前ら",    # Omaera (非常随意的 "你们")
            "貴様ら",    # Kisamara (粗鲁的 "你们")

            # --- 第三人称 (单数) ---
            # "彼" (Kare - 他/男友) 和 "彼女" (Kanojo - 她/女友) 已经在您的列表中
            "あの人",    # Ano hito ("那个人"，较常用且礼貌)
            "あの方",    # Ano kata ("那位"，更礼貌)
            "あいつ",    # Aitsu ("那家伙"，随意，可能不礼貌)
            "こいつ",    # Koitsu ("这家伙"，随意，可能不礼貌)
            "そいつ",    # Soitsu ("那家伙"，指离听者近的人/物，随意)

            # --- 第三人称 (复数) ---
            "彼ら",      # Karera ("他们"，可指男性群体或男女混合群体)
            "彼女ら",    # Kanojora ("她们"，专指女性群体，不如 彼ら 常用)
            "あの人たち",# Ano hitotachi ("那些人")
            "あの方々",  # Ano katagata ("那些位"，更礼貌)
            "あいつら",  # Aitsura ("那些家伙"，随意，可能不礼貌)
            "こいつら",  # Koitsura ("这些家伙"，随意，可能不礼貌)
            "そいつら",  # Soitsura ("那些家伙"，指离听者近的，随意)
        }

        if original.lower() in pronouns_and_others_to_filter:
            return True
        return False

    # 检查是否纯英文
    def is_pure_english_text(self,text):
        """
        检查给定的文本是否为纯英文字母（允许空格和换行符）。

        Args:
            text: 要检查的文本字符串。

        Returns:
            如果文本是纯英文字母，则返回 True，否则返回 False。
        """
        for char in text:
            if char not in string.ascii_letters and char != ' ' and char != '\n':
                return False
        return True

    # 提取回复中的禁翻表内容
    def extract_ntl(self, text):
        """
        从文本中提取<code>标签内的术语表

        参数：
            text (str): 原始文本内容

        返回：
            list[tuple]: 包含(原文, 译文, 备注)的列表，没有匹配内容时返回空列表
        """
        # 匹配完整的code>标签内容（支持多行内容）
        code_match = re.search(
            r'<code[^>]*>(.*?)</code>',  # 兼容标签属性
            text,
            re.DOTALL | re.IGNORECASE
        )

        if not code_match:
            return []

        content = code_match.group(1).strip()
        if not content:
            return []

        # 解析具体条目
        entries = []

        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue  # 跳过空行

            # 使用分隔符拆分字段（最多拆分成2个部分）
            parts = [part.strip() for part in line.split('|', 1)]

            # 有效性检查：至少需要原文和译文两个字段
            if len(parts) < 1:
                continue

            original = parts[0]
            info = parts[1] if len(parts) >= 2 else ""


            # 检查并过滤错误内容
            if ResponseExtractor._is_invalid_NTL_entry(self,original, info):
                continue
            else:
                entries.append((original, info))

        return entries

    # 禁翻表过滤规则
    def _is_invalid_NTL_entry(self, original, info):
        """判断条目是否需要过滤"""
        # 非空检查
        if not original.strip() :
            return True

        # 过滤表头行
        if original.lower() in ("markers", "标记符", "备注","原文", "source"):
            return True

        # 过滤提取错行
        if info.lower() in ("|"):
            return True

        # 过滤常见符号
        if original.strip() in ("#","「","」","『","』","※","★","？","！","～","…","♥","♡","^^","『』","♪","･･･","ー","（ ）","!!","无","\\n"):
            return True

        # 过滤换行符或制表符
        if original.strip() == '\n' or original.strip() == '\t' or original.strip() == '\r':
            return True

        # 过滤纯数字（匹配整数）
        if re.fullmatch(r'^\d+$', original):
            return True

        # 过滤纯英文（匹配大小写字母组合）
        if re.fullmatch(r'^[a-zA-Z]+$', original):
            return True

        # 新增：过滤被方括号/中文括号包围的数字（如[32]、【57】）
        if re.fullmatch(r'^[\[【]\d+[\]】]$', original):
            return True

        # 新增：过滤纯英文字母和数字的组合（如abc123）
        if re.fullmatch(r'^[a-zA-Z0-9]+$', original):
            return True

        return False