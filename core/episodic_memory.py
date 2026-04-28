"""
core/episodic_memory.py
v7.0 — Episodic Memory (Session Classification + Persistent Storage)

辅助模块: Memory 架构迁移

升级路径:
  v6.0: InMemoryStore (LangGraph) + sessions/{thread_id}.md (扁平文件)
  v7.0: InMemoryStore (保留) + SQLite FTS5 (新增，跨会话语义检索)

会话分类管理: 按 (cancer_type, complexity, evolution_round) 三维分类存储，
支持快速按类检索历史 Case 的 Session 摘要。
"""

import sqlite3
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

MEMORY_DB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "workspace", "memory", "episodic.db"
)


# ===========================================================
# 数据库初始化
# ===========================================================

def init_db() -> sqlite3.Connection:
    """初始化 SQLite 数据库（幂等操作）"""
    os.makedirs(os.path.dirname(MEMORY_DB), exist_ok=True)
    conn = sqlite3.connect(MEMORY_DB)
    conn.row_factory = sqlite3.Row  # 允许按列名访问

    # 主表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            rowid       INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id     TEXT NOT NULL,
            session_id  TEXT,
            cancer_type TEXT,
            mutation    TEXT,
            treatment_line INTEGER DEFAULT 0,
            complexity  TEXT DEFAULT 'unknown',
            evolution_round TEXT DEFAULT 'R0',
            report_summary  TEXT DEFAULT '',
            expert_feedback TEXT DEFAULT '',
            judge_scores    TEXT DEFAULT '{}',
            auto_metrics    TEXT DEFAULT '{}',
            errors_detected TEXT DEFAULT '[]',
            created_at  TEXT,
            UNIQUE(case_id)
        )
    """)

    # FTS5 虚拟表（支持全文检索）
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS cases_fts USING fts5(
            case_id,
            cancer_type,
            mutation,
            report_summary,
            expert_feedback,
            errors_detected,
            content='cases',
            content_rowid='rowid'
        )
    """)

    # Trigger: 自动维护 FTS 索引
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS cases_ai AFTER INSERT ON cases BEGIN
            INSERT INTO cases_fts(rowid, case_id, cancer_type, mutation,
                report_summary, expert_feedback, errors_detected)
            VALUES (new.rowid, new.case_id, new.cancer_type, new.mutation,
                new.report_summary, new.expert_feedback, new.errors_detected);
        END
    """)
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS cases_ad AFTER DELETE ON cases BEGIN
            INSERT INTO cases_fts(cases_fts, rowid, case_id, cancer_type, mutation,
                report_summary, expert_feedback, errors_detected)
            VALUES ('delete', old.rowid, old.case_id, old.cancer_type, old.mutation,
                old.report_summary, old.expert_feedback, old.errors_detected);
        END
    """)

    conn.commit()
    return conn


# ===========================================================
# 写入操作
# ===========================================================

def insert_case(conn: sqlite3.Connection, case_data: Dict[str, Any]):
    """插入或更新一个 Case 记录"""
    conn.execute("""
        INSERT OR REPLACE INTO cases
        (case_id, session_id, cancer_type, mutation, treatment_line,
         complexity, evolution_round, report_summary, expert_feedback,
         judge_scores, auto_metrics, errors_detected, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        case_data["case_id"],
        case_data.get("session_id", ""),
        case_data.get("cancer_type", "Unknown"),
        case_data.get("mutation", ""),
        case_data.get("treatment_line", 0),
        case_data.get("complexity", "unknown"),
        case_data.get("evolution_round", "R0"),
        case_data.get("report_summary", ""),
        case_data.get("expert_feedback", ""),
        json.dumps(case_data.get("judge_scores", {}), ensure_ascii=False),
        json.dumps(case_data.get("auto_metrics", {}), ensure_ascii=False),
        json.dumps(case_data.get("errors_detected", []), ensure_ascii=False),
        case_data.get("created_at", datetime.now().isoformat()),
    ))
    conn.commit()


# ===========================================================
# 检索操作
# ===========================================================

def search_by_cancer_type(
    conn: sqlite3.Connection,
    cancer_type: str,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """按癌种检索最近的 Case 记录"""
    cursor = conn.execute("""
        SELECT * FROM cases
        WHERE cancer_type = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (cancer_type, top_k))
    return [dict(row) for row in cursor.fetchall()]


def fulltext_search(
    conn: sqlite3.Connection,
    query: str,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    使用 FTS5 全文检索 Case 记录。
    适合在 Orchestrator 中按药物名/突变类型/错误类型等关键词检索历史 Case。
    """
    cursor = conn.execute("""
        SELECT c.* FROM cases c
        JOIN cases_fts f ON c.rowid = f.rowid
        WHERE cases_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """, (query, top_k))
    return [dict(row) for row in cursor.fetchall()]


def get_session_classification_summary(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    获取会话分类管理摘要：
    按 (cancer_type, complexity, evolution_round) 三维统计案例分布
    """
    cursor = conn.execute("""
        SELECT
            cancer_type,
            complexity,
            evolution_round,
            COUNT(*) as count
        FROM cases
        GROUP BY cancer_type, complexity, evolution_round
        ORDER BY count DESC
    """)
    rows = cursor.fetchall()

    summary: Dict[str, Any] = {
        "total_cases": 0,
        "by_cancer_type": {},
        "by_complexity": {"simple": 0, "moderate": 0, "complex": 0},
        "by_round": {},
        "detail": [],
    }

    for row in rows:
        row = dict(row)
        summary["total_cases"] += row["count"]
        summary["detail"].append(row)

        ct = row["cancer_type"] or "Unknown"
        summary["by_cancer_type"][ct] = summary["by_cancer_type"].get(ct, 0) + row["count"]

        cx = row["complexity"] or "unknown"
        if cx in summary["by_complexity"]:
            summary["by_complexity"][cx] += row["count"]

        rnd = row["evolution_round"] or "R0"
        summary["by_round"][rnd] = summary["by_round"].get(rnd, 0) + row["count"]

    return summary


# ===========================================================
# 便捷函数（无需管理 conn 的高层 API）
# ===========================================================

def save_case_to_db(case_data: Dict[str, Any]):
    """便捷：自动管理连接，插入 Case 记录"""
    conn = init_db()
    try:
        insert_case(conn, case_data)
    finally:
        conn.close()


def query_similar_cases_db(
    cancer_type: str = "",
    query_text: str = "",
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """便捷：自动管理连接，检索相似 Case"""
    conn = init_db()
    try:
        if query_text:
            return fulltext_search(conn, query_text, top_k)
        elif cancer_type:
            return search_by_cancer_type(conn, cancer_type, top_k)
        else:
            return []
    finally:
        conn.close()
