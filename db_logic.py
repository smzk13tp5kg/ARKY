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

# このモジュールで使うテーブル名（DDL に合わせる）
TABLE_NAME = "test_arky_patterns"


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
    table_name: str = TABLE_NAME,
) -> None:
    """
    App 側から渡された 3パターン分の subject/body を
    Supabase の test_arky_patterns テーブルに「3レコード」として保存する。

    対応テーブル構成（DDL）:
      create table public.test_arky_patterns (
        id                bigserial primary key,
        generatedid       bigint      not null,    -- 同一入力で共通のグループID
        pattern_index     integer     not null,    -- 1,2,3
        template          text        null,
        tone              text        null,
        recipient         text        null,
        seasonal_greeting boolean     null,
        user_message      text        null,        -- ユーザーの元入力
        subject           text        null,
        body              text        null,
        created_at        timestamptz not null default now(),
        constraint chk_pattern_index check (pattern_index >= 1 and pattern_index <= 3)
      );

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

    # created_at はテーブル側の default now() に任せるので明示指定しない
    rows = []
    for idx, p in enumerate(patterns, start=1):
        rows.append(
            {
                "generatedid": generatedid,
                "pattern_index": idx,          # DDL に合わせて pattern_index
                "template": template,
                "tone": tone,
                "recipient": recipient,
                "seasonal_greeting": seasonal_greeting,
                "user_message": message,       # DDL に合わせて user_message
                "subject": p.get("subject", "") or "",
                "body": p.get("body", "") or "",
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
