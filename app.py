import streamlit as st
from datetime import datetime
import html
import textwrap
import json
import re

# 外部ロジックをインポート
from openai_logic import generate_email_with_openai

# DB保存ロジック（あれば使う）
try:
    from db_logic import save_email_record
    HAS_DB = True
except ImportError:
    HAS_DB = False


# ============================================
# 時候の挨拶（ヘルパー）
# ============================================
def get_seasonal_greeting() -> str:
    month = datetime.now().month
    greetings = {
        1: "新春の候",
        2: "余寒の候",
        3: "早春の候",
        4: "春暖の候",
        5: "新緑の候",
        6: "初夏の候",
        7: "盛夏の候",
        8: "晩夏の候",
        9: "初秋の候",
        10: "秋涼の候",
        11: "晩秋の候",
        12: "師走の候",
    }
    return greetings.get(month, "")


# ============================================
# AI パターンブロックを分解するヘルパー
# ============================================
def parse_pattern_block(block: str) -> dict:
    """
    openai_logic から返ってきた 1 パターン分の Markdown テキストから、
    件名／本文／改善点／注意点 をざっくり抽出する。
    """
    # 先頭の "## パターンX" 行を削除
    block = re.sub(r"^##\s*パターン[^\n]*\n?", "", block, count=1, flags=re.MULTILINE)

    subject = ""
    body = ""
    improve = ""
    caution = ""

    # 件名
    m = re.search(r"件名[:：]\s*(.+)", block)
    if m:
        subject = m.group(1).strip()

    # "本文:" 以降を切り出し
    pos_body_label = block.find("本文:")
    if pos_body_label != -1:
        rest = block[pos_body_label + len("本文:") :]
    else:
        rest = block

    # 改善点・注意点の位置
    idx_improve = rest.find("- 改善点")
    idx_caution = rest.find("- 注意点")

    # 本文
    if idx_improve != -1:
        body = rest[:idx_improve].strip()
        rest2 = rest[idx_improve:]
    else:
        body = rest.strip()
        rest2 = ""

    # 改善点・注意点
    if rest2:
        if idx_caution != -1 and rest2.find("- 注意点") > -1:
            split_pos = rest2.find("- 注意点")
            improve_block = rest2[:split_pos].strip()
            caution_block = rest2[split_pos:].strip()
        else:
            improve_block = rest2.strip()
            caution_block = ""
    else:
        improve_block = ""
        caution_block = ""

    # ラベル部分を削る
    improve = re.sub(r"^-+\s*改善点[:：]?\s*", "", improve_block, flags=re.MULTILINE).strip()
    caution = re.sub(r"^-+\s*注意点[:：]?\s*", "", caution_block, flags=re.MULTILINE).strip()

    return {
        "subject": subject,
        "body": body,
        "improve": improve,
        "caution": caution,
    }


