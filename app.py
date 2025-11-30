import streamlit as st
from datetime import datetime
import random
import html
import textwrap
import json

# ============================================
# 時候の挨拶（ヘルパー）
# ============================================
def get_seasonal_greeting() -> str:
    """現在の月に応じた時候の挨拶を返す"""
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
# メール生成関数
# ============================================
def generate_email(template, tone, recipient, message, variation=0, seasonal_text: str | None = None):
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

    # ★ 時候の挨拶を greeting にだけ付与する
    if seasonal_text:
        greeting = f"{seasonal_text}、{base_greeting}"
    else:
        greeting = base_greeting

    # ★ body_variations から seasonal_block を削除
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
# カスタムCSS（統合版）
# ============================================
st.markdown(
    """
<style>
* {
    box-sizing: border-box;
}

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
    background-image: url('https://raw.githubusercontent.com/smzk13tp5kg/ARKY/main/ARKY%20background%20image.png');
    background-size: cover;
    background-position: center center;
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
body {
    background-color: #050b23;
}

/* メインエリア調整 */
main.block-container {
    padding-top: 0rem;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    max-width: 100% !important;
}

/* メインブロックの上下余白 */
.stMainBlockContainer {
    padding-top: 0 !important;
    padding-bottom: 10px !important;
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

/* サイドバー開閉ボタンのアイコン色 */
button[title="Open sidebar"] svg,
button[title="Close sidebar"] svg {
    fill: #ffffff !important;
    color: #ffffff !important;
}

/* -------------------------------------------
   3D フリップボタン（Pure CSS）
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

/* ボタン内部のdivは表示するが、透明度を下げる */
.stButton > button > div,
.stFormSubmitButton > button > div {
  position: relative;
  z-index: 10;
  color: #ffffff !important;
  font-weight: 700;
  text-transform: uppercase;
}

/* 新規作成ボタン用のラッパ（緑系の3Dフリップ） */
.create-button-container .stButton > button::before {
  background-color: #10b981;
  border-color: #10b981;
  color: #ffffff;
}

.create-button-container .stButton > button::after {
  background-color: #059669;
  border-color: #059669;
  color: #ffffff;
}

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
    color: #ffffff !important;
}

/* セクション見出し */
.section-header {
    font-size: 16px;
    font-weight: 700;
    color: #ffd666;
    margin: 8px 0;
}

/* タイトル直下のメッセージエリア（アイコン＋AIバブル） */
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

/* ★ グラデ枠＋グラデ文字の AI バブル ★ */
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

/* コピー案内テキスト（白文字） */
.copy-info {
    color: #ffffff;
    font-size: 13px;
    margin-bottom: 4px;
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
    position: relative;             /* ← しっぽの基準にする */
    background: #ffffff;
    color: #111827;
    margin-left: auto;              /* 右寄せしたい場合。左寄せなら消してOK */
    max-width: 80%;                 /* 余白を少し残すために調整（お好み） */
}

/* ユーザー吹き出しの“しっぽ”（右側） */
.chat-bubble.user::after {
    content: "";
    position: absolute;
    right: -8px;                    /* バブルの右外側に飛び出させる */
    top: 14px;                      /* 縦位置。お好みで調整 */
    width: 0;
    height: 0;
    border-style: solid;
    border-width: 8px 0 8px 8px;    /* 三角形のサイズ */
    border-color: transparent transparent transparent #ffffff;  /* ← バブルと同じ色 */

    /* 影をちょっと付けたい場合 */
    filter: drop-shadow(-1px 1px 2px rgba(0,0,0,0.15));
}

/* ★ AIチャットバブルを intro-bubble と同じスタイルに変更 ★ */
.chat-bubble.assistant {
    position: relative;
    padding: 0;                     /* 内側の padding はテキスト側で制御 */
    border-radius: 16px;
    background: transparent;
    overflow: visible;
    margin-right: auto;             /* 左寄せ（必要に応じて調整） */
    max-width: 85%;                 /* お好みで可変 */
}

/* 外側の光るグラデーション枠（assistant用） */
.chat-bubble.assistant::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 16px;
    padding: 4px; /* 枠の太さ */

    background: linear-gradient(120deg, #6559ae, #ff7159, #6559ae);
    background-size: 400% 400%;
    animation: intro-gradient 3s ease-in-out infinite;

    -webkit-mask:
      linear-gradient(#000 0 0) content-box,
      linear-gradient(#000 0 0);
    -webkit-mask-composite: xor;
            mask-composite: exclude;
}

/* 内側テキストのグラデーション（assistant用） */
.chat-bubble.assistant > span {
    position: relative;
    display: block;
    padding: 10px 18px;
    border-radius: 12px;

    background: rgba(5, 11, 35, 0.85);      /* 半透明背景 */
    background-image: linear-gradient(120deg, #fdfbff, #ffd7b2, #ffe6ff);
    background-size: 400% 400%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;

    font-size: 14px;
    font-weight: 600;
    line-height: 1.6;

    animation: intro-gradient 3s ease-in-out infinite;
}

/* Streamlit の要素コンテナ余白を削る */
.stElementContainer {
    margin: 0 !important;
    padding: 0 !important;
}

/* 一部アイコンの色を白に */
.st-emotion-cache-pd6qx2 {
    color: #ffffff !important;
    fill: #ffffff !important;
}

/* サイドバー上部ヘッダー（黄色で囲った余白）の高さを詰める */
[data-testid="stSidebarHeader"] {
    min-height: 0 !important;
    height: 0 !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

/* サイドバーコンテンツの上パディングも少しだけにする */
[data-testid="stSidebarContent"] {
    padding-top: 7px !important;   /* 0でもいいけど、開閉アイコンが見えなくなるからこれくらいが自然かも */
}


</style>
""",
    unsafe_allow_html=True,
)

