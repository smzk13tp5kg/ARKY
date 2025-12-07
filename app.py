import streamlit as st
from datetime import datetime
import html
import textwrap
import json
import re

# ============================================
# ページ設定
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
except ImportError:
    HAS_DB = False


# ============================================
# 時候の挨拶
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
# パターンブロック解析
# ============================================
def parse_pattern_block(block: str) -> dict:
    """
    openai_logic から返ってきた 1 パターン分の Markdown テキストから、
    件名／本文／改善点／注意点 をざっくり抽出する。
    """
    block = re.sub(r"^##\s*パターン[^\n]*\n?", "", block, count=1, flags=re.MULTILINE)

    subject = ""
    body = ""
    improve = ""
    caution = ""

    m = re.search(r"件名[:：]\s*(.+)", block)
    if m:
        subject = m.group(1).strip()

    pos_body_label = block.find("本文:")
    rest = block[pos_body_label + len("本文:") :] if pos_body_label != -1 else block

    idx_improve = rest.find("- 改善点")
    if idx_improve != -1:
        body = rest[:idx_improve].strip()
        rest2 = rest[idx_improve:]
    else:
        body = rest.strip()
        rest2 = ""

    if rest2:
        if "- 注意点" in rest2:
            split_pos = rest2.find("- 注意点")
            improve_block = rest2[:split_pos].strip()
            caution_block = rest2[split_pos:].strip()
        else:
            improve_block = rest2.strip()
            caution_block = ""
    else:
        improve_block = ""
        caution_block = ""

    improve = re.sub(r"^-+\s*改善点[:：]?\s*", "", improve_block, flags=re.MULTILINE).strip()
    caution = re.sub(r"^-+\s*注意点[:：]?\s*", "", caution_block, flags=re.MULTILINE).strip()

    return {
        "subject": subject,
        "body": body,
        "improve": improve,
        "caution": caution,
    }


