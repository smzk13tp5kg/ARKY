# openai_logic.py
import os
from openai import OpenAI

# ローカルでは .env から、Streamlit Cloud では Secrets から環境変数を読む想定
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # dotenv が無くても無視（Cloud環境ではSecretsから環境変数が入る想定）
    pass


def _get_client():
    """
    OpenAIクライアントを返すヘルパー。
    APIキーが設定されていない場合は None を返す。
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def generate_email_with_openai(
    template: str,
    tone: str,
    recipient: str,
    message: str,
    seasonal_text: str | None = None,
    previous_suggestions: str | None = None,
    is_refine: bool = False,
) -> str:
    """
    ビジネスメッセージ案を3パターン生成するラッパー関数。

    - 初回生成:
        is_refine=False または previous_suggestions が None の場合。
        ユーザーの要望をもとに、3パターンのメール案を新規に生成する。

    - 再生成（リライト）:
        is_refine=True かつ previous_suggestions が存在する場合。
        既存の3パターン＋追加要望 message をもとに、
        3パターンすべてを書き直したMarkdownを生成する。
    """

    client = _get_client()
    if client is None:
        return "⚠️ OpenAI APIキーが設定されていません。（環境変数 OPENAI_API_KEY を確認してください）"

    # 共通情報
    seasonal_info = seasonal_text or "なし"

    # --------------------------------------------------
    # プロンプト組み立て：初回生成 / リライトで分岐
    # --------------------------------------------------
    if is_refine and previous_suggestions:
        # 既存3パターンをベースに「追加要望」を反映してリライト
        main_prompt = f"""
あなたはビジネスメールのプロ編集者です。

以下に、すでに生成済みの3パターンのメール案があります。
これらをベースに、追加要望を反映した新しい3パターンを作成してください。

【メールの種類】
- テンプレート種別: {template}
- トーン: {tone}
- 宛先: {recipient}
- 時候の挨拶: {seasonal_info}

【既存の3パターン（そのまま引用）】
{previous_suggestions}

【追加要望】
{message}

【出力タスク】
- 既存の3パターンそれぞれについて、追加要望を反映した新しい文案に書き直してください。
- 元の文案の構成・ニュアンスは可能な限り維持しつつ、必要な変更だけを行ってください。
- 各パターンについて必ず以下を含めてください：
  - 件名
  - 本文
  - 改善点
  - 注意点

【出力フォーマット（絶対にこの構造を守る）】

## パターン1
件名: ...
本文:
...

- 改善点:
  - ...
- 注意点:
  - ...

## パターン2
件名: ...
本文:
...

- 改善点:
  - ...
- 注意点:
  - ...

## パターン3
件名: ...
本文:
...

- 改善点:
  - ...
- 注意点:
  - ...

【厳守事項】
- 「もちろんです」「では早速作成します」などの前置き文は一切書かないこと。
- 上記の「## パターン1」「## パターン2」「## パターン3」以外の見出しやテキストは書かないこと。
- 3パターンより多く（4パターン目以降）を出力しないこと。
"""
    else:
        # 初回：ユーザー要望から3パターンを新規生成
        main_prompt = f"""
あなたはビジネスメールのプロ編集者です。

以下の条件に基づき、ビジネスメールの文案を3パターン生成してください。

【メールの種類】
- テンプレート種別: {template}
- トーン: {tone}
- 宛先: {recipient}
- 時候の挨拶: {seasonal_info}

【ユーザーの要望（概要）】
{message}

【出力タスク】
- 上記の要望に対して適切なビジネスメール文案を3パターン作成してください。
- 各パターンについて必ず以下を含めてください：
  - 件名
  - 本文
  - 改善点（そのパターンをさらに良くするための視点）
  - 注意点（相手に誤解や不快感を与えないための注意点）

【出力フォーマット（絶対にこの構造を守る）】

## パターン1
件名: ...
本文:
...

- 改善点:
  - ...
- 注意点:
  - ...

## パターン2
件名: ...
本文:
...

- 改善点:
  - ...
- 注意点:
  - ...

## パターン3
件名: ...
本文:
...

- 改善点:
  - ...
- 注意点:
  - ...

【厳守事項】
- 「もちろんです」「では早速作成します」などの前置き文は一切書かないこと。
- 上記の「## パターン1」「## パターン2」「## パターン3」以外の見出しやテキストは書かないこと。
- 3パターンより多く（4パターン目以降）を出力しないこと。
"""

    # --------------------------------------------------
    # 実際の文章生成（1回の呼び出しで3パターン）
    # --------------------------------------------------
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "あなたはビジネス文書を最適化するプロ編集者です。",
            },
            {"role": "user", "content": main_prompt},
        ],
    )

    generated_text = response.choices[0].message.content
    return generated_text  # Markdown形式のテキスト（3パターン分）
