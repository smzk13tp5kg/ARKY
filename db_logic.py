# db_logic.py
"""
Supabase へメール生成結果を保存するためのヘルパーモジュール。
Streamlit の UI は一切書かない。
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import List, Dict, Any, Optional

from supabase import create_client, Client

# .env があればローカルで読み込む（Cloud では Secrets 前提）
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def _get_supabase() -> Optional[Client]:
    """
    Supabase クライアントを返す。
    URL / KEY が設定されていなければ None を返す。
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase: Optional[Client] = _get_supabase()


def _get_next_ids() -> Dict[str, int]:
    """
    test-arky テーブルから max(id), max(generatedid) を取得し、
    次に使う id と generatedid を返す。

    戻り値:
        {
            "next_id":      次の id,
            "next_genid":   次の generatedid
        }
    """
    if supabase is None:
        return {"next_id": 1, "next_genid": 1}

    # id の最大値
    resp_id = (
        supabase.table("test-arky")
        .select("id")
        .order("id", desc=True)
        .limit(1)
        .execute()
    )
    max_id = resp_id.data[0]["id"] if resp_id.data else 0

    # generatedid の最大値
    resp_gen = (
        supabase.table("test-arky")
        .select("generatedid")
        .order("generatedid", desc=True)
        .limit(1)
        .execute()
    )
    max_genid = resp_gen.data[0]["generatedid"] if resp_gen.data else 0

    return {"next_id": max_id + 1, "next_genid": max_genid + 1}


def save_email_batch(
    template: str,
    tone: str,
    recipient: str,
    message: str,
    patterns: List[Dict[str, str]],
) -> None:
    """
    3パターン（または1〜3パターン）の生成結果を Supabase にまとめて保存する。

    引数:
        template : 「依頼」「謝罪」などテンプレート種別
        tone     : 「標準ビジネス」「フォーマル」などトーン
        recipient: 「上司」「同僚」など相手種別
        message  : ユーザーが入力した元メッセージ
        patterns : 生成結果のリスト
                   [
                     {"subject": "...", "body": "..."},
                     {"subject": "...", "body": "..."},
                     {"subject": "...", "body": "..."},
                   ]
                   のような形式を想定（1〜3要素）

    挙動:
        - 1回の呼び出しにつき generatedid は共通の値を採番
        - patterns の要素ごとに 1 行ずつ INSERT
        - regeneratedid には "1","2","3" ... のようにパターン番号を文字列で保存
    """
    if supabase is None:
        # DB 未設定の場合は何もしない
        return

    if not patterns:
        return

    ids = _get_next_ids()
    next_id = ids["next_id"]
    genid = ids["next_genid"]

    rows: List[Dict[str, Any]] = []
    now = datetime.utcnow().isoformat()

    for idx, pat in enumerate(patterns):
        subject = pat.get("subject", "")
        body = pat.get("body", "")

        row = {
            "id": next_id + idx,          # 連番で付与
            "generatedid": genid,         # 3パターン共通
            "regeneratedid": str(idx + 1),  # "1", "2", "3" ...
            "template": template,
            "tone": tone,
            "recipient": recipient,
            "message": message,
            "subject": subject,
            "body": body,
            # 追加で使いたければ created_at カラムをテーブルに作っておく
            # "created_at": now,
        }
        rows.append(row)

    # まとめて insert
    supabase.table("test-arky").insert(rows).execute()