# ============================================
# メール生成関数（既存ロジック）
# ============================================
def generate_email(
    template,
    tone,
    recipient,
    message,
    variation=0,
    seasonal_text: str | None = None,
):
    subject_variations = {
        "依頼": [
            f"【ご依頼】{message[:20]}",
            f"【お願い】{message[:20]}",
            f"{message[:20]}についてのご依頼",
        ],
        "交渉": [
            f"【ご相談】{message[:20]}",
            f"【打ち合わせ依頼】{message[:20]}",
            f"{message[:20]}に関するご相談",
        ],
        "お礼": [
            f"お礼申し上げます - {message[:15]}",
            f"感謝の気持ちをお伝えいたします - {message[:15]}",
            f"御礼 - {message[:15]}",
        ],
        "謝罪": [
            f"お詫び申し上げます - {message[:15]}",
            f"深くお詫び申し上げます - {message[:15]}",
            f"謹んでお詫び申し上げます - {message[:15]}",
        ],
        "挨拶": [
            f"ご挨拶 - {message[:20]}",
            f"ご挨拶申し上げます - {message[:20]}",
            f"{message[:20]}",
        ],
    }
    template_subjects = subject_variations.get(
        template,
        [f"{template} - {message[:20]}"],
    )
    subject = template_subjects[variation % len(template_subjects)]

    greetings_variations = {
        "上司": [
            "お疲れ様です。",
            "お疲れ様でございます。",
            "いつもお世話になっております。",
        ],
        "同僚": [
            "お疲れ様です。",
            "お疲れさまです。",
            "こんにちは。",
        ],
        "部下": [
            "お疲れ様です。",
            "お疲れ様。",
            "こんにちは。",
        ],
        "社外企業社員": [
            "いつもお世話になっております。",
            "平素より大変お世話になっております。",
            "お世話になっております。",
        ],
        "取引先": [
            "いつもお世話になっております。",
            "平素より格別のご高配を賜り、厚く御礼申し上げます。",
            "お世話になっております。",
        ],
    }
    greeting_list = greetings_variations.get(recipient, ["お世話になっております。"])
    base_greeting = greeting_list[variation % len(greeting_list)]

    if seasonal_text:
        greeting = f"{seasonal_text}、{base_greeting}"
    else:
        greeting = base_greeting

    body_variations = [
        f"""{greeting}

{message}に関しまして、ご連絡させていただきます。

詳細につきましては、下記のとおりとなります。
ご確認いただけますと幸いです。

お忙しいところ恐縮ですが、
""",
        f"""{greeting}

{message}の件につきまして、ご連絡申し上げます。

詳細は以下のとおりでございます。
ご確認のほど、何卒よろしくお願い申し上げます。

ご多忙中誠に恐縮ではございますが、
""",
        f"""{greeting}

{message}についてご連絡いたします。

下記の内容をご確認ください。

お手数をおかけいたしますが、
""",
    ]
    body_start = body_variations[variation % len(body_variations)]

    closings_variations = {
        "上司": [
            "ご確認のほど、よろしくお願いいたします。",
            "ご査収のほど、よろしくお願い申し上げます。",
            "ご検討のほど、よろしくお願いいたします。",
        ],
        "同僚": [
            "よろしくお願いします。",
            "ご確認お願いします。",
            "よろしくね。",
        ],
        "部下": [
            "よろしくお願いします。",
            "確認しておいてください。",
            "よろしく。",
        ],
        "社外企業社員": [
            "ご検討のほど、よろしくお願い申し上げます。",
            "ご確認の上、ご返信いただけますと幸いです。",
            "何卒よろしくお願いいたします。",
        ],
        "取引先": [
            "ご検討のほど、よろしくお願い申し上げます。",
            "ご査収のほど、何卒よろしくお願い申し上げます。",
            "ご確認のほど、よろしくお願いいたします。",
        ],
    }
    closing_list = closings_variations.get(recipient, ["よろしくお願いいたします。"])
    closing = closing_list[variation % len(closing_list)]

    body = body_start + closing

    advices = {
        "依頼": "依頼メールでは、具体的な内容と期限を明記することで、相手が対応しやすくなります。簡潔で丁寧な表現を心掛けましょう。",
        "交渉": "交渉メールでは、双方にメリットがある提案を心掛けましょう。相手の立場を考慮した表現が重要です。",
        "お礼": "お礼メールは迅速に送ることで、誠意が伝わります。具体的に何に対する感謝なのかを明記しましょう。",
        "謝罪": "謝罪メールでは、具体的な理由と今後の対策を含めることで、誠実さが伝わります。責任を明確にすることが大切です。",
        "挨拶": "挨拶メールは、簡潔で丁寧な表現を心掛けましょう。相手との関係性に応じた適切なトーンを選びましょう。",
    }
    advice = advices.get(template, "メールは簡潔で丁寧な表現を心掛けましょう。")

    return {
        "subject": subject,
        "body": body,
        "advice": advice,
        "variation": variation,
    }


# ============================================
# ページ設定
# ============================================
st.set_page_config(
    page_title="ビジネスメール作成アシスタント",
    page_icon="✉️",
    layout="wide",
)


