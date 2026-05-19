import re

from app.schemas import Issue
from app.services.query_tables import extract_table_names


def analyze_rules(
    query: str,
    detected_type: str,
    schema_info: str = "",
    index_info: str = "",
) -> tuple[list[Issue], list[str], list[str], str | None]:
    issues: list[Issue] = []
    improvements: list[str] = []
    notes: list[str] = [
        "Ket qua review phu thuoc schema, index va du lieu thuc te.",
        "Khong execute query; hay kiem chung bang EXPLAIN/EXPLAIN ANALYZE hoac cong cu tuong ung tren database that.",
    ]

    lower = query.lower()
    compact = re.sub(r"\s+", " ", lower).strip()
    schema_tokens = _extract_identifiers(schema_info)
    index_tokens = _extract_identifiers(index_info)
    query_tables = extract_table_names(query)

    if query_tables:
        notes.append(f"Bang lien quan trong query: {', '.join(query_tables[:8])}.")

    if schema_info.strip():
        notes.append("Da nhan schema bo sung tu nguoi dung de doi chieu rule-based review.")
    else:
        notes.append("Chua co schema chi tiet; mot so danh gia ve cot bang chi la suy luan tu query.")

    if index_info.strip():
        notes.append("Da nhan thong tin index/chỉ muc bo sung tu nguoi dung.")
    else:
        notes.append("Chua co thong tin index cu the; cac goi y index duoc giu o muc an toan.")

    if detected_type in {"mysql", "postgres", "generic_sql"}:
        _analyze_sql(query, compact, detected_type, schema_tokens, index_tokens, query_tables, issues, improvements, notes)
    elif detected_type == "mongodb":
        _analyze_mongodb(query, lower, index_tokens, issues, improvements, notes)
    else:
        issues.append(
            Issue(
                severity="medium",
                title="Khong nhan dien chac chan loai query",
                description="He thong chua xac dinh duoc query thuoc SQL hay MongoDB/NoSQL.",
                suggestion="Chon database_type thu cong hoac bo sung context cu phap query.",
            )
        )

    optimized_query = _suggest_optimized_query(query, compact)
    notes.extend(_build_prevention_notes(compact, query_tables))

    if not improvements:
        improvements.append("Bo sung schema, index, row count va muc tieu toi uu de review chinh xac hon.")

    improvements.extend(_build_prevention_actions(detected_type, compact))

    return issues, _dedupe(improvements), _dedupe(notes), optimized_query


def calculate_score(issues: list[Issue]) -> int:
    score = 100
    weights = {"low": 8, "medium": 15, "high": 25, "critical": 40}
    for issue in issues:
        score -= weights.get(issue.severity, 10)
    return max(0, min(100, score))


def build_summary(score: int, issues: list[Issue]) -> str:
    if not issues:
        return "Chua thay diem nghen ro rang trong rule-based review. Van nen kiem tra bang EXPLAIN de xac nhan query thuc te."
    high_count = sum(1 for item in issues if item.severity in {"high", "critical"})
    if high_count:
        return f"Query co {len(issues)} van de; {high_count} diem co kha nang gay cham query hoac sai ket qua. Uu tien sua cac muc severity cao truoc. Score hien tai: {score}."
    return f"Query co {len(issues)} diem can cai thien. Nen toi uu cach viet SQL, index va cach loc/sort de tranh lap lai van de nay. Score hien tai: {score}."


