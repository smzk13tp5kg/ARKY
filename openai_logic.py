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
        これまでどおり、メタプロンプト＋ gpt-4o-mini の2段階で
        「## パターン1〜3＋件名＋本文＋改善点＋注意点」のMarkdownを生成する。

    - 再生成（リライト）:
        is_refine=True かつ previous_suggestions が存在する場合。
        既存の3パターン＋追加要望 message をもとに、
        3パターンすべてを書き直したMarkdownを1回の呼び出しで生成する。
    """

    client = _get_client()
    if client is None:
        # import 時には例外を投げず、呼び出されたときだけ安全なメッセージを返す
        return "⚠️ OpenAI APIキーが設定されていません。（環境変数 OPENAI_API_KEY を確認してください）"

    # ----------------------------------------
    # 1) 再生成（リライト）モード
    # ----------------------------------------
    if is_refine and previous_suggestions:
        # 既存3パターン＋追加要望をもとにリライトさせるプロンプト
        refine_prompt = f"""
あなたはビジネスメールのプロ編集者です。

以下に、すでに生成済みの3パターンのメール案があります。
これらをベースに、追加要望を反映した新しい3パターンを作成してください。

【メールの種類】
- テンプレート種別: {template}
- トーン: {tone}
- 宛先: {recipient}
- 時候の挨拶: {seasonal_text or "なし"}

【既存の3パターン（そのまま引用）】
{previous_suggestions}

【追加要望】
{message}

【重要な指示】
- 既存の3パターンの構成・ニュアンスは可能な限り維持してください。
- 追加要望に必要な範囲だけを変更してください。
- 各パターンの「件名」「本文」を必ず更新してください。
- 各パターンについて「- 改善点」「- 注意点」も必ず記載してください。
- 出力形式は次のMarkdown構造に【厳密に】従ってください。

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

【禁止事項】
- 「もちろんです」「では早速作成します」などの前置き文は一切書かないこと。
- 上記の「## パターン1」「## パターン2」「## パターン3」以外の見出しや説明文は書かないこと。
- 3パターンより多く（4パターン目以降）を出力しないこと。
"""

        message_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "あなたはビジネス文書を最適化するプロ編集者です。",
                },
                {"role": "user", "content": refine_prompt},
            ],
        )
        generated_text = message_response.choices[0].message.content
        return generated_text  # Markdown形式のテキスト（3パターン分）

    # ----------------------------------------
    # 2) 初回生成モード（従来どおりのメタプロンプト方式）
    # ----------------------------------------
    receiver = recipient
    receiver_character = f"{recipient}向け / トーン: {tone}"
    situation = f"{template}メール"
    additional_info = seasonal_text or ""
    example_sentence = message

    # ============================================
    # メタプロンプト
    # ============================================
    meta_prompt = f"""
あなたは「ビジネスメッセージ生成AIのためのプロンプトを設計する専門家」です。

以下の入力情報をもとに、別の生成AIがビジネス文章を作るための
【最適プロンプト】を作成してください。

この最適プロンプトでは、生成AIに以下の二つの役割を必ず持たせてください。

---
# 役割①：状況分析者（Reasoning Agent）
与えられた状況（相手・性格・シチュエーション・補足情報・例文）を読み取り、
「どのような文章を書くべきか」について、
自分で“理由”を論理的に言語化する工程を必ず行う。

※ この思考結果は文章としてユーザーに見せず、生成AIの内部思考として扱う。

---

# 役割②：文章作成者（Writer Agent）
役割①で導いた理由（内部思考）に基づいて
● 文章を3パターン生成する  
● 各パターンについて「改善点」と「注意点」も出す  
というタスクを行う。

---

# 入力情報（状況分析の対象）
- 相手: {receiver}
- 相手のキャラ: {receiver_character}
- シチュエーション: {situation}
- 補足情報: {additional_info}
- ユーザー入力の例文: {example_sentence}

---

# プロンプトに必ず含める要件
- 文章を3パターン生成する指示
- 各パターンに「改善点」「注意点」を付ける指示
- 相手に適した敬語レベルで書く指示
- 過剰に丁寧すぎず、読みやすさを重視する指示
- Markdown形式で出力する指示
- 「理由を先に考えてから文章を作る」という流れを明示すること
- ただし、内部思考（理由）は最終出力に含めない と明記すること

---

# 出力フォーマットに関する厳守ルール

以下のフォーマットを **そのまま** 別の生成AIに渡すことを前提とするため、
出力形式は次のMarkdown構造 **のみ** とし、それ以外はいっさい書かないこと。

（出力例）

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

---

# フォーマット上の禁止事項

- 「もちろんです」「では早速作成します」などの前置き文は一切書かないこと。
- 上記の「## パターン1」「## パターン2」「## パターン3」以外の見出しは書かないこと。
- 3パターンより多く（4パターン目以降）を出力しないこと。
- 解説文や使い方説明など、パターン以外のテキストは書かないこと。

---

# あなたの最終出力内容

- あなたが作成するのは「最適なプロンプト本文のみ」ではなく、
  実際にこのフォーマットで文章を生成させるための"完成されたプロンプト"である。
- ただし出力形式は上記のMarkdown構造に従うこと。
"""

    # ③ メタプロンプト → 最適プロンプトを生成
    meta_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "あなたはプロンプト設計の専門家です。"},
            {"role": "user", "content": meta_prompt},
        ],
    )

    final_prompt = meta_response.choices[0].message.content

    # ④ 実際の文章生成（3パターン）
    message_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "あなたはビジネス文書を最適化するプロ編集者です。",
            },
            {"role": "user", "content": final_prompt},
        ],
    )

    generated_text = message_response.choices[0].message.content
    return generated_text  # Markdown 形式のテキスト（3パターン分）