# ============================================
# カスタムCSS
# ============================================
st.markdown(
    """
<style>
* { box-sizing: border-box; }

/* 全体背景：濃い紺色 + ARKY背景画像 */
.stApp {
    background-color: #050b23;
    position: relative;
}
.stApp::before {
    content: '';
    position: fixed;
    top: 0;
    left: 450px;
    right: 0;
    height: 100%;

    background-image: url('https://raw.githubusercontent.com/smzk13tp5kg/ARKY/main/ARKYappbackgroundimage.png');
    background-size: contain;
    background-position: center top;
    background-repeat: no-repeat;

    opacity: 0.4;
    z-index: 0;
    pointer-events: none;
}

[data-testid="stAppViewContainer"] {
    background-color: transparent;
    position: relative;
    z-index: 1;
}
[data-testid="stHeader"] {
    background-color: rgba(5, 11, 35, 0.95);
    backdrop-filter: blur(10px);
}
body { background-color: #050b23; }

/* ツールバー消す */
div[data-testid="stToolbar"] {
    height: 0 !important;
    min-height: 0 !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    overflow: hidden !important;
}
div[data-testid="stToolbar"] > div {
    display: none !important;
}

/* メインエリア調整 */
main.block-container {
    padding-top: 0rem;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    max-width: 100% !important;
}

/* カラムレイアウト */
[data-testid="column"] {
    padding: 0 !important;
    width: 100% !important;
    min-width: 0 !important;
}
div[data-testid="stHorizontalBlock"] {
    gap: 0.5rem !important;
    width: 100% !important;
}
[data-testid="stVerticalBlock"] > div {
    max-width: 100% !important;
}

/* -------------------------------------------
   サイドバー
------------------------------------------- */
[data-testid="stSidebar"] {
    width: 450px !important;
    min-width: 450px !important;
    max-width: 450px !important;
    background: #050b23;
    border-right: 1px solid #cfae63;
}
[data-testid="stSidebar"] * {
    color: #ffffff !important;
}

/* サイドバー開閉ボタンのアイコン色 */
button[title="Open sidebar"] svg,
button[title="Close sidebar"] svg {
    fill: #ffffff !important;
    color: #ffffff !important;
}

/* サイドバー上部ヘッダー縮小 */
[data-testid="stSidebarHeader"] {
    min-height: 0 !important;
    height: 0 !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}
[data-testid="stSidebarContent"] {
    padding-top: 7px !important;
}

/* -------------------------------------------
   すべてのボタン：3D フリップスタイル
------------------------------------------- */
.stButton,
.stFormSubmitButton {
  perspective: 1000px;
  display: inline-block;
  width: 100%;
}

.stButton > button,
.stFormSubmitButton > button {
  position: relative;
  width: 100%;
  height: 50px;
  font-size: 1.0rem;
  font-weight: 700;
  text-transform: uppercase;
  cursor: pointer;
  border: none;
  background: transparent;
  transform-style: preserve-3d;
  transform: translateZ(-25px);
  transition: transform 0.25s;
  color: transparent !important;
}

.stButton > button::before,
.stButton > button::after,
.stFormSubmitButton > button::before,
.stFormSubmitButton > button::after {
  position: absolute;
  width: 100%;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 5px solid #000;
  box-sizing: border-box;
  border-radius: 8px;
  left: 0;
  top: 0;
}

/* 前面（オレンジ背景×白文字） */
.stButton > button::before,
.stFormSubmitButton > button::before {
  content: attr(data-text);
  background-color: #ff8c00;
  color: #ffffff;
  border-color: #ff8c00;
  transform: rotateY(0deg) translateZ(25px);
}

/* 背面（黄色背景×白文字） */
.stButton > button::after,
.stFormSubmitButton > button::after {
  content: attr(data-text);
  background-color: #ffd700;
  color: #ffffff;
  border-color: #ffd700;
  transform: rotateX(90deg) translateZ(25px);
}

/* ホバー時：X軸90度回転でフリップ */
.stButton > button:hover,
.stFormSubmitButton > button:hover {
  transform: translateZ(-25px) rotateX(-90deg);
}

/* ボタン内部のdiv（テキスト） */
.stButton > button > div,
.stFormSubmitButton > button > div {
  position: relative;
  z-index: 10;
  color: #ffffff !important;
  font-weight: 700;
  text-transform: uppercase;
}

/* -------------------------------------------
   メインエリア：ヘッダー・見出し
------------------------------------------- */
.top-bar {
    background: #050b23;
    padding: 0px 8px 8px 8px;
    border-bottom: 1px solid #cfae63;
    margin-bottom: 20px;
}
.app-title {
    font-size: 24px;
    font-weight: 700;
    color: #ffffff !important;
}
.section-header {
    font-size: 16px;
    font-weight: 700;
    color: #ffd666;
    margin: 8px 0;
}

/* メインブロック（stMainBlockContainer）の上パディングを強制的に6pxに変更 */
div.stMainBlockContainer {
    padding-top: 6px !important;
}

/* Streamlit が付ける block-container（同一要素の場合）も一応抑えておく */
main.block-container {
    padding-top: 6px !important;
}

/* プレビュー内の小見出し行 */
.preview-section-label {
    font-size: 12px;
    font-weight: 600;
    color: #6b7280;
    margin-bottom: 4px;
}

/* 改善点・注意点の本文エリア背景 #fffff9 */
.preview-note-body {
    background: #fffff9;
    border-radius: 8px;
    border: 1px solid #f3e7c4;
    color: #111827;
    font-size: 13px;
    padding: 10px 12px;
    line-height: 1.5;
    word-break: break-word;
    white-space: pre-wrap;
}

/* プレビュー見出し＋コピーアイコン */
.preview-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

/* コピーアイコン（パターン用） */
.pattern-copy-icon {
    cursor: pointer;
    font-size: 18px;
    margin-left: 8px;
    transition: transform 0.15s ease-out, text-shadow 0.15s ease-out;
}

/* クリック時のキラッとエフェクト */
.pattern-copy-icon.copy-flash {
    animation: copy-flash 0.5s ease-out;
}

@keyframes copy-flash {
    0% {
        transform: scale(1);
        text-shadow: none;
        color: #ffffff;
    }
    30% {
        transform: scale(1.4);
        text-shadow: 0 0 12px #ffd666;
        color: #ffd666;
    }
    100% {
        transform: scale(1);
        text-shadow: none;
        color: #ffffff;
    }
}

/* タイトル直下のメッセージエリア */
.intro-wrapper {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 0px;
}
.intro-icon {
    width: 120px;
    height: 120px;
    flex-shrink: 0;
}
.intro-icon img {
    width: 100%;
    height: 100%;
    object-fit: contain;
}

/* グラデ枠＋グラデ文字の AI バブル */
.intro-bubble {
    position: relative;
    padding: 0;
    border-radius: 16px;
    background: transparent;
    overflow: visible;
}
.intro-bubble::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 16px;
    padding: 4px;
    background: linear-gradient(120deg, #6559ae, #ff7159, #6559ae);
    background-size: 400% 400%;
    animation: intro-gradient 3s ease-in-out infinite;
    -webkit-mask:
      linear-gradient(#000 0 0) content-box,
      linear-gradient(#000 0 0);
    -webkit-mask-composite: xor;
            mask-composite: exclude;
}
.intro-bubble-text {
    position: relative;
    display: block;
    padding: 10px 18px;
    border-radius: 12px;
    background: rgba(5, 11, 35, 0.85);
    background-image: linear-gradient(120deg, #fdfbff, #ffd7b2, #ffe6ff);
    background-size: 400% 400%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 14px;
    font-weight: 600;
    line-height: 1.6;
    animation: intro-gradient 3s ease-in-out infinite;
}
@keyframes intro-gradient {
    0%   { background-position: 14% 0%; }
    50%  { background-position: 87% 100%; }
    100% { background-position: 14% 0%; }
}

/* 右：プレビューカード */
.preview-main-wrapper {
    background: #ffffff;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    padding: 16px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    min-height: 350px;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}
.preview-subject {
    color: #111827;
    font-size: 14px;
    margin-bottom: 8px;
    font-weight: bold;
}
.preview-body {
    background: #f3f4f6;
    border-radius: 8px;
    border: 1px solid #d1d5db;
    color: #111827;
    font-size: 14px;
    padding: 12px;
    flex-grow: 1;
    min-height: 120px;
    overflow-y: auto;
    word-break: break-word;
    white-space: pre-wrap;
}
.advice-box {
    background: #fffbe6;
    border: 1px solid #ffd666;
    border-radius: 8px;
    padding: 10px;
    color: #4b5563;
    font-size: 13px;
    margin-top: 12px;
}
.copy-info {
    color: #ffffff;
    font-size: 13px;
    margin-bottom: 4px;
}

/* チャットバブル */
.chat-log {
    display: flex;
    flex-direction: column;
    gap: 6px;
    max-height: 420px;
    overflow-y: auto;
    padding-right: 8px;
}
.chat-bubble {
    border-radius: 12px;
    padding: 8px 12px;
    max-width: 100%;
    font-size: 14px;
    line-height: 1.5;
    word-break: break-word;
    box-shadow: 0 2px 4px rgba(0,0,0,0.15);
}
.chat-bubble.user {
    position: relative;
    background: #ffffff;
    color: #111827;
    margin-left: auto;
    max-width: 80%;
}
.chat-bubble.user::after {
    content: "";
    position: absolute;
    right: -8px;
    top: 14px;
    width: 0;
    height: 0;
    border-style: solid;
    border-width: 8px 0 8px 8px;
    border-color: transparent transparent transparent #ffffff;
    filter: drop-shadow(-1px 1px 2px rgba(0,0,0,0.15));
}
/* アシスタント（ガイド）の吹き出し：枠も文字も動的に光らせる */
.chat-bubble.assistant {
    position: relative;
    padding: 0;
    border-radius: 18px;
    background: transparent;
    overflow: visible;
    margin-right: auto;
    max-width: 85%;
}
.chat-bubble.assistant::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 18px;
    padding: 3px;
    background: linear-gradient(120deg, #6559ae, #ff9f4a, #ffd666, #ff7159, #6559ae);
    background-size: 300% 300%;
    animation: assistant-glow-border 4s ease-in-out infinite;
    -webkit-mask:
      linear-gradient(#000 0 0) content-box,
      linear-gradient(#000 0 0);
    -webkit-mask-composite: xor;
            mask-composite: exclude;
}
.chat-bubble.assistant > span {
    position: relative;
    display: block;
    padding: 10px 18px;
    border-radius: 14px;
    background: rgba(5, 11, 35, 0.9);
    background-image: linear-gradient(120deg, #fdfbff, #ffd7b2, #ffe6ff);
    background-size: 300% 300%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 14px;
    font-weight: 600;
    line-height: 1.6;
    animation: assistant-glow-text 4s ease-in-out infinite;
}

/* 枠のグローアニメーション */
@keyframes assistant-glow-border {
    0% {
        background-position: 0% 50%;
        box-shadow: 0 0 0px rgba(255, 214, 102, 0.0);
    }
    50% {
        background-position: 100% 50%;
        box-shadow: 0 0 16px rgba(255, 214, 102, 0.35);
    }
    100% {
        background-position: 0% 50%;
        box-shadow: 0 0 0px rgba(255, 214, 102, 0.0);
    }
}

/* テキストのグラデ移動＆ほんのり発光 */
@keyframes assistant-glow-text {
    0% {
        background-position: 0% 50%;
        text-shadow: 0 0 0px rgba(255, 214, 102, 0.0);
    }
    50% {
        background-position: 100% 50%;
        text-shadow: 0 0 8px rgba(255, 214, 102, 0.4);
    }
    100% {
        background-position: 0% 50%;
        text-shadow: 0 0 0px rgba(255, 214, 102, 0.0);
    }
}

/* サイドバーのラジオボタンの余白を詰める */
[data-testid="stSidebar"] .stRadio > div {
    margin-top: 2px !important;
    margin-bottom: 2px !important;
    padding: 0 !important;
}
[data-testid="stSidebar"] .nav-label {
    margin-bottom: 4px !important;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================
# JS：全ボタンに data-text を付与（3D用）
# ============================================
st.components.v1.html(
    """
    <script>
    (function() {
      function updateButtonText() {
        const buttons = parent.document.querySelectorAll('.stButton > button, .stFormSubmitButton > button');
        buttons.forEach(btn => {
          const textDiv = btn.querySelector('div');
          if (textDiv && textDiv.textContent) {
            btn.setAttribute('data-text', textDiv.textContent.trim());
          }
        });
      }
      setTimeout(updateButtonText, 500);
      const observer = new MutationObserver(updateButtonText);
      observer.observe(parent.document.body, { childList: true, subtree: true });
    })();
    </script>
    """,
    height=0,
)


# ============================================
# セッション状態初期化
# ============================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_user_message" not in st.session_state:
    st.session_state.last_user_message = ""
if "generated_email" not in st.session_state:
    st.session_state.generated_email = None
if "variation_count" not in st.session_state:
    st.session_state.variation_count = 0
if "ai_suggestions" not in st.session_state:
    st.session_state.ai_suggestions = None


# ============================================
# トップバー
# ============================================
st.markdown(
    "<div class='top-bar'><h1 class='app-title'>✉️ ビジネスメール作成アシスタント</h1></div>",
    unsafe_allow_html=True,
)


# ============================================
# サイドバー
# ============================================
with st.sidebar:
    st.markdown(
        "<div class='sidebar-app-title'>■ メール生成AI</div>",
        unsafe_allow_html=True,
    )

    # テンプレート
    st.markdown("<div class='nav-section'>", unsafe_allow_html=True)
    st.markdown("<div class='nav-label'>テンプレート</div>", unsafe_allow_html=True)
    template_display = st.radio(
        "テンプレート",
        [
            "📧 依頼メール",
            "✉️ 交渉メール",
            "🙏 お礼メール",
            "💼 謝罪メール",
            "📩 挨拶メール",
            "➕ その他",
        ],
        index=0,
        label_visibility="collapsed",
        key="template_radio",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    display_to_template = {
        "📧 依頼メール": "依頼",
        "✉️ 交渉メール": "交渉",
        "🙏 お礼メール": "お礼",
        "💼 謝罪メール": "謝罪",
        "📩 挨拶メール": "挨拶",
        "➕ その他": "その他",
    }
    template = display_to_template[template_display]

    custom_template = None
    if template == "その他":
        custom_template = st.text_input("カスタムテンプレート", placeholder="例: 報告")
        template = custom_template if custom_template else "その他"

    # トーン
    st.markdown("<div class='nav-section'>", unsafe_allow_html=True)
    st.markdown("<div class='nav-label'>トーン</div>", unsafe_allow_html=True)
    tone_display = st.radio(
        "トーン",
        [
            "😊 カジュアル／フレンドリー（同僚向け）",
            "📄 標準ビジネス（最も一般的）",
            "📘 フォーマル（社外顧客／上位者／依頼交渉）",
            "🙏 厳粛・儀礼的（謝罪・クレーム対応）",
            "⏱️ 緊急・簡潔（即時対応が必要な通知）",
            "🌿 柔らめ（関係維持・お礼・広報向け）",
        ],
        index=1,
        label_visibility="collapsed",
        key="tone_radio",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    display_to_tone = {
        "😊 カジュアル／フレンドリー（同僚向け）": "カジュアル／フレンドリー",
        "📄 標準ビジネス（最も一般的）": "標準ビジネス",
        "📘 フォーマル（社外顧客／上位者／依頼交渉）": "フォーマル",
        "🙏 厳粛・儀礼的（謝罪・クレーム対応）": "厳粛・儀礼的",
        "⏱️ 緊急・簡潔（即時対応が必要な通知）": "緊急・簡潔",
        "🌿 柔らめ（関係維持・お礼・広報向け）": "柔らめ",
    }
    tone = display_to_tone[tone_display]

    # 相手
    st.markdown("<div class='nav-section'>", unsafe_allow_html=True)
    st.markdown("<div class='nav-label'>相手</div>", unsafe_allow_html=True)
    recipient_display = st.radio(
        "相手",
        [
            "👤 上司",
            "😊 同僚",
            "👔 部下",
            "🏢 社外企業社員",
            "🏪 取引先",
            "➕ その他",
        ],
        index=0,
        label_visibility="collapsed",
        key="recipient_radio",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    display_to_recipient = {
        "👤 上司": "上司",
        "😊 同僚": "同僚",
        "👔 部下": "部下",
        "🏢 社外企業社員": "社外企業社員",
        "🏪 取引先": "取引先",
        "➕ その他": "その他",
    }
    recipient = display_to_recipient[recipient_display]

    custom_recipient = None
    if recipient == "その他":
        custom_recipient = st.text_input("カスタム相手", placeholder="例: 顧客")
        recipient = custom_recipient if custom_recipient else "その他"

    # 時候の挨拶
    st.markdown("<div class='nav-section'>", unsafe_allow_html=True)
    st.markdown("<div class='nav-label'>時候の挨拶</div>", unsafe_allow_html=True)
    seasonal_option = st.radio(
        "時候の挨拶",
        ["不要", "追加する"],
        index=0,
        label_visibility="collapsed",
        key="seasonal_radio",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    add_seasonal = seasonal_option == "追加する"
    seasonal_text = get_seasonal_greeting() if add_seasonal else ""

    st.caption("© 2025 ARKY")


# ============================================
# メイン 2 カラム
# ============================================
col1, col2 = st.columns([3, 2], gap="medium")


# --------------------------------------------
# 左：メッセージ＋フォーム
# --------------------------------------------
with col1:
    st.markdown("<div class='section-header'>💬 メッセージ</div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="intro-wrapper">
          <div class="intro-icon">
            <img src="https://raw.githubusercontent.com/smzk13tp5kg/ARKY/main/AIhontai.png">
          </div>
          <div class="intro-bubble">
            <span class="intro-bubble-text">
              ようこそ！<br>ビジネスメールの作成をお手伝いします。<br>
              左側のナビゲーションエリアでテンプレートやトーン、相手を選び、
              下部の入力欄からメッセージ内容を入力してください。
            </span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # フォーム
    with st.form("message_form", clear_on_submit=True):
        user_message = st.text_area(
            "メッセージを入力",
            placeholder="例：取引先に感謝を伝えるメールを作成したい",
            height=120,
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("✓ 送信")

        if submitted and user_message:
            if template == "その他" and not custom_template:
                st.error("⚠️ カスタムテンプレートを入力してください")
            elif recipient == "その他" and not custom_recipient:
                st.error("⚠️ カスタム相手を入力してください")
            else:
                st.session_state.last_user_message = user_message

                st.session_state.variation_count = 0
                base_email = generate_email(
                    template,
                    tone,
                    recipient,
                    user_message,
                    variation=0,
                    seasonal_text=seasonal_text,
                )
                st.session_state.generated_email = base_email

                user_display_text = (
                    f"{user_message}\n\n"
                    f"――――――――――\n"
                    f"テンプレート: {template} / トーン: {tone} / 相手: {recipient}"
                )
                st.session_state.messages.append({"role": "user", "content": user_display_text})

                guide = (
                    f"{template}メールを「{tone}」なトーンで、"
                    f"{recipient}宛に作成しました！右側のプレビューをご覧ください。"
                )
                st.session_state.messages.append({"role": "assistant", "content": guide})

                st.session_state.ai_suggestions = generate_email_with_openai(
                    template=template,
                    tone=tone,
                    recipient=recipient,
                    message=user_message,
                    seasonal_text=seasonal_text,
                )

                if HAS_DB:
                    try:
                        save_email_record(
                            template=template,
                            tone=tone,
                            recipient=recipient,
                            seasonal_text=seasonal_text or "",
                            user_message=user_message,
                            subject=base_email["subject"],
                            body=base_email["body"],
                            ai_suggestions=st.session_state.ai_suggestions,
                        )
                    except Exception as e:
                        st.warning(f"DB保存時にエラーが発生しました: {e}")

                if len(st.session_state.messages) > 50:
                    st.session_state.messages = st.session_state.messages[-50:]

                st.rerun()

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    chat_html_parts = ["<div class='chat-log'>"]
    for msg in st.session_state.messages:
        role = msg["role"]
        text = html.escape(msg["content"]).replace("\n", "<br>")
        if role == "user":
            chat_html_parts.append(f"<div class='chat-bubble user'>{text}</div>")
        else:
            chat_html_parts.append(f"<div class='chat-bubble assistant'><span>{text}</span></div>")
    chat_html_parts.append("</div>")
    st.markdown("\n".join(chat_html_parts), unsafe_allow_html=True)


# --------------------------------------------
# 右：AIが作った3パターンのプレビュー
# --------------------------------------------
with col2:
    ai_text = st.session_state.ai_suggestions

    if not ai_text:
        placeholder_html = textwrap.dedent(
            """
            <div class="preview-main-wrapper">
                <p><em>メッセージを送信すると、ここにAIが生成した3パターンのプレビューが表示されます。</em></p>
            </div>
            """
        )
        st.markdown(placeholder_html, unsafe_allow_html=True)
    else:
        # 行頭が「## パターン数字」の行で分割（MULTILINE）
        raw_blocks = re.split(r"(?=^##\s*パターン\s*\d+)", ai_text, flags=re.MULTILINE)
        blocks = [b.strip() for b in raw_blocks if b.strip()]

        # 先頭3つだけ使う
        blocks = blocks[:3]

        # 3つに満たない場合はプレースホルダで埋める
        while len(blocks) < 3:
            blocks.append("このパターンはまだ生成されていません。")

        # コピー用テキスト配列（元の Markdown まるごと）
        copy_texts = blocks.copy()

        for idx, block in enumerate(blocks):
            st.markdown(
                f"<div class='section-header'>◆ パターン {idx + 1}</div>",
                unsafe_allow_html=True,
            )

            parsed = parse_pattern_block(block)
            subj = html.escape(parsed["subject"] or "").replace("\n", "<br>")
            body = html.escape(parsed["body"] or "").replace("\n", "<br>")
            improve = html.escape(parsed["improve"] or "").replace("\n", "<br>")
            caution = html.escape(parsed["caution"] or "").replace("\n", "<br>")

            card_html = f"""
            <div class="preview-main-wrapper">
              <div class="preview-header">
                <span>パターン {idx + 1}</span>
                <span class="pattern-copy-icon"
                      data-pattern="{idx}"
                      title="メッセージをコピーします">📋</span>
              </div>

              <div style="margin-top:8px;">
                <div class="preview-section-label">件名</div>
                <div class="preview-subject">{subj}</div>
              </div>

              <div style="margin-top:12px;">
                <div class="preview-section-label">本文</div>
                <div class="preview-body">{body}</div>
              </div>

              <div style="margin-top:12px;">
                <div class="preview-section-label">改善点</div>
                <div class="preview-note-body">{improve}</div>
              </div>

              <div style="margin-top:12px;">
                <div class="preview-section-label">注意点</div>
                <div class="preview-note-body">{caution}</div>
              </div>
            </div>
            """

            st.markdown(card_html, unsafe_allow_html=True)

            # ボタン行（リセット／表現を変える）
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("リセット", key=f"reset_{idx}", use_container_width=True):
                    st.session_state.messages = []
                    st.session_state.last_user_message = ""
                    st.session_state.ai_suggestions = None
                    st.session_state.variation_count = 0
                    st.rerun()

            with btn_col2:
                if st.button("🔄 表現を変える", key=f"regen_{idx}", use_container_width=True):
                    if st.session_state.last_user_message:
                        st.session_state.variation_count += 1

                        st.session_state.ai_suggestions = generate_email_with_openai(
                            template=template,
                            tone=tone,
                            recipient=recipient,
                            message=st.session_state.last_user_message,
                            seasonal_text=seasonal_text,
                        )

                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": (
                                    f"AIによる新しい3パターン（バリエーション "
                                    f"{st.session_state.variation_count + 1}）を生成しました。"
                                ),
                            }
                        )
                        if len(st.session_state.messages) > 50:
                            st.session_state.messages = st.session_state.messages[-50:]
                    else:
                        st.warning("直近のユーザー入力が見つかりません。先にメッセージを送信してください。")

                    st.rerun()

            st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # コピーアイコン用 JS
        texts_json = json.dumps(copy_texts, ensure_ascii=False)

        st.components.v1.html(
            f"""
            <script>
            (function() {{
              const texts = {texts_json};

              function setupIcons() {{
                const icons = parent.document.querySelectorAll('.pattern-copy-icon');
                if (!icons || icons.length === 0) return;

                function copyText(text) {{
                  if (navigator.clipboard && navigator.clipboard.writeText) {{
                    navigator.clipboard.writeText(text).catch(function(err) {{
                      console.warn("navigator.clipboard failed:", err);
                      fallbackCopy(text);
                    }});
                  }} else {{
                    fallbackCopy(text);
                  }}
                }}

                function fallbackCopy(text) {{
                  try {{
                    const textarea = document.createElement('textarea');
                    textarea.value = text;
                    textarea.style.position = 'fixed';
                    textarea.style.top = '-9999px';
                    textarea.style.left = '-9999px';
                    document.body.appendChild(textarea);
                    textarea.focus();
                    textarea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textarea);
                  }} catch (e) {{
                    console.error("Fallback copy failed:", e);
                  }}
                }}

                icons.forEach(function(icon) {{
                  const idx = parseInt(icon.getAttribute('data-pattern'), 10);
                  if (!isNaN(idx) && texts[idx]) {{
                    icon.addEventListener('click', function() {{
                      copyText(texts[idx]);

                      // クリック時にキラッとアニメーション
                      icon.classList.remove('copy-flash');
                      void icon.offsetWidth;
                      icon.classList.add('copy-flash');
                    }});
                  }}
                }});
              }}

              setTimeout(setupIcons, 500);
            }})();
            </script>
            """,
            height=0,
        )
