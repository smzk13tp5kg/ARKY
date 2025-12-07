import streamlit as st
from datetime import datetime
import html
import textwrap
import json
import re

# ============================================
# ページ設定（アプリの最重要設定：最優先で実行）
# ============================================
st.set_page_config(
    page_title="ビジネスメール作成アシスタント",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 外部ロジックをインポート
from openai_logic import generate_email_with_openai

# DB保存ロジック（あれば使う）
try:
    from db_logic import save_email_batch
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
        rest = block[pos_body_label + len("本文:"):]
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
    padding-left: 2.0rem !important;
    padding-right: 2.0rem !important;
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
    width: 400px !important;
    min-width: 400px !important;
    max-width: 400px !important;
    background: #050b23;
    border-right: 1px solid #cfae63;
}

/* サイドバーの開閉ボタン（≪アイコン）の色設定 */
[data-testid="stSidebar"] [data-testid="collapsedControl"] {
    color: #cfae63 !important;
}
[data-testid="stSidebar"] [data-testid="collapsedControl"] svg {
    color: #cfae63 !important;
    fill: #cfae63 !important;
}

/* サイドバー内のテキストは白色 */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span:not([data-testid="collapsedControl"] span),
[data-testid="stSidebar"] div:not([data-testid="collapsedControl"]),
[data-testid="stSidebar"] p {
    color: #ffffff !important;
}

/* ラジオボタンのラベルテキストも白 */
[data-testid="stSidebar"] .stRadio label {
    color: #ffffff !important;
}

/* 開閉ボタン内のテキストだけゴールド */
[data-testid="stSidebar"] [data-testid="collapsedControl"] span {
    color: #cfae63 !important;
}

/* サイドバー上部ヘッダー縮小 */
[data-testid="stSidebarHeader"] {
    min-height: 0 !important;
    height: 0 !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}
