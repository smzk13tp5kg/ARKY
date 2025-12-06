import streamlit as st
from datetime import datetime
import html
import textwrap
import json

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
# メール生成関数（従来ロジック）
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
# カスタムCSS（あなたのコードをそのまま利用）
# ============================================
st.markdown(
    """
<style>
* { box-sizing: border-box; }
/* ……（ここはあなたのCSSそのままなので省略せず貼ってOK） …… */
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
if "pattern_variations" not in st.session_state:
    st.session_state.pattern_variations = [0, 0, 0]  # 3パターン分
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
# 左：メッセージ＋フォーム＋チャットログ
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
                # ベースメッセージを保存
                st.session_state.last_user_message = user_message
                # 各パターンの variation 初期化
                st.session_state.pattern_variations = [0, 1, 2]

                # チャットログに選択内容付きで記録
                user_display_text = (
                    f"{user_message}\n\n"
                    f"――――――――――\n"
                    f"テンプレート: {template} / トーン: {tone} / 相手: {recipient}"
                )
                st.session_state.messages.append({"role": "user", "content": user_display_text})

                guide = (
                    f"{template}メールを「{tone}」なトーンで、"
                    f"{recipient}宛に3パターン生成しました！右側のプレビューをご覧ください。"
                )
                st.session_state.messages.append({"role": "assistant", "content": guide})

                # OpenAI案（3パターン解説）を生成
                st.session_state.ai_suggestions = generate_email_with_openai(
                    template=template,
                    tone=tone,
                    recipient=recipient,
                    message=user_message,
                    seasonal_text=seasonal_text,
                )

                # DB保存（あれば）
                if HAS_DB:
                    try:
                        base_email = generate_email(
                            template,
                            tone,
                            recipient,
                            user_message,
                            variation=0,
                            seasonal_text=seasonal_text,
                        )
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

                # メモリ対策：チャット履歴を最大50件に制限
                if len(st.session_state.messages) > 50:
                    st.session_state.messages = st.session_state.messages[-50:]

                st.rerun()

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # チャットログ表示
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
# 右：プレビュー（3パターン）
# --------------------------------------------
with col2:
    st.markdown(
        "<div class='section-header'>📄 プレビュー（3パターン）</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    if not st.session_state.last_user_message:
        placeholder_html = textwrap.dedent(
            """
            <div class="preview-main-wrapper">
                <p><em>メールを生成すると、ここに3パターンのプレビューが表示されます。</em></p>
            </div>
            """
        )
        st.markdown(placeholder_html, unsafe_allow_html=True)
    else:
        # 3パターン分ループ
        for idx in range(3):
            variation = st.session_state.pattern_variations[idx]
            email = generate_email(
                template,
                tone,
                recipient,
                st.session_state.last_user_message,
                variation=variation,
                seasonal_text=seasonal_text,
            )

            st.markdown(
                f"<div class='section-header'>◆ パターン {idx+1}</div>",
                unsafe_allow_html=True,
            )

            body_html = html.escape(email["body"]).replace("\n", "<br>")
            subject_html = html.escape(email["subject"])

            preview_html = textwrap.dedent(
                f"""
                <div class="preview-main-wrapper">
                    <p class="preview-label"><strong>件名</strong></p>
                    <p class="preview-subject">{subject_html}</p>
                    <hr>
                    <p class="preview-label"><strong>本文</strong></p>
                    <p class="preview-body">{body_html}</p>
                </div>
                """
            )
            st.markdown(preview_html, unsafe_allow_html=True)

            # コピー用テキスト
            full_text = f"件名: {email['subject']}\n\n{email['body']}"
            escaped_full_text = json.dumps(full_text)

            btn_col1, btn_col2, btn_col3 = st.columns(3)

            # 📋 コピー
            with btn_col1:
                if st.button("📋 コピー", key=f"copy_{idx}", use_container_width=True):
                    st.components.v1.html(
                        f"""
                        <script>
                        (function() {{
                          const text = {escaped_full_text};
                          function copyText(t) {{
                              if (navigator.clipboard && navigator.clipboard.writeText) {{
                                  navigator.clipboard.writeText(t).catch(function(err) {{
                                      console.warn("navigator.clipboard failed:", err);
                                  }});
                              }} else {{
                                  const textarea = document.createElement('textarea');
                                  textarea.value = t;
                                  textarea.style.position = 'fixed';
                                  textarea.style.left = '-9999px';
                                  document.body.appendChild(textarea);
                                  textarea.focus();
                                  textarea.select();
                                  document.execCommand('copy');
                                  document.body.removeChild(textarea);
                              }}
                          }}
                          copyText(text);
                        }})();
                        </script>
                        """,
                        height=0,
                    )
                    st.success(f"パターン{idx+1}をコピーしました")

            # 🔄 リセット（全体リセット）
            with btn_col2:
                if st.button("リセット", key=f"reset_{idx}", use_container_width=True):
                    st.session_state.messages = []
                    st.session_state.last_user_message = ""
                    st.session_state.pattern_variations = [0, 0, 0]
                    st.session_state.ai_suggestions = None
                    st.rerun()

            # 🎲 表現を変える（このパターンだけ）
            with btn_col3:
                if st.button("🔄 表現を変える", key=f"regen_{idx}", use_container_width=True):
                    st.session_state.pattern_variations[idx] += 1
                    st.rerun()

            st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # ↓ OpenAI案（3パターン解説）は、カードの下にまとめて表示
        if st.session_state.ai_suggestions:
            st.markdown("### 🤖 OpenAI案（3パターン解説）")
            st.markdown(st.session_state.ai_suggestions)
