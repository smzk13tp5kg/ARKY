# db_logic.py
import os
from datetime import datetime
from typing import List, Dict, Any

from supabase import create_client, Client

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # dotenv が無くても無視（Cloud環境では Secrets から入る想定）
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


def _get_next_ids(table: str, n: int = 3) -> Dict[str, Any]:
    """
    test-arky テーブルの現在の最大 id / generatedid を取得し、
    次に使う id 群（n件分）と、新しい generatedid を返す。
    """
    if supabase is None:
        return {"ids": [], "generatedid": None}

    # 最新行を1件取得
    res = (
        supabase.table(table)
        .select("id, generatedid")
        .order("id", desc=True)
        .limit(1)
        .execute()
    )

    if res.data:
        max_id = res.data[0].get("id", 0) or 0
        max_generatedid = res.data[0].get("generatedid", 0) or 0
    else:
        max_id = 0
        max_generatedid = 0

    # 連番 id を n件分ふる
    ids = [max_id + i + 1 for i in range(n)]
    new_generatedid = max_generatedid + 1

    return {"ids": ids, "generatedid": new_generatedid}


# ============================================
# 3パターン分をまとめて保存する関数
# ============================================
def save_email_batch(
    template: str,
    tone: str,
    recipient: str,
    message: str,
    patterns: List[Dict[str, str]],
    table_name: str = "test-arky",
) -> None:
    """
    App 側から渡された 3パターン分の subject/body を
    Supabase の test-arky テーブルにまとめて保存する。

    patterns: [
        {"subject": "...", "body": "..."},
        {"subject": "...", "body": "..."},
        {"subject": "...", "body": "..."},
    ]
    """

    if supabase is None:
        # 接続情報が無い場合は何もしない（App 側は警告だけ出す想定）
        print("[save_email_batch] Supabase client is None. Skipping DB insert.")
        return

    if not patterns:
        print("[save_email_batch] patterns is empty. Nothing to insert.")
        return

    # 念のため 3件に揃える（過不足があっても動くように）
    patterns = list(patterns)
    patterns = patterns[:3]
    while len(patterns) < 3:
        patterns.append({"subject": "", "body": ""})

    # id / generatedid を採番
    id_info = _get_next_ids(table_name, n=len(patterns))
    ids = id_info.get("ids", [])
    generatedid = id_info.get("generatedid")

    if not ids or generatedid is None:
        print("[save_email_batch] Failed to get next ids/generatedid. Skipping insert.")
        return

    # 現在時刻（任意：作成日時を残したい場合）
    now_str = datetime.utcnow().isoformat()

    rows = []
    for idx, pat in enumerate(patterns):
        rows.append(
            {
                "id": ids[idx],
                "generatedid": generatedid,
                # ここでは 1,2,3 を regeneratedid として入れておく
                "regeneratedid": str(idx + 1),
                "template": template,
                "tone": tone,
                "recipient": recipient,
                "message": message,
                "subject": pat.get("subject", ""),
                "body": pat.get("body", ""),
                # テーブルに created_at 等のカラムがあればここで追加
                # "created_at": now_str,
            }
        )

    # 挿入実行
    res = supabase.table(table_name).insert(rows).execute()
    print("[save_email_batch] Inserted rows:", res.data)