[data-testid="stSidebarContent"] {
    padding-top: 0px !important;
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
.stFormSubmitButton > button::before,
.stButton > button::after,
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

/* メインブロック（stMainBlockContainer）の上パディング */
div.stMainBlockContainer {
    padding-top: 6px !important;
}
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

/* コピー用ボタン（パターン用） */
.pattern-copy-icon {
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    margin-left: 8px;
    font-size: 13px;
    font-weight: 600;
    border-radius: 999px;
    border: 1px solid #ffd666;
    background: #111827;
    color: #ffffff;
    transition:
        transform 0.15s ease-out,
        box-shadow 0.15s ease-out,
        background-color 0.15s ease-out,
        border-color 0.15s ease-out;
}
.pattern-copy-icon:hover {
    background: #1f2937;
    border-color: #ffea99;
}

/* クリック時のキラッとエフェクト */
.pattern-copy-icon.copy-flash {
    animation: copy-flash 0.5s ease-out;
}
@keyframes copy-flash {
    0% {
        transform: scale(1);
        box-shadow: none;
        background-color: #111827;
        border-color: #ffd666;
        color: #ffffff;
    }
    30% {
        transform: scale(1.05);
        box-shadow: 0 0 10px rgba(255, 214, 102, 0.8);
        background-color: #ffd666;
        border-color: #ffe9a3;
        color: #111827;
    }
    100% {
        transform: scale(1);
        box-shadow: none;
        background-color: #111827;
        border-color: #ffd666;
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
    width: 130px;
    height: 130px;
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

/* 右：プレビューカード（グラデーション枠つき） */
.preview-main-wrapper {
    position: relative;
    background: #ffffff;
    border-radius: 12px;
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

/* グラデーション枠（イントロバブル系） */
.preview-main-wrapper::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 12px;
    padding: 3px;

    background: linear-gradient(
        120deg,
        #6559ae,
        #ff7159,
        #ffd666,
        #ff7159,
        #6559ae
    );
    background-size: 400% 400%;
    animation: preview-gradient 4s ease-in-out infinite;

    -webkit-mask:
        linear-gradient(#000 0 0) content-box,
        linear-gradient(#000 0 0);
    -webkit-mask-composite: xor;
            mask-composite: exclude;
}

/* グラデーションの動き */
@keyframes preview-gradient {
    0% {
        background-position: 0% 0%;
        box-shadow: 0 0 0px rgba(255, 214, 102, 0.0);
    }
    50% {
        background-position: 100% 100%;
        box-shadow: 0 0 14px rgba(255, 214, 102, 0.4);
    }
    100% {
        background-position: 0% 0%;
        box-shadow: 0 0 0px rgba(255, 214, 102, 0.0);
    }
}

/* プレビュー本文など（中身）はそのまま */
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
    animation: assistant-glow-text 3s ease-in-out infinite;
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

/* カスタムテンプレート入力ボックス（その他） */
[data-testid="stSidebar"] [data-testid="stTextInput"] > div {
    width: calc(100% - 30px) !important;
    margin-left: 0 !important;
    background: transparent !important;
}
[data-testid="stSidebar"] [data-testid="stTextInput"] input {
    width: 100% !important;
    background-color: #330033 !important;
    border: 5px solid #ffffcc !important;
    color: #ffffff !important;
    padding: 6px 10px !important;
    border-radius: 8px !important;
}

/* 右ペインの Streamlit 標準ヘッダーを高さ0にする（非表示に近い） */
[data-testid="stHeader"] {
    height: 0 !important;
    min-height: 0 !important;
    max-height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    overflow: hidden !important;
    background: transparent !important;
    border: none !important;
}

/* プレビュータブの見た目カスタマイズ（パターン1〜3用） */
.stTabs {
    margin-top: 4px;
}
.stTabs [role="tablist"] {
    gap: 0.5rem;
}
.stTabs [role="tablist"] > [role="tab"] {
    position: relative;
    border: none;
    background: transparent;
    opacity: 1 !important;
    border-radius: 999px;
    padding: 0;
    color: #ffffff !important;
    font-weight: 600;
    font-size: 13px;
    cursor: pointer;
}
.stTabs [role="tablist"] > [role="tab"] > div {
    position: relative;
    border-radius: inherit;
    padding: 4px 16px;
}
/* グラデ枠 */
.stTabs [role="tablist"] > [role="tab"]::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 999px;
    padding: 2px;
    background: linear-gradient(120deg, #6559ae, #ff7159, #ffd666, #ff7159, #6559ae);
    background-size: 400% 400%;
    animation: tab-gradient 4s ease-in-out infinite;
    -webkit-mask:
      linear-gradient(#000 0 0) content-box,
      linear-gradient(#000 0 0);
    -webkit-mask-composite: xor;
            mask-composite: exclude;
}
@keyframes tab-gradient {
    0%   { background-position: 0% 0%;   box-shadow: 0 0 0px rgba(255,214,102,0.0); }
    50%  { background-position: 100% 100%; box-shadow: 0 0 10px rgba(255,214,102,0.4); }
    100% { background-position: 0% 0%;   box-shadow: 0 0 0px rgba(255,214,102,0.0); }
}
/* パターン別背景色 */
.stTabs [role="tablist"] > [role="tab"]:nth-child(1) > div {
    background-color: #990000;
}
.stTabs [role="tablist"] > [role="tab"]:nth-child(2) > div {
    background-color: #660066;
}
.stTabs [role="tablist"] > [role="tab"]:nth-child(3) > div {
    background-color: #336600;
}
/* 選択中タブの光り方 */
.stTabs [role="tablist"] > [role="tab"][aria-selected="true"] > div {
    box-shadow: 0 0 8px rgba(255,214,102,0.6);
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
if "variation_count" not in st.session_state:
    st.session_state.variation_count = 0
if "ai_suggestions" not in st.session_state:
    st.session_state.ai_suggestions = None
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False

# 生成に必要なパラメータ
for key in [
    "pending_template",
    "pending_tone",
    "pending_recipient",
    "pending_seasonal_text",
    "pending_add_seasonal",
]:
    if key not in st.session_state:
