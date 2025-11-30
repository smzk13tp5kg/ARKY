import streamlit as st
from datetime import datetime
import random
import html
import textwrap

# ============================================
# メール生成関数
# ============================================
def generate_email(template, tone, recipient, message, variation=0):
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
    template_subjects = subject_variations.get(template, [f"{template} - {message[:20]}"])
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
    greeting = greeting_list[variation % len(greeting_list)]

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
    closing = closing_list[variation % len(closings_variations)]

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
* {
    box-sizing: border-box;
}

/* 全体背景：濃い紺色 */
.stApp {
    background-color: #050b23;
}
[data-testid="stAppViewContainer"] {
    background-color: #050b23;
}
[data-testid="stHeader"] {
    background-color: #050b23;
}
body {
    background-color: #050b23;
}

/* メインエリア調整 */
main.block-container {
    padding-top: 0.5rem;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    max-width: 100% !important;
}

/* カラム、ブロックの幅調整 */
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

# ==============================
# ボタン用カスタムCSS（デフォルト＝オレンジ×白、辞書ボタンだけ青系）
# ==============================
st.markdown(
    """
<style>
/* ▼▼ デフォルト：全ての st.button / st.form_submit_button をオレンジ＋白に（3D効果付き） ▼▼ */
.stButton > button,
.stFormSubmitButton > button {
  font-size: 1.0rem;
  font-weight: 700;
  line-height: 1.5;
  position: relative;
  display: inline-block;
  padding: 0.7rem 1.8rem;
  cursor: pointer;
  user-select: none;
  transition: all 0.3s ease;
  text-align: center;
  vertical-align: middle;
  text-decoration: none;
  letter-spacing: 0.05em;
  color: #ffffff !important;
  border-radius: 0.5rem;
  background: #ff8c00;  /* オレンジ */
  border: none;
  overflow: visible;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2), 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* テキストを前面に出す */
.stButton > button > div,
.stFormSubmitButton > button > div {
  position: relative;
  z-index: 1;
  color: #ffffff !important;
}

/* ホバー時：黄色に変更＋押し込み効果 */
.stButton > button:hover,
.stFormSubmitButton > button:hover {
  background: #ffd700 !important;  /* 黄色 */
  color: #ffffff !important;
  transform: translateY(2px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2), 0 1px 2px rgba(0, 0, 0, 0.1);
}

.stButton > button:hover > div,
.stFormSubmitButton > button:hover > div {
  color: #ffffff !important;
}

/* アクティブ時：さらに押し込む */
.stButton > button:active,
.stFormSubmitButton > button:active {
  transform: translateY(4px);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

/* ▼▼ 新規作成ボタン用のラッパ（緑系の3Dボタン） ▼▼ */
.create-button-container .stButton > button {
    position: relative;
    width: 100%;
    padding: 0.9rem 1.5rem;
    border-radius: 12px;
    background: #10b981;  /* 緑 */
    color: #ffffff !important;
    text-align: center;
    font-size: 1.0rem;
    font-weight: 700;
    overflow: visible;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2), 0 2px 4px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    border: none;
}

.create-button-container .stButton > button > div {
    color: #ffffff !important;
    z-index: 1;
}

.create-button-container .stButton > button:hover {
    background: #059669 !important;  /* 濃い緑 */
    color: #ffffff !important;
    transform: translateY(2px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.create-button-container .stButton > button:hover > div {
    color: #ffffff !important;
}

/* ▼▼ 辞書ビュー用：用語一覧ボタン（AliceBlue / Azure）に上書き ▼▼ */
.term-button-container .stButton > button {
    position: relative;
    width: 100%;
    padding: 0.9rem 1.1rem;
    border-radius: 12px;
    border: 1px solid #F0FFFF;       /* Azure */
    background-color: #F0F8FF;       /* AliceBlue */
    color: #111827 !important;
    text-align: left;
    font-size: 0.90rem;
    font-weight: 500;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
}

/* 用語ボタン内テキストを前面に */
.term-button-container .stButton > button > div {
    position: relative;
    z-index: 2;
    color: #111827 !important;
}

/* 用語ボタンのスライドアニメ：Azure */
.term-button-container .stButton > button::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: #F0FFFF;             /* Azure */
    transform: translateX(-96%);
    transition: transform .5s ease-in-out;
    z-index: 1;
}

/* Hover時：スライドイン（用語ボタン） */
.term-button-container .stButton > button:hover::before {
    transform: translateX(0%);
}

/* Hover時テキスト色（用語ボタン） */
.term-button-container .stButton > button:hover {
    color: #111827 !important;
    transform: translateY(2px);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}

.term-button-container .stButton > button:hover > div {
    color: #111827 !important;
}
</style>
""",
    unsafe_allow_html=True,
)

