# db_logic.py
import os
from datetime import datetime, timezone
from typing import List, Dict
from supabase import create_client, Client

# .env（ローカル） or Streamlit Secrets（クラウド）から読み込み
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # dotenv が無くても無視（Streamlit Cloud では Secrets 前提）
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


def _assert_client():
    """Supabaseクライアントが無い場合は例外を投げる。"""
    if supabase is None:
        raise RuntimeError(
            "Supabaseクライアントが初期化されていません。\n"
            "環境変数 SUPABASE_URL / SUPABASE_KEY を確認してください。"
        )


def _get_next_generatedid(table: str) -> int:
    """
    指定テーブルの現在の最大 generatedid を取得し、
    次に使う generatedid を返す。

    ※ generatedid が NULL の行は無視する前提。
    """
    _assert_client()

    res = (
        supabase.table(table)
        .select("generatedid")
        .order("generatedid", desc=True)
        .limit(1)
        .execute()
    )

    if res.data:
        max_generatedid = res.data[0].get("generatedid") or 0
    else:
        max_generatedid = 0

    return int(max_generatedid) + 1


# ============================================
# 3パターン分を「3レコード」で保存する関数（B案）
# ============================================
def save_email_batch(
    template: str,
    tone: str,
    recipient: str,
    message: str,
    seasonal_greeting: bool,
    patterns: List[Dict[str, str]],
    table_name: str = "test_arky_patterns",
) -> None:
    """
    App 側から渡された 3パターン分の subject/body を
    Supabase の test_arky_patterns テーブルに「3レコード」として保存する。

    前提テーブル構成（例）:
      - id : bigint, PK (identity)
      - generatedid : bigint  … 同一入力で共通のグループID
      - pattern_no : int      … 1,2,3
      - template : text
      - tone : text
      - recipient : text
      - message : text        … ユーザーの元入力
      - seasonal_greeting : boolean
      - subject : text
      - body : text
      - created_at : timestamptz (default now())

    patterns: [
      {"subject": "...", "body": "..."},
      {"subject": "...", "body": "..."},
      {"subject": "...", "body": "..."},
    ]
    """
    _assert_client()

    if not patterns:
        raise ValueError("patterns が空です。保存するデータがありません。")

    # 念のため 3件に揃える
    patterns = list(patterns)
    patterns = patterns[:3]
    while len(patterns) < 3:
        patterns.append({"subject": "", "body": ""})

    # グループ共通の generatedid を採番
    generatedid = _get_next_generatedid(table_name)

    # created_at はアプリ側で明示的に入れても良いし、テーブル側 default now() でも OK
    now_iso = datetime.now(timezone.utc).isoformat()

    rows = []
    for idx, p in enumerate(patterns, start=1):
        rows.append(
            {
                "generatedid": generatedid,
                "pattern_no": idx,  # 1, 2, 3
                "template": template,
                "tone": tone,
                "recipient": recipient,
                "message": message,
                "seasonal_greeting": seasonal_greeting,
                "subject": p.get("subject", "") or "",
                "body": p.get("body", "") or "",
                "created_at": now_iso,  # テーブル側で default now() を使うなら省略可
            }
        )

    # 挿入実行
    try:
        res = supabase.table(table_name).insert(rows).execute()
        # デバッグ用ログ（Streamlit の Logs に出る）
        print("[save_email_batch] inserted rows:", res.data)
    except Exception as e:
        # App 側で st.error に出したいので、そのまま投げる
        raise RuntimeError(f"Supabase 挿入エラー: {e}")

