# db_logic.py
import os
from datetime import datetime
from typing import List, Dict
from supabase import create_client, Client

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # Cloud 環境では Secrets から入る想定なので無視してよい
    pass

# ============================================
# Supabase クライアント初期化
# ============================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client | None = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None


def _get_next_generation_id(table: str) -> int:
    """
    test-arky テーブルの現在の最大 generation_id を取得し、
    次に使う generation_id を返す。
    """
    if supabase is None:
        # Supabase 未設定の場合、とりあえず 1 を返す
        return 1

    res = (
        supabase.table(table)
        .select("generation_id")
        .order("generation_id", desc=True)
        .limit(1)
        .execute()
    )

    if res.data:
        max_generation_id = res.data[0].get("generation_id", 0) or 0
    else:
        max_generation_id = 0

    return max_generation_id + 1


# ============================================
# 3パターン分を「3レコード」として保存する関数
# ============================================
def save_email_batch(
    template: str,
    tone: str,
    recipient: str,
    message: str,
    seasonal_greeting: bool,
    patterns: List[Dict[str, str]],
    table_name: str = "test-arky",
) -> None:
    """
    patterns: [
        {"subject": "...", "body": "..."},
        {"subject": "...", "body": "..."},
        {"subject": "...", "body": "..."},
    ] を想定。
    1パターン = 1レコードとして、最大3レコード insert する。
    3件未満の時は空文字で埋める。
    """

    if supabase is None:
        raise Exception("Supabase接続情報が設定されていません。（SUPABASE_URL / SUPABASE_KEY）")

    if not patterns:
        raise Exception("保存するパターンが空です。")

    # 念のため 3件に揃える
    patterns = list(patterns)
    patterns = patterns[:3]
    while len(patterns) < 3:
        patterns.append({"subject": "", "body": ""})

    # 1回の生成を識別する generation_id を採番
    generation_id = _get_next_generation_id(table_name)

    # 各パターンを 1 レコードとして作成
    rows = []
    for idx, pat in enumerate(patterns, start=1):
        row = {
            "generation_id": generation_id,
            "pattern_no": idx,                      # 1,2,3
            "template": template,
            "tone": tone,
            "recipient": recipient,
            "seasonal_flag": seasonal_greeting,
            "user_message": message,
            "subject": pat.get("subject", ""),
            "body": pat.get("body", ""),
            "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }
        rows.append(row)

    # 挿入実行（まとめて insert）
    try:
        res = supabase.table(table_name).insert(rows).execute()
        print("[save_email_batch] 挿入成功件数:", len(res.data or []))
    except Exception as e:
        # App.py 側でメッセージを出す前提で、例外はそのまま投げる
        raise Exception(f"Supabase挿入エラー: {str(e)}")