# ============================================
# メール生成（テンプレベース）
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
        "提案": [
            f"【ご提案】{message[:20]}",
            f"{message[:20]}に関するご提案",
            f"ご提案の件：{message[:20]}",
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
        "提案": "提案メールでは、双方にメリットがある提案を心掛けましょう。相手の立場を考慮した表現が重要です。",
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
# CSS（あなたの最新CSSをそのまま貼る想定）
# ============================================
# ※ ここでは省略します。実際には、あなたが最後に貼ってくれた
#    大きな <style> ブロックをそのまま st.markdown に入れてください。


# ============================================
# JS：ボタンに data-text を付与
# （省略したくなければ前と同じ）
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
# セッション状態
# ============================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_user_message" not in st.session_state:
    st.session_state.last_user_message = ""
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
            "✉️ 提案メール",
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
        "✉️ 提案メール": "提案",
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
            "📘 フォーマル（社外／上位者／依頼交渉）",
            "🙏 厳粛・儀礼的（謝罪・クレーム対応）",
            "⏱️ 緊急・簡潔（即時対応が必要な通知）",
            "🌿 ソフト（関係維持・お礼・勧誘・広報）",
        ],
        index=1,
        label_visibility="collapsed",
        key="tone_radio",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    display_to_tone = {
        "😊 カジュアル／フレンドリー（同僚向け）": "カジュアル／フレンドリー",
        "📄 標準ビジネス（最も一般的）": "標準ビジネス",
        "📘 フォーマル（社外／上位者／依頼交渉）": "フォーマル",
        "🙏 厳粛・儀礼的（謝罪・クレーム対応）": "厳粛・儀礼的",
        "⏱️ 緊急・簡潔（即時対応が必要な通知）": "緊急・簡潔",
        "🌿 ソフト（関係維持・お礼・勧誘・広報）": "柔らめ",
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
col1, col2 = st.columns([1, 1], gap="medium")

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
              左側からテンプレートやトーン、相手、時候の挨拶の有無を選び、
              下の入力欄にやりたいことを入力したら送信してください。
            </span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

    # 送信処理
    if submitted and user_message:
        if template == "その他" and not custom_template:
            st.error("⚠️ カスタムテンプレートを入力してください")
        elif recipient == "その他" and not custom_recipient:
            st.error("⚠️ カスタム相手を入力してください")
        else:
            st.session_state.last_user_message = user_message

            # チャットログ更新
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

            # 生成中表示
            with st.spinner("メッセージを生成しています…"):
                ai_text = generate_email_with_openai(
                    template=template,
                    tone=tone,
                    recipient=recipient,
                    message=user_message,
                    seasonal_text=seasonal_text,
                )

            st.session_state.ai_suggestions = ai_text

            # DB保存
            if HAS_DB and ai_text:
                try:
                    raw_blocks = re.split(r"(?=^##\s*パターン\s*\d+)", ai_text, flags=re.MULTILINE)
                    blocks = [b.strip() for b in raw_blocks if b.strip()]
                    blocks = blocks[:3]
                    while len(blocks) < 3:
                        blocks.append("このパターンはまだ生成されていません。")

                    patterns_for_db = []
                    for b in blocks:
                        parsed = parse_pattern_block(b)
                        patterns_for_db.append(
                            {"subject": parsed.get("subject", ""), "body": parsed.get("body", "")}
                        )

                    save_email_batch(
                        template=template,
                        tone=tone,
                        recipient=recipient,
                        message=user_message,
                        seasonal_greeting=add_seasonal,
                        patterns=patterns_for_db,
                    )
                except Exception as e:
                    st.error(f"❌ DB保存エラー: {str(e)}")

            if len(st.session_state.messages) > 50:
                st.session_state.messages = st.session_state.messages[-50:]

            st.experimental_rerun()

    elif reset_clicked:
        st.session_state.messages = []
        st.session_state.last_user_message = ""
        st.session_state.ai_suggestions = None
        st.experimental_rerun()

    # チャットログ表示
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    chat_html_parts = ["<div class='chat-log'>"]
    for msg in st.session_state.messages:
        role = msg["role"]
        text = html.escape(msg["content"]).replace("\n", "<br>")
        if role == "user":
            chat_html_parts.append(f"<div class='chat-bubble user'>{text}</div>")
        else:
            chat_html_parts.append(
                f"<div class='chat-bubble assistant'><span>{text}</span></div>"
            )
    chat_html_parts.append("</div>")
    st.markdown("\n".join(chat_html_parts), unsafe_allow_html=True)

# --------------------------------------------
# 右：プレビューエリア
# --------------------------------------------
with col2:
    ai_text = st.session_state.ai_suggestions

    if not ai_text:
        # 初期／リセット直後：案内文
        placeholder_html = textwrap.dedent(
            """
            <div class="preview-main-wrapper">
              <div class="preview-header"><span></span></div>
              <div style="margin-top:8px;">
                <p style="font-size:14px; color:#4b5563; margin:0;">
                  送信ボタンをクリックすると、ここにAIが生成したメッセージが表示されます。
                </p>
              </div>
            </div>
            """
        )
        st.markdown(placeholder_html, unsafe_allow_html=True)

    else:
        # タブ表示
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
                    <span class="pattern-copy-icon"
                          data-pattern="{idx}"
                          title="メッセージをコピーします">
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
        texts_json = json.dumps(copy_texts, ensure_ascii=False)
        st.components.v1.html(
            f"""
            <script>
            (function() {{
              const texts = {texts_json};
              function setup() {{
                const icons = parent.document.querySelectorAll('.pattern-copy-icon');
                if (!icons || icons.length === 0) return;
                icons.forEach(icon => {{
                  icon.addEventListener('click', () => {{
                    const idx = icon.getAttribute('data-pattern');
                    const text = texts[idx] || "";
                    if (navigator.clipboard && navigator.clipboard.writeText) {{
                      navigator.clipboard.writeText(text);
                    }}
                    icon.classList.remove('copy-flash');
                    void icon.offsetWidth;
                    icon.classList.add('copy-flash');
                  }});
                }});
              }}
              setTimeout(setup, 500);
            }})();
            </script>
            """,
            height=0,
        )