/* -------------------------------------------
   メインエリア
------------------------------------------- */

/* トップバー */
.top-bar {
    background: #050b23;
    padding: 16px 8px 8px 8px;
    border-bottom: 1px solid #cfae63;
    margin-bottom: 20px;
}
.app-title {
    font-size: 24px;
    font-weight: 700;
    color: #ffffff !重要;
}

/* セクション見出し */
.section-header {
    font-size: 16px;
    font-weight: 700;
    color: #ffd666;
    margin: 8px 0;
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
    margin-bottom: 16px;
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
    min-height: 200px;
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
.copy-area textarea {
    background: #f3f4f6 !important;
    border-radius: 8px !important;
    border: 1px solid #d1d5db !important;
    color: #111827 !important;
    font-size: 12px !important;
    width: 100% !important;
}

/* ============================================
   チャットメッセージ（自前バブル表示）
============================================ */
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
    background: #ffffff;
    color: #111827;
}
.chat-bubble.assistant {
    background: linear-gradient(180deg, #ffd666 0%, #f4a021 100%);
    color: #ffffff;
}

</style>
""",
    unsafe_allow_html=True,
)

# ============================================
# セッション状態初期化
# ============================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "generated_email" not in st.session_state:
    st.session_state.generated_email = None
if "variation_count" not in st.session_state:
    st.session_state.variation_count = 0

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

    # 新規作成
    st.markdown("<div class='sidebar-new-btn'>", unsafe_allow_html=True)
    if st.button("新規作成", use_container_width=True):
        st.session_state.messages = []
        st.session_state.generated_email = None
        st.session_state.variation_count = 0
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # テンプレート
    with st.container():
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
    with st.container():
        st.markdown("<div class='nav-section'>", unsafe_allow_html=True)
        st.markdown("<div class='nav-label'>トーン</div>", unsafe_allow_html=True)
        tone_display = st.radio(
            "トーン",
            [
                "😊 カジュアル／フレンドリー（同僚向け）",
                "📄 標準ビジネス（最も一般的）",
                "📘 フォーマル（社外顧客／上位者／依頼交渉）",
                "🙏 厳粛・儀礼的（謝罪・不祥事・クレーム対応）",
                "⏱️ 緊急・簡潔（即時対応が必要な通知）",
                "🌿 柔らかめ（関係維持・お礼・広報向け）",
            ],
            index=1,
            label_visibility="collapsed",
            key="tone_radio",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    display_to_tone = {
        "😊 カジュアル／フレンドリー（同僚・社内フラット向け）": "カジュアル／フレンドリー",
        "📄 標準ビジネス（最も一般的）": "標準ビジネス",
        "📘 フォーマル（社外顧客／上位者／依頼交渉）": "フォーマル",
        "🙏 厳粛・儀礼的（謝罪・不祥事・クレーム対応）": "厳粛・儀礼的",
        "⏱️ 緊急・簡潔（即時対応が必要な通知）": "緊急・簡潔",
        "🌿 柔らかめ（関係維持・お礼・広報向け）": "柔らかめ",
    }
    tone = display_to_tone[tone_display]

    # 相手
    with st.container():
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

    # ナビゲーションエリア最下部：入力フォーム
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div class='card input-card'>", unsafe_allow_html=True)
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
                st.session_state.messages.append({"role": "user", "content": user_message})

                response = (
                    f"{template}メールを「{tone}」なトーンで、"
                    f"{recipient}宛に作成しました！右側のプレビューをご覧ください。"
                )
                st.session_state.messages.append({"role": "assistant", "content": response})

                st.session_state.variation_count = 0
                st.session_state.generated_email = generate_email(
                    template, tone, recipient, user_message, variation=0
                )
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.caption("© 2025 ARKY")

# ============================================
# メイン 2 カラム
# ============================================
col1, col2 = st.columns([3, 2], gap="medium")

with col1:
    st.markdown("<div class='section-header'>💬 メッセージ</div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='section-header'>📄 プレビュー</div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

# ============================================
# 左：メッセージエリア（自前チャット表示）
# ============================================
with col1:
    chat_html_parts = []
    chat_html_parts.append("<div class='chat-log'>")

    if not st.session_state.messages:
        initial_msg = (
            "こんにちは！ビジネスメールの作成をお手伝いします。<br><br>"
            "左側のナビゲーションエリアでテンプレートやトーン、相手を選び、"
            "下部の入力欄からメッセージ内容を入力してください。"
        )
        chat_html_parts.append(
            f"<div class='chat-bubble assistant'>{initial_msg}</div>"
        )
    else:
        for msg in st.session_state.messages:
            role = msg["role"]
            text = html.escape(msg["content"]).replace("\n", "<br>")
            if role == "user":
                chat_html_parts.append(
                    f"<div class='chat-bubble user'>{text}</div>"
                )
            else:
                chat_html_parts.append(
                    f"<div class='chat-bubble assistant'>{text}</div>"
                )

    chat_html_parts.append("</div>")
    st.markdown("\n".join(chat_html_parts), unsafe_allow_html=True)

# ============================================
# 右：プレビューエリア
# ============================================
with col2:
    if st.session_state.generated_email is None:
        placeholder_html = textwrap.dedent(
            """
            <div class="preview-main-wrapper">
                <p><em>メールを生成すると、ここにプレビューが表示されます。</em></p>
            </div>
            """
        )
        st.markdown(placeholder_html, unsafe_allow_html=True)

    else:
        email = st.session_state.generated_email

        body_html = html.escape(email["body"]).replace("\n", "<br>")
        subject_html = html.escape(email["subject"])

        preview_html = textwrap.dedent(
            f"""
            <div class="preview-main-wrapper">
                <p><strong>件名</strong></p>
                <p>{subject_html}</p>
                <hr>
                <p><strong>本文</strong></p>
                <p>{body_html}</p>
            </div>
            """
        )
        st.markdown(preview_html, unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        advice_html = textwrap.dedent(
            f"""
            <div class="advice-box">
                <strong>💡 アドバイス</strong><br>
                {email['advice']}
            </div>
            """
        )
        st.markdown(advice_html, unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        st.markdown("<div class='preview-actions'>", unsafe_allow_html=True)
        btn_col1, btn_col2 = st.columns(2)

        with btn_col1:
            if st.button("📋 コピー", use_container_width=True):
                full_text = f"件名: {email['subject']}\n\n{email['body']}"
                st.info("以下のテキストをコピーしてご利用ください。")
                st.markdown("<div class='copy-area'>", unsafe_allow_html=True)
                st.text_area(
                    "コピー用テキスト",
                    full_text,
                    height=120,
                    label_visibility="collapsed",
                )
                st.markdown("</div>", unsafe_allow_html=True)

        with btn_col2:
            if st.button("🔄 再生成", use_container_width=True):
                st.session_state.messages.append(
                    {"role": "assistant", "content": "メールを再生成しています..."}
                )

                last_user_message = None
                for msg in reversed(st.session_state.messages):
                    if msg["role"] == "user":
                        last_user_message = msg["content"]
                        break

                if last_user_message:
                    st.session_state.variation_count += 1
                    st.session_state.generated_email = generate_email(
                        template,
                        tone,
                        recipient,
                        last_user_message,
                        variation=st.session_state.variation_count,
                    )
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": (
                                f"新しいバージョン（バリエーション "
                                f"{st.session_state.variation_count + 1}）を生成しました！プレビューをご確認ください。"
                            ),
                        }
                    )

                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


