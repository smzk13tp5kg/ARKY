# db_logic.py
import os
from datetime import datetime
from typing import List, Dict, Any
from supabase import create_client, Client

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
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


def _get_next_generatedid(table: str) -> int:
    """
    test-arky テーブルの現在の最大 generatedid を取得し、
    次に使う generatedid を返す。
    """
    if supabase is None:
        return 1
    
    res = (
        supabase.table(table)
        .select("generatedid")
        .order("generatedid", desc=True)
        .limit(1)
        .execute()
    )
    
    if res.data:
        max_generatedid = res.data[0].get("generatedid", 0) or 0
    else:
        max_generatedid = 0
    
    return max_generatedid + 1


# ============================================
# 3パターン分をまとめて保存する関数
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
    App 側から渡された 3パターン分の subject/body を
    Supabase の test-arky テーブルに1レコードとして保存する。
    
    patterns: [
        {"subject": "...", "body": "..."},
        {"subject": "...", "body": "..."},
        {"subject": "...", "body": "..."},
    ]
    """
    if supabase is None:
        raise Exception("Supabase接続情報が設定されていません。環境変数を確認してください。")
    
    if not patterns:
        raise Exception("保存するパターンが空です。")
    
    # 念のため 3件に揃える
    patterns = list(patterns)
    patterns = patterns[:3]
    while len(patterns) < 3:
        patterns.append({"subject": "", "body": ""})
    
    # 次の generatedid を取得
    generatedid = _get_next_generatedid(table_name)
    
    # 1レコード分のデータを作成
    row = {
        "generatedid": generatedid,
        "template": template,
        "tone": tone,
        "recipient": recipient,
        "seasonal_greeting": seasonal_greeting,
        "user_message": message,
        "subject_1": patterns[0].get("subject", ""),
        "body_1": patterns[0].get("body", ""),
        "subject_2": patterns[1].get("subject", ""),
        "body_2": patterns[1].get("body", ""),
        "subject_3": patterns[2].get("subject", ""),
        "body_3": patterns[2].get("body", ""),
    }
    
    # 挿入実行
    try:
        res = supabase.table(table_name).insert(row).execute()
        print("[save_email_batch] 挿入成功:", res.data)
    except Exception as e:
        raise Exception(f"Supabase挿入エラー: {str(e)}")
