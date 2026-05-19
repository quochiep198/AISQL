import re

from app.schemas import Issue


def validate_sql_syntax(query: str, detected_type: str) -> list[Issue]:
    if detected_type not in {"select", "insert", "update", "delete", "merge", "ddl", "mysql", "postgres", "generic_sql", "auto"}:
        return []

    issues: list[Issue] = []
    compact = re.sub(r"\s+", " ", query).strip()
    lower = compact.lower()

    paren_error = _find_unbalanced_parentheses(query)
    if paren_error:
        issues.append(
            Issue(
                severity="critical",
                category="correctness",
                title="Câu truy vấn bị lệch ngoặc",
                description=paren_error,
                suggestion="Kiểm tra lại số lượng dấu ngoặc mở/đóng và vị trí kết thúc từng biểu thức.",
            )
        )

    quote_error = _find_unclosed_quote(query)
    if quote_error:
        issues.append(
            Issue(
                severity="critical",
                category="correctness",
                title="Câu truy vấn bị thiếu dấu nháy đóng",
                description=quote_error,
                suggestion="Đóng đầy đủ chuỗi literal và escape ký tự đặc biệt nếu cần.",
            )
        )

    if re.search(r"\bselect\s+from\b", lower):
        issues.append(
            Issue(
                severity="critical",
                category="correctness",
                title="SELECT thiếu danh sách cột",
                description="Phát hiện mẫu `SELECT FROM ...`, đây là cú pháp không hợp lệ.",
                suggestion="Bổ sung danh sách cột hoặc biểu thức sau SELECT trước FROM.",
            )
        )

    if re.search(r"\bselect\s*,", lower) or re.search(r",\s*from\b", lower):
        issues.append(
            Issue(
                severity="critical",
                category="correctness",
                title="SELECT có dấu phẩy thừa",
                description="Phát hiện dấu phẩy thừa trong danh sách cột, thường gây lỗi syntax gần FROM.",
                suggestion="Xóa dấu phẩy thừa cuối danh sách cột hoặc hoàn thiện cột còn thiếu.",
            )
        )

    if re.search(r"\b(where|and|or)\s*(;)?\s*$", lower):
        issues.append(
            Issue(
                severity="critical",
                category="correctness",
                title="Mệnh đề điều kiện chưa hoàn chỉnh",
                description="Query kết thúc ngay sau WHERE/AND/OR nên điều kiện lọc đang bị dang dở.",
                suggestion="Bổ sung đầy đủ biểu thức điều kiện ở phía sau WHERE/AND/OR.",
            )
        )

    if re.search(r"\bjoin\s+[a-z_][a-z0-9_\.]*\s*(?:as\s+)?[a-z_][a-z0-9_]*?\s*(where|group by|order by|limit|offset|$)", lower) and " on " not in f" {lower} ":
        issues.append(
            Issue(
                severity="critical",
                category="correctness",
                title="JOIN thiếu điều kiện ON",
                description="Phát hiện JOIN nhưng không thấy điều kiện ON đi kèm, query có thể lỗi syntax hoặc tạo Cartesian product ngoài ý muốn.",
                suggestion="Bổ sung ON rõ ràng cho từng JOIN hoặc đổi sang cú pháp JOIN phù hợp.",
            )
        )

    if re.search(r"\b(insert\s+into\s+[^\(]+\(\s*\)\s*values)\b", lower):
        issues.append(
            Issue(
                severity="critical",
                category="correctness",
                title="INSERT có danh sách cột rỗng",
                description="Phát hiện INSERT với cặp ngoặc cột rỗng trước VALUES, đây là cú pháp không hợp lệ.",
                suggestion="Khai báo danh sách cột hợp lệ hoặc bỏ hẳn phần danh sách cột nếu DB cho phép.",
            )
        )

    if re.search(r"\b(update|delete|insert into|merge into)\b", lower) and re.search(r"\bset\s*,", lower):
        issues.append(
            Issue(
                severity="critical",
                category="correctness",
                title="SET có dấu phẩy thừa",
                description="Phát hiện `SET ,` hoặc danh sách gán giá trị bị lỗi ngay sau SET.",
                suggestion="Kiểm tra lại danh sách cột trong SET và bỏ dấu phẩy thừa.",
            )
        )

    return _dedupe_issues(issues)


def _find_unbalanced_parentheses(query: str) -> str | None:
    depth = 0
    in_single = False
    in_double = False
    escape = False

    for index, char in enumerate(query, start=1):
        if escape:
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            continue
        if in_single or in_double:
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                return f"Phát hiện dấu `)` dư tại vị trí gần ký tự thứ {index}."

    if depth > 0:
        return "Câu truy vấn đang thiếu dấu `)` để đóng hết các biểu thức."
    return None


def _find_unclosed_quote(query: str) -> str | None:
    in_single = False
    in_double = False
    escape = False

    for char in query:
        if escape:
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double

    if in_single:
        return "Câu truy vấn đang thiếu dấu nháy đơn `'` để đóng chuỗi literal."
    if in_double:
        return 'Câu truy vấn đang thiếu dấu nháy kép `"` để đóng identifier hoặc chuỗi.'
    return None


def _dedupe_issues(issues: list[Issue]) -> list[Issue]:
    seen: set[tuple[str, str]] = set()
    deduped: list[Issue] = []
    for issue in issues:
        key = (issue.title, issue.description)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(issue)
    return deduped
