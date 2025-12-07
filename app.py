import streamlit as st
from datetime import datetime
import html
import textwrap
import json
import re

# ============================================
# ページ設定（アプリの最重要設定）
# ============================================
st.set_page_config(
    page_title="ビジネスメール作成アシスタント",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 外部ロジック
from openai_logic import generate_email_with_openai

try:
    from db_logic import save_email_batch
    HAS_DB = True
except:
    HAS_DB = False


# ============================================
# 時候の挨拶
# ============================================
def get_seasonal_greeting() -> str:
    month = datetime.now().month
    greetings = {
        1: "新春の候", 2: "余寒の候", 3: "早春の候", 4: "春暖の候",
        5: "新緑の候", 6: "初夏の候", 7: "盛夏の候", 8: "晩夏の候",
        9: "初秋の候", 10: "秋涼の候", 11: "晩秋の候", 12: "師走の候"
    }
    return greetings.get(month, "")


# ============================================
# パターン解析
# ============================================
def parse_pattern_block(block: str) -> dict:
    block = re.sub(r"^##\s*パターン[^\n]*\n?", "", block, count=1, flags=re.MULTILINE)

    subject = ""
    body = ""
    improve = ""
    caution = ""

    m = re.search(r"件名[:：]\s*(.+)", block)
    if m:
        subject = m.group(1).strip()

    pos = block.find("本文:")
    rest = block[pos + len("本文:"):] if pos != -1 else block

    idx_i = rest.find("- 改善点")
    idx_c = rest.find("- 注意点")

    if idx_i != -1:
        body = rest[:idx_i].strip()
        rest2 = rest[idx_i:]
    else:
        body = rest.strip()
        rest2 = ""

    if "- 注意点" in rest2:
        sp = rest2.find("- 注意点")
        improve = rest2[:sp].strip()
        caution = rest2[sp:].strip()
    else:
        improve = rest2.strip()

    improve = re.sub(r"^-+\s*改善点[:：]?\s*", "", improve)
    caution = re.sub(r"^-+\s*注意点[:：]?\s*", "", caution)

    return {
        "subject": subject,
        "body": body,
        "improve": improve,
        "caution": caution,
    }


# ============================================
# CSS（※ここは省略、あなたの最新CSSをそのまま貼る）
# ============================================
st.markdown("""<style>
/* ------ あなたの CSS 全文をここに貼ってください（省略） ------ */
</style>""", unsafe_allow_html=True)


# ============================================
# JS：ボタンに data-text を付与
# ============================================
st.components.v1.html("""
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
""", height=0)


# ============================================
# セッション状態
# ============================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_user_message" not in st.session_state:
    st.session_state.last_user_message = ""

if "ai_suggestions" not in st.session_state:
    st.session_state.ai_suggestions = None

if "need_generate" not in st.session_state:
    st.session_state.need_generate = False

for key in ["pending_template", "pending_tone", "pending_recipient",
            "pending_seasonal_text", "pending_add_seasonal"]:
    if key not in st.session_state:
        st.session_state[key] = None


# ============================================
# トップバー
# ============================================
st.markdown("<div class='top-bar'><h1 class='app-title'>✉️ ビジネスメール作成アシスタント</h1></div>", unsafe_allow_html=True)


# ============================================
# サイドバー
# ============================================
with st.sidebar:
    st.markdown("<div class='sidebar-app-title'>■ メール生成AI</div>", unsafe_allow_html=True)

    # テンプレート
    template_display = st.radio(
        "テンプレート",
        ["📧 依頼メール", "✉️ 提案メール", "🙏 お礼メール", "💼 謝罪メール", "📩 挨拶メール", "➕ その他"],
        index=0,
        label_visibility="collapsed",
        key="template_radio",
    )
    display_to_template = {
        "📧 依頼メール": "依頼", "✉️ 提案メール": "提案", "🙏 お礼メール": "お礼",
        "💼 謝罪メール": "謝罪", "📩 挨拶メール": "挨拶", "➕ その他": "その他",
    }
    template = display_to_template[template_display]

    custom_template = None
    if template == "その他":
        custom_template = st.text_input("カスタムテンプレート", placeholder="例: 報告")
        template = custom_template if custom_template else "その他"

    # トーン
    tone_display = st.radio(
        "トーン",
        ["😊 カジュアル／フレンドリー（同僚向け）",
         "📄 標準ビジネス（最も一般的）",
         "📘 フォーマル（社外／上位者／依頼交渉）",
         "🙏 厳粛・儀礼的（謝罪・クレーム対応）",
         "⏱️ 緊急・簡潔（即時通知）",
         "🌿 ソフト（関係維持・お礼・広報）"],
        index=1,
        label_visibility="collapsed",
        key="tone_radio",
    )
    display_to_tone = {
        "😊 カジュアル／フレンドリー（同僚向け）": "カジュアル／フレンドリー",
        "📄 標準ビジネス（最も一般的）": "標準ビジネス",
        "📘 フォーマル（社外／上位者／依頼交渉）": "フォーマル",
        "🙏 厳粛・儀礼的（謝罪・クレーム対応）": "厳粛・儀礼的",
        "⏱️ 緊急・簡潔（即時通知）": "緊急・簡潔",
        "🌿 ソフト（関係維持・お礼・広報）": "柔らめ",
    }
    tone = display_to_tone[tone_display]

    # 相手
    recipient_display = st.radio(
        "相手",
        ["👤 上司", "😊 同僚", "👔 部下", "🏢 社外企業社員", "🏪 取引先", "➕ その他"],
        index=0,
        label_visibility="collapsed",
        key="recipient_radio",
    )
    display_to_recipient = {
        "👤 上司": "上司", "😊 同僚": "同僚", "👔 部下": "部下",
        "🏢 社外企業社員": "社外企業社員", "🏪 取引先": "取引先", "➕ その他": "その他",
    }
    recipient = display_to_recipient[recipient_display]

    custom_recipient = None
    if recipient == "その他":
        custom_recipient = st.text_input("カスタム相手", placeholder="例: 顧客")
        recipient = custom_recipient if custom_recipient else "その他"

    # 時候の挨拶
    seasonal_option = st.radio(
        "時候の挨拶",
        ["不要", "追加する"],
        index=0,
        label_visibility="collapsed",
        key="seasonal_radio",
    )
    add_seasonal = seasonal_option == "追加する"
    seasonal_text = get_seasonal_greeting() if add_seasonal else ""

    st.caption("© 2025 ARKY")


# ============================================
# メイン 2 カラム
# ============================================
col1, col2 = st.columns([1, 1], gap="medium")

# --------------------------------------------
# 左：メッセージフォーム
# --------------------------------------------
with col1:

    st.markdown("<div class='section-header'>💬 メッセージ</div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="intro-wrapper">
      <div class="intro-icon">
        <img src="https://raw.githubusercontent.com/smzk13tp5kg/ARKY/main/AIhontai.png">
      </div>
      <div class="intro-bubble">
        <span class="intro-bubble-text">
          ようこそ！<br>
          左側でテンプレートやトーンを設定し、<br>
          下のメッセージ欄に内容を入力してください。
        </span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    with st.form("message_form", clear_on_submit=True):
        user_message = st.text_area(
            "メッセージを入力",
            placeholder="例：使用する会議室の交換をお願いしたい",
            height=120,
            label_visibility="collapsed",
        )

        submit_col, reset_col = st.columns([1, 1])
        with submit_col:
            submitted = st.form_submit_button("✓ 送信", use_container_width=True)
        with reset_col:
            reset_clicked = st.form_submit_button("リセット", use_container_width=True)

    # フォーム送信処理（1st ステップ）
    if submitted and user_message:
        st.session_state.last_user_message = user_message

        st.session_state.pending_template = template
        st.session_state.pending_tone = tone
        st.session_state.pending_recipient = recipient
        st.session_state.pending_seasonal_text = seasonal_text
        st.session_state.pending_add_seasonal = add_seasonal

        st.session_state.ai_suggestions = None    # 初期化
        st.session_state.need_generate = True     # 「生成中」フラグON

        st.experimental_rerun()

    elif reset_clicked:
        st.session_state.messages = []
        st.session_state.last_user_message = ""
        st.session_state.ai_suggestions = None
        st.session_state.need_generate = False

        for key in ["pending_template", "pending_tone", "pending_recipient",
                    "pending_seasonal_text", "pending_add_seasonal"]:
            st.session_state[key] = None

        st.experimental_rerun()


# --------------------------------------------
# 右：プレビューエリア
# --------------------------------------------
with col2:

    ai_text = st.session_state.ai_suggestions
    generating = st.session_state.need_generate

    # ========================
    # ① パターン未生成のとき
    # ========================
    if ai_text is None:

        if generating:
            msg_html = "メッセージを生成しています・・・<br>数秒お待ちください。"
        else:
            msg_html = "送信ボタンをクリックすると、ここにAIが生成したメッセージが表示されます。"

        placeholder_html = f"""
        <div class="preview-main-wrapper">
          <div class="preview-header"><span></span></div>
          <p style="font-size:14px; color:#4b5563; margin:0; margin-top:8px;">
            {msg_html}
          </p>
        </div>
        """
        st.markdown(placeholder_html, unsafe_allow_html=True)

    # ========================
    # ② パターン生成済み → タブ表示
    # ========================
    else:

        raw_blocks = re.split(r"(?=^##\s*パターン\s*\d+)", ai_text, flags=re.MULTILINE)
        blocks = [b.strip() for b in raw_blocks if b.strip()]
        blocks = blocks[:3]

        while len(blocks) < 3:
            blocks.append("このパターンはまだ生成されていません。")

        copy_texts = blocks.copy()

        tabs = st.tabs([f"パターン {i+1}" for i in range(3)])

        for idx, (tab, block) in enumerate(zip(tabs, blocks)):
            with tab:
                parsed = parse_pattern_block(block)

                subj = html.escape(parsed["subject"] or "").replace("\n", "<br>")
                body = html.escape(parsed["body"] or "").replace("\n", "<br>")
                improve = html.escape(parsed["improve"] or "").replace("\n", "<br>")
                caution = html.escape(parsed["caution"] or "").replace("\n", "<br>")

                card_html = f"""
                <div class="preview-main-wrapper">
                  <div class="preview-header">
                    <span></span>
                    <span class="pattern-copy-icon" data-pattern="{idx}">
                       📋 テキストコピー
                    </span>
                  </div>

                  <div style="margin-top:4px;">
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

        # コピーJS
        st.components.v1.html(f"""
        <script>
        (function(){{
          const texts = {json.dumps(copy_texts, ensure_ascii=False)};
          function setup(){{
            const icons = parent.document.querySelectorAll('.pattern-copy-icon');
            icons.forEach(icon => {{
              icon.onclick = () => {{
                const idx = icon.getAttribute('data-pattern');
                navigator.clipboard.writeText(texts[idx] || "");
                icon.classList.remove('copy-flash');
                void icon.offsetWidth;
                icon.classList.add('copy-flash');
              }};
            }})
          }}
          setTimeout(setup, 300);
        }})();
        </script>
        """, height=0)


# ============================================
# 「生成中 → 実生成」処理（2nd ステップ）
# ============================================
if st.session_state.need_generate and st.session_state.last_user_message:

    with st.spinner("メッセージを生成しています…"):

        ai_text = generate_email_with_openai(
            template=st.session_state.pending_template,
            tone=st.session_state.pending_tone,
            recipient=st.session_state.pending_recipient,
            message=st.session_state.last_user_message,
            seasonal_text=st.session_state.pending_seasonal_text,
        )

    st.session_state.ai_suggestions = ai_text
    st.session_state.need_generate = False

    # DB保存
    if HAS_DB and ai_text:
        try:
            raw_blocks = re.split(r"(?=^##\s*パターン\s*\d+)", ai_text, flags=re.MULTILINE)
            blocks = [b.strip() for b in raw_blocks if b.strip()]
            blocks = blocks[:3]

            patterns_for_db = []
            for b in blocks