def _extract_identifiers(raw: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", raw or "")}


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _mentioned_columns(compact: str, schema_tokens: set[str]) -> list[str]:
    if not schema_tokens:
        return []
    found = [token for token in sorted(schema_tokens) if re.search(rf"\b{re.escape(token)}\b", compact)]
    return found[:5]


def _has_index_for_any(columns: list[str], index_tokens: set[str]) -> bool:
    return any(column in index_tokens for column in columns)


def _analyze_sql(
    query: str,
    compact: str,
    detected_type: str,
    schema_tokens: set[str],
    index_tokens: set[str],
    query_tables: list[str],
    issues: list[Issue],
    improvements: list[str],
    notes: list[str],
) -> None:
    mentioned_columns = _mentioned_columns(compact, schema_tokens)
    table_hint = f" Tren cac bang: {', '.join(query_tables[:4])}." if query_tables else ""

    if re.search(r"\bselect\s+from\b", compact):
        issues.append(
            Issue(
                severity="high",
                title="Cau truy van SQL khong hoan chinh",
                description=f"Query co SELECT nhung khong co danh sach cot hop le truoc FROM.{table_hint}",
                suggestion="Bo sung cot can truy van truoc FROM va kiem tra lai cu phap SQL.",
            )
        )
        improvements.append("Kiem tra lai cu phap SELECT ... FROM ... truoc khi toi uu.")

    if re.search(r"\bselect\s+\*", compact):
        issues.append(
            Issue(
                severity="medium",
                title="Su dung SELECT *",
                description=f"SELECT * co the doc nhieu cot khong can thiet va lam tang network/data transfer.{table_hint}",
                suggestion="Chi select cac cot can thiet.",
            )
        )
        improvements.append("Thay SELECT * bang danh sach cot cu the.")

    if re.search(r"\b(delete|update)\b", compact) and " where " not in f" {compact} ":
        issues.append(
            Issue(
                severity="critical",
                title="UPDATE/DELETE thieu WHERE",
                description=f"Query UPDATE/DELETE khong co WHERE co the anh huong toan bo bang.{table_hint}",
                suggestion="Them WHERE ro rang hoac co co che xac nhan an toan.",
            )
        )

    if re.search(r"\blike\s+['\"]%", compact):
        like_columns = _extract_predicate_columns(compact, "like")
        has_matching_index = _has_index_for_any(like_columns, index_tokens)
        issues.append(
            Issue(
                severity="high",
                title="LIKE voi wildcard dau chuoi",
                description=f"LIKE '%keyword' hoac '%keyword%' thuong khong tan dung duoc index B-tree thong thuong.{table_hint}",
                suggestion="Can nhac full-text index, search service, hoac thay doi pattern truy van.",
            )
        )
        if has_matching_index:
            notes.append("Da co index tren mot so cot LIKE, nhung wildcard dau chuoi van co the khien index khong duoc tan dung tot.")

    if "order by rand()" in compact or "order by random()" in compact:
        issues.append(
            Issue(
                severity="high",
                title="ORDER BY random tren tap du lieu lon",
                description=f"ORDER BY RAND()/RANDOM() co the phai sort toan bo tap ket qua.{table_hint}",
                suggestion="Dung chien luoc random theo id hoac precomputed sampling phu hop.",
            )
        )

    if " limit " in f" {compact} " and " order by " not in f" {compact} ":
        issues.append(
            Issue(
                severity="low",
                title="LIMIT khong co ORDER BY",
                description=f"Ket qua LIMIT khong co ORDER BY co the khong on dinh giua cac lan chay.{table_hint}",
                suggestion="Them ORDER BY theo tieu chi xac dinh.",
            )
        )

    if re.search(r"\boffset\s+[1-9]\d{3,}", compact):
        issues.append(
            Issue(
                severity="medium",
                title="OFFSET lon",
                description=f"OFFSET lon co the khien database phai scan hoac bo qua nhieu dong.{table_hint}",
                suggestion="Can nhac keyset pagination/cursor pagination.",
            )
        )

    if re.search(r"\bjoin\b", compact) and not re.search(r"\bjoin\b.+\bon\b", compact):
        issues.append(
            Issue(
                severity="high",
                title="JOIN thieu dieu kien ON ro rang",
                description=f"JOIN khong co ON ro rang co the tao Cartesian product hoac ket qua sai.{table_hint}",
                suggestion="Bo sung dieu kien JOIN chinh xac.",
            )
        )

    if compact.count(" or ") >= 3:
        issues.append(
            Issue(
                severity="medium",
                title="Nhieu dieu kien OR",
                description=f"Nhieu OR co the lam giam hieu qua su dung index.{table_hint}",
                suggestion="Kiem tra execution plan; can nhac UNION hoac index phu hop.",
            )
        )

    predicate_columns = _extract_predicate_columns(compact, "where") + _extract_order_by_columns(compact)
    known_columns = [column for column in predicate_columns if not schema_tokens or column in schema_tokens]
    if known_columns:
        if _has_index_for_any(known_columns, index_tokens):
            notes.append(f"Da tim thay thong tin index lien quan toi mot phan cot trong query: {', '.join(sorted(set(known_columns))[:5])}.")
        elif index_tokens:
            improvements.append(
                f"Kiem tra lai index cho cac cot dang filter/sort: {', '.join(sorted(set(known_columns))[:5])}."
            )
        else:
            improvements.append(
                f"Can nhac index cho cac cot dang filter/sort: {', '.join(sorted(set(known_columns))[:5])}."
            )

    if mentioned_columns and not predicate_columns:
        notes.append(f"Schema duoc cung cap co nhac toi cac cot lien quan trong query: {', '.join(mentioned_columns)}.")

    if detected_type == "postgres":
        improvements.append("Dung EXPLAIN ANALYZE de kiem tra execution plan thuc te.")
        if " ilike " in compact and re.search(r"\bilike\s+['\"]%", compact):
            issues.append(
                Issue(
                    severity="high",
                    title="ILIKE wildcard hai dau",
                    description="ILIKE '%keyword%' thuong kho tan dung index thong thuong.",
                    suggestion="Can nhac trigram index hoac full-text search.",
                )
            )
    elif detected_type == "mysql":
        improvements.append("Dung EXPLAIN de kiem tra execution plan.")
        improvements.append("Can nhac composite index theo thu tu WHERE + ORDER BY khi phu hop.")
    else:
        improvements.append("Dung EXPLAIN/EXPLAIN ANALYZE theo database tuong ung de kiem chung.")

    if len(query) > 3000 or compact.count("select") > 5:
        issues.append(
            Issue(
                severity="medium",
                title="Query dai hoac nested phuc tap",
                description=f"Query dai hoac nhieu nested SELECT co the kho bao tri va kho toi uu.{table_hint}",
                suggestion="Tach logic, dung CTE co kiem soat, hoac phan tich tung phan bang execution plan.",
            )
        )


def _build_prevention_notes(compact: str, query_tables: list[str]) -> list[str]:
    notes: list[str] = []
    if query_tables:
        notes.append(f"Uu tien review execution plan cho cac bang: {', '.join(query_tables[:4])}.")
    if " join " in f" {compact} ":
        notes.append("Khi query dung JOIN, can review thu tu join, dieu kien ON va index tren cot join.")
    if " order by " in f" {compact} ":
        notes.append("Neu query vua WHERE vua ORDER BY, coder nen doi chieu thu tu cot trong composite index.")
    return notes


def _build_prevention_actions(detected_type: str, compact: str) -> list[str]:
    actions = [
        "Truoc khi merge, chay EXPLAIN cho query moi hoac query da sua.",
        "Tranh SELECT * trong code production; chi lay cot can dung.",
    ]
    if " join " in f" {compact} ":
        actions.append("Dat convention review cho JOIN: phai co ON ro rang va index tren cot join chinh.")
    if " limit " in f" {compact} " and " order by " not in f" {compact} ":
        actions.append("Voi pagination, luon viet ORDER BY ro rang de ket qua on dinh giua cac lan chay.")
    if detected_type == "mysql":
        actions.append("Voi MySQL, uu tien kiem tra composite index theo thu tu loc truoc roi den sap xep.")
    if detected_type == "postgres":
        actions.append("Voi PostgreSQL, review them bitmap scan, sequential scan va sort cost trong EXPLAIN ANALYZE.")
    return actions


def _analyze_mongodb(
    query: str,
    lower: str,
    index_tokens: set[str],
    issues: list[Issue],
    improvements: list[str],
    notes: list[str],
) -> None:
    if "{}" in lower or ".find()" in lower:
        issues.append(
            Issue(
                severity="medium",
                title="Query MongoDB khong co filter",
                description="Query thieu filter co the scan nhieu document.",
                suggestion="Them filter phu hop va index cho field loc.",
            )
        )

    if "$regex" in lower and not re.search(r'"\$regex"\s*:\s*"\^', query):
        issues.append(
            Issue(
                severity="high",
                title="Regex khong anchored",
                description="Regex khong bat dau bang ^ thuong kho tan dung index.",
                suggestion="Dung anchored regex neu nghiep vu cho phep hoac thiet ke index/search rieng.",
            )
        )

    if "$lookup" in lower:
        issues.append(
            Issue(
                severity="medium",
                title="$lookup co the nang",
                description="$lookup tren collection lon co the ton tai nguyen neu thieu filter/index.",
                suggestion="Dam bao field join co index va dat $match som nhat co the.",
            )
        )

    if "aggregate" in lower and "$match" not in lower:
        issues.append(
            Issue(
                severity="medium",
                title="Aggregation thieu $match som",
                description="Pipeline khong co $match som co the xu ly nhieu document khong can thiet.",
                suggestion="Dua $match len som khi co dieu kien loc.",
            )
        )

    if "$project" not in lower:
        improvements.append("Bo sung projection de chi tra ve field can thiet.")

    if index_tokens:
        notes.append("Da co thong tin index MongoDB bo sung; hay doi chieu tiep bang explain('executionStats').")
    else:
        improvements.append("Tao index cho field thuong dung trong filter/sort.")


def _extract_predicate_columns(compact: str, operator: str) -> list[str]:
    if operator == "like":
        pattern = re.compile(r"\b([a-z_][a-z0-9_\.]*)\s+like\b")
    else:
        pattern = re.compile(r"\b([a-z_][a-z0-9_\.]*)\s*(=|>|<|>=|<=|in\s*\(|between\b)")
    return [_strip_qualifier(match.group(1)) for match in pattern.finditer(compact)]


def _extract_order_by_columns(compact: str) -> list[str]:
    match = re.search(r"\border by\s+(.+?)(?:\blimit\b|\boffset\b|$)", compact)
    if not match:
        return []

    columns: list[str] = []
    for part in match.group(1).split(","):
        token_match = re.search(r"([a-z_][a-z0-9_\.]*)", part.strip())
        if token_match:
            columns.append(_strip_qualifier(token_match.group(1)))
    return columns


def _strip_qualifier(identifier: str) -> str:
    return identifier.rsplit(".", 1)[-1]


def _suggest_optimized_query(query: str, compact: str) -> str | None:
    # Chi dua goi y an toan cho pattern don gian, khong tu bia schema.
    if re.search(r"\bselect\s+\*", compact):
        rewritten = re.sub(r"(?i)\bselect\s+\*", "SELECT <needed_columns>", query, count=1)
        if " limit " in f" {compact} " and " order by " not in f" {compact} ":
            return f"{rewritten}\nORDER BY <stable_column> DESC"
        return rewritten
    if " limit " in f" {compact} " and " order by " not in f" {compact} ":
        return f"{query.rstrip()}\nORDER BY <stable_column> DESC"
    if re.search(r"\boffset\s+[1-9]\d{3,}", compact):
        return f"-- Consider keyset pagination instead of large OFFSET\n{query}"
    return None