# ============================================
# JavaScriptでボタンテキストを動的に設定
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
      
      // 初回実行
      setTimeout(updateButtonText, 500);
      
      // MutationObserverで動的に追加されるボタンも監視
      const observer = new MutationObserver(updateButtonText);
      observer.observe(parent.document.body, {
        childList: true,
        subtree: true
      });
      
      // 定期的にも実行
      setInterval(updateButtonText, 1000);
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

    # 新規作成ボタン（緑系3D）
    st.markdown("<div class='create-button-container'>", unsafe_allow_html=True)
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
                "🙏 厳粛・儀礼的（謝罪・クレーム対応）",
                "⏱️ 緊急・簡潔（即時対応が必要な通知）",
                "🌿 柔らかめ（関係維持・お礼・広報向け）",
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

    # 時候の挨拶
    with st.container():
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

    # タイトル直下のメッセージエリア（アイコン＋AIグラデバブル）
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

    # フォーム（intro-bubble の直下）
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
                    template, tone, recipient, user_message, variation=0, seasonal_text=seasonal_text
                )
                st.rerun()

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 送信済みメッセージ一覧（ユーザー＆アシスタント）
    chat_html_parts = []
    chat_html_parts.append("<div class='chat-log'>")

    for msg in st.session_state.messages:
        role = msg["role"]
        text = html.escape(msg["content"]).replace("\n", "<br>")
        if role == "user":
            chat_html_parts.append(
                f"<div class='chat-bubble user'>{text}</div>"
            )
        else:
            # ★ span で包むのがポイント
            chat_html_parts.append(
                f"<div class='chat-bubble assistant'><span>{text}</span></div>"
            )

    chat_html_parts.append("</div>")
    st.markdown("\n".join(chat_html_parts), unsafe_allow_html=True)

# --------------------------------------------
# 右：プレビュー
# --------------------------------------------
with col2:
    st.markdown("<div class='section-header'>📄 プレビュー</div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

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

# ---------- コピー ボタン ----------
        with btn_col1:
            full_text = f"件名: {email['subject']}\n\n{email['body']}"
            copy_button_id = f"copy_btn_{random.randint(1000, 9999)}"
            escaped_text = json.dumps(full_text)
            
            html_code = f"""
<div style="perspective: 1000px; width: 100%;">
    <button id="{copy_button_id}" 
            style="position: relative; width: 100%; height: 50px; 
                   font-size: 1.0rem; font-weight: 700; 
                   text-transform: uppercase; cursor: pointer; 
                   border: none; background: transparent;
                   transform-style: preserve-3d; 
                   transform: translateZ(-25px);
                   transition: transform 0.25s;">
        <div style="position: absolute; width: 100%; height: 50px; 
                    display: flex; align-items: center; justify-content: center;
                    border: 5px solid #ff8c00; box-sizing: border-box; 
                    border-radius: 8px; left: 0; top: 0;
                    background-color: #ff8c00; color: #ffffff;
                    transform: rotateY(0deg) translateZ(25px);">
            📋 コピー
        </div>
        <div style="position: absolute; width: 100%; height: 50px; 
                    display: flex; align-items: center; justify-content: center;
                    border: 5px solid #ffd700; box-sizing: border-box; 
                    border-radius: 8px; left: 0; top: 0;
                    background-color: #ffd700; color: #ffffff;
                    transform: rotateX(90deg) translateZ(25px);">
            📋 コピー
        </div>
    </button>
    <div id="copy_status_{copy_button_id}" 
         style="color: #ffffff; font-size: 13px; margin-top: 8px; 
                min-height: 20px; text-align: center;"></div>
</div>
<script>
(function() {{
    const btn = document.getElementById('{copy_button_id}');
    const statusDiv = document.getElementById('copy_status_{copy_button_id}');
    const textToCopy = {escaped_text};
    
    btn.addEventListener('mouseenter', function() {{
        this.style.transform = 'translateZ(-25px) rotateX(-90deg)';
    }});
    
    btn.addEventListener('mouseleave', function() {{
        this.style.transform = 'translateZ(-25px)';
    }});
    
    btn.addEventListener('click', function() {{
        const textarea = document.createElement('textarea');
        textarea.value = textToCopy;
        textarea.style.position = 'fixed';
        textarea.style.left = '-9999px';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();
        
        try {{
            const success = document.execCommand('copy');
            document.body.removeChild(textarea);
            
            if (success) {{
                statusDiv.textContent = '✔ コピーしました';
                statusDiv.style.color = '#10b981';
                setTimeout(function() {{
                    statusDiv.textContent = '';
                    statusDiv.style.color = '#ffffff';
                }}, 3000);
            }} else {{
                statusDiv.textContent = '⚠ コピーに失敗しました';
                statusDiv.style.color = '#ef4444';
            }}
        }} catch (e) {{
            if (textarea.parentNode) {{
                document.body.removeChild(textarea);
            }}
            statusDiv.textContent = '⚠ コピーに失敗しました';
            statusDiv.style.color = '#ef4444';
        }}
    }});
}})();
</script>
"""
            st.markdown(html_code, unsafe_allow_html=True)
            
        # ---------- 再生成 ボタン ----------
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
                        seasonal_text=seasonal_text,
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




