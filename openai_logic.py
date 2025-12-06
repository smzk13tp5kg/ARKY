from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

print("APIキー:", os.getenv("OPENAI_API_KEY")) 

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------
# ① ユーザー入力（アプリから渡される値）
# -------------------------
receiver = "上司"
receiver_character = "丁寧で慎重"
situation = "欠勤連絡"
additional_info = "急な発熱のため。明日の会議に出席不可。業務引き継ぎは佐藤さんに依頼済み。"
example_sentence = "明日の会議欠席しないといけません。すみません。"

# -------------------------
# ② メタプロンプト（他のAIに送るプロンプトを生成）
# -------------------------

meta_prompt = f"""
あなたは「ビジネスメッセージ生成AIのためのプロンプトを設計する専門家」です。

以下の入力情報をもとに、別の生成AIがビジネス文章を作るための
【最適プロンプト】を作成してください。

この最適プロンプトでは、生成AIに以下の二つの役割を必ず持たせてください。

---
# 役割①：状況分析者（Reasoning Agent）
与えられた状況（相手・性格・シチュエーション・補足情報・例文）を読み取り、
「どのような文章を書くべきか」について、
**自分で“理由”を論理的に言語化する工程を必ず行う。**

例：
- なぜこの敬語レベルを使うべきなのか
- なぜこの順番（結論→背景など）が適切なのか
- なぜこの相手にはこういう言い回しが良いのか　など
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
- ただし、**内部思考（理由）は最終出力に含めない** と明記すること

---

# 出力形式
- あなたが作成するのは「最適なプロンプト本文のみ」
- 他の説明・前置き・考察は一切書かない
- 余分な語句なしで、別の生成AIに渡せるプロンプトだけを書いてください
"""


meta_response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "あなたはプロンプト設計の専門家です。"},
        {"role": "user", "content": meta_prompt}
    ]
)

final_prompt = meta_response.choices[0].message.content
print("【生成されたプロンプトA】")
print(final_prompt)
print("──────────────────────")

# -------------------------
# ③ 実際の文章生成（3パターン）
# -------------------------

message_response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "あなたはビジネス文書を最適化するプロ編集者です。"},
        {"role": "user", "content": final_prompt}
    ]
)

generated_text = message_response.choices[0].message.content

print("【生成されたビジネスメッセージ（3パターン）】")
print(generated_text)
