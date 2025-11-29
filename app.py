import streamlit as st
from datetime import datetime
import random

# ============================================
# メール生成関数（最初に定義）
# ============================================
def generate_email(template, tone, recipient, message, variation=0):
    """メールを生成する（variation: 0=通常, 1=バリエーション1, 2=バリエーション2）"""
    
    # 件名生成（バリエーション）
    subject_variations = {
        '依頼': [
            f'【ご依頼】{message[:20]}',
            f'【お願い】{message[:20]}',
            f'{message[:20]}についてのご依頼'
        ],
        '交渉': [
            f'【ご相談】{message[:20]}',
            f'【打ち合わせ依頼】{message[:20]}',
            f'{message[:20]}に関するご相談'
        ],
        'お礼': [
            f'お礼申し上げます - {message[:15]}',
            f'感謝の気持ちをお伝えいたします - {message[:15]}',
            f'御礼 - {message[:15]}'
        ],
        '謝罪': [
            f'お詫び申し上げます - {message[:15]}',
            f'深くお詫び申し上げます - {message[:15]}',
            f'謹んでお詫び申し上げます - {message[:15]}'
        ],
        '挨拶': [
            f'ご挨拶 - {message[:20]}',
            f'ご挨拶申し上げます - {message[:20]}',
            f'{message[:20]}'
        ]
    }
    
    template_subjects = subject_variations.get(template, [f'{template} - {message[:20]}'])
    subject = template_subjects[variation % len(template_subjects)]
    
    # 挨拶文（バリエーション）
    greetings_variations = {
        '上司': ['お疲れ様です。', 'お疲れ様でございます。', 'いつもお世話になっております。'],
        '同僚': ['お疲れ様です。', 'お疲れさまです。', 'こんにちは。'],
        '部下': ['お疲れ様です。', 'お疲れ様。', 'こんにちは。'],
        '社外企業社員': ['いつもお世話になっております。', '平素より大変お世話になっております。', 'お世話になっております。'],
        '取引先': ['いつもお世話になっております。', '平素より格別のご高配を賜り、厚く御礼申し上げます。', 'お世話になっております。']
    }
    
    greeting_list = greetings_variations.get(recipient, ['お世話になっております。'])
    greeting = greeting_list[variation % len(greeting_list)]
    
    # 本文の表現バリエーション（※トーンは今は使わず、共通ロジック）
    body_variations = [
        # バリエーション0: 標準
        f"""{greeting}

{message}に関しまして、ご連絡させていただきます。

詳細につきましては、下記のとおりとなります。
ご確認いただけますと幸いです。

お忙しいところ恐れ入りますが、
""",
        # バリエーション1: 丁寧
        f"""{greeting}

{message}の件につきまして、ご連絡申し上げます。

詳細は以下のとおりでございます。
ご確認のほど、何卒よろしくお願い申し上げます。

ご多忙中誠に恐縮ではございますが、
""",
        # バリエーション2: 簡潔
        f"""{greeting}

{message}についてご連絡いたします。

下記の内容をご確認ください。

お手数をおかけいたしますが、
"""
    ]
    
    body_start = body_variations[variation % len(body_variations)]
    
    # 結びの言葉（バリエーション）
    closings_variations = {
        '上司': [
            'ご確認のほど、よろしくお願いいたします。',
            'ご査収のほど、よろしくお願い申し上げます。',
            'ご検討のほど、よろしくお願いいたします。'
        ],
        '同僚': [
            'よろしくお願いします。',
            'ご確認お願いします。',
            'よろしくね。'
        ],
        '部下': [
            'よろしくお願いします。',
            '確認しておいてください。',
            'よろしく。'
        ],
        '社外企業社員': [
            'ご検討のほど、よろしくお願い申し上げます。',
            'ご確認の上、ご返信いただけますと幸いです。',
            '何卒よろしくお願いいたします。'
        ],
        '取引先': [
            'ご検討のほど、よろしくお願い申し上げます。',
            'ご査収のほど、何卒よろしくお願い申し上げます。',
            'ご確認のほど、よろしくお願いいたします。'
        ]
    }
    
    closing_list = closings_variations.get(recipient, ['よろしくお願いいたします。'])
    closing = closing_list[variation % len(closing_list)]
    
    body = body_start + closing
    
    # アドバイス生成
    advices = {
        '依頼': '依頼メールでは、具体的な内容と期限を明記することで、相手が対応しやすくなります。簡潔で丁寧な表現を心掛けましょう。',
        '交渉': '交渉メールでは、双方にメリットがある提案を心掛けましょう。相手の立場を考慮した表現が重要です。',
        'お礼': 'お礼メールは迅速に送ることで、誠意が伝わります。具体的に何に対する感謝なのかを明記しましょう。',
        '謝罪': '謝罪メールでは、具体的な理由と今後の対策を含めることで、誠実さが伝わります。責任を明確にすることが大切です。',
        '挨拶': '挨拶メールは、簡潔で丁寧な表現を心掛けましょう。相手との関係性に応じた適切なトーンを選びましょう。'
    }
    advice = advices.get(template, 'メールは簡潔で丁寧な表現を心掛けましょう。')
    
    return {
        'subject': subject,
        'body': body,
        'advice': advice,
        'variation': variation
    }

# ============================================
# ページ設定
# ============================================
st.set_page_config(
    page_title="ビジネスメール作成アシスタント",
    page_icon="✉️",
    layout="wide"
)

# ============================================
# カスタムCSS
# ============================================
st.markdown("""
<style>
* {
    box-sizing: border-box;
}

/* 全体テーマ */
body {
    background-color: #050b23;
}

/* ページ全体の余白調整 */
main.block-container {
    padding-top: 0.5rem;
}

/* サイドバー（左） */
[data-testid="stSidebar"] {
    width: 240px !important;
    min-width: 240px !important;
    max-width: 240px !important;
    background: #050b23;
    border-right: 1px solid #29314f;
}

[data-testid="stSidebar"] > div:first-child {
    padding: 12px 8px 16px 8px;
}

/* サイドバータイトル */
.sidebar-app-title {
    font-size: 14px;
    font-weight: 600;
    color: #ffffff;
    padding: 4px 8px 10px 8px;
}

/* 新規作成ボタン（ゴールド） */
.sidebar-new-btn .stButton>button, .stSidebar .stButton>button {
    background: linear-gradient(180deg, #ffd666 0%, #f4a021 100%);
    color: #1b2433;
    border: none;
    border-radius: 999px;
    font-weight: 700;
    font-size: 14px;
    padding: 10px 16px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.25);
}
.sidebar-new-btn .stButton>button:hover, .stSidebar .stButton>button:hover {
    background: linear-gradient(180deg, #ffe58f 0%, #f0a73a 100%);
}

/* サイドバー：見出し */
.nav-label {
    font-size: 12px;
    font-weight: 600;
    color: #c3d3ff;
    margin: 4px 0 6px 4px;
}

/* サイドバー：カード */
.nav-section {
    background: #050b23;
    border-radius: 12px;
    padding: 6px 4px 10px 4px;
    margin-bottom: 12px;
    border: 1px solid #29314f;
}

/* ラジオグループ */
.nav-section div[role="radiogroup"] {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

/* ラジオの各行（pill風） */
.nav-section div[role="radiogroup"] > label {
    border-radius: 999px;
    padding: 4px 8px;
    border: 1px solid transparent;
    background: transparent;
    cursor: pointer;
}
.nav-section div[role="radiogroup"] > label:hover {
    background: rgba(255,255,255,0.06);
}
.nav-section div[role="radiogroup"] span {
    font-size: 12px;
    color: #e2e8ff;
}
st.markdown("""
<style>
/* ===== サイドバーのラジオ文字色を強制的に白／ゴールドにする ===== */

/* 通常時：白っぽい色 */
.nav-section div[role="radiogroup"] > label {
    color: #ffffff !important;  /* ここを #ffd666 にすればゴールド系 */
}

/* 選択中はゴールド寄りに（お好みで） */
.nav-section div[role="radiogroup"] input:checked ~ div {
    color: #ffd666 !important;
}
</style>
""", unsafe_allow_html=True)

/* 選択中（だいたいのターゲット。バージョンによって微調整必要） */
.nav-section div[role="radiogroup"] input:checked ~ div {
    background: rgba(255,214,102,0.1);
    border-color: #ffd666;
    color: #ffd666;
}

/* メインタイトル（中央上部） */
.top-bar {
    background: #050b23;
    padding: 16px 8px 8px 8px;
    border-bottom: 1px solid #29314f;
}
.app-title {
    font-size: 24px;
    font-weight: 700;
    color: #ffffff;
    margin: 0;
}

/* メイン領域の背景 */
section.main > div {
    background: #050b23;
}

/* セクション見出し（メッセージ／プレビュー） */
.section-header {
    font-size: 14px;
    font-weight: 700;
    color: #ffb74d;
    margin: 8px 0;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* ボックス共通（カード） */
.card {
    background: #0b1533;
    border-radius: 16px;
    border: 1px solid #3b4468;
    padding: 16px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.35);
    color: #e5ecff;
}

/* メッセージカード */
.message-card {
    max-height: 260px;
    overflow-y: auto;
    margin-bottom: 10px;
}

/* メッセージ行 */
.msg-row {
    display: flex;
    flex-direction: row;
    gap: 8px;
    align-items: flex-start;
    padding: 6px 0;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.msg-row:last-child {
    border-bottom: none;
}
.msg-icon {
    font-size: 16px;
    margin-top: 2px;
}
.msg-text-main {
    font-size: 13px;
    color: #f5f7ff;
}

/* 入力カード内のテキストエリア */
.input-card textarea {
    background: #020821;
    border-radius: 12px !important;
    border-color: #3b4468 !important;
    color: #e5ecff !important;
    font-size: 13px;
}

/* 入力カードの送信ボタン */
.input-card .stButton>button {
    background: #1a73e8;
    color: #ffffff;
    border-radius: 999px;
    border: none;
    font-weight: 600;
    padding: 6px 18px;
    font-size: 13px;
}
.input-card .stButton>button:hover {
    background: #3b82f6;
}

/* プレビューカード（件名・本文） */
.preview-card {
    background: #0b1533;
    border-radius: 16px;
    border: 1px solid #3b4468;
    padding: 12px 14px;
    color: #e5ecff;
    font-size: 13px;
}

/* プレビュー内テキストエリア */
.preview-card textarea {
    background: #020821;
    border-radius: 12px !important;
    border-color: #3b4468 !important;
    color: #e5ecff !important;
    font-size: 13px;
}

/* アドバイスカード */
.advice-box {
    background: #1b4332;
    border-left: 3px solid #95d5b2;
    border-radius: 12px;
    padding: 12px 14px;
    margin-top: 10px;
    font-size: 12px;
    color: #e9f5f0;
}

/* コピー／再生成ボタン */
.preview-actions .stButton>button {
    background: #1e40af;
    color: #ffffff;
    border-radius: 8px;
    border: none;
    font-weight: 600;
    font-size: 13px;
    padding: 6px 16px;
}
.preview-actions .stButton>button:hover {
    background: #2563eb;
}

/* コピー用テキストエリア */
.copy-area textarea {
    background: #020821;
    border-radius: 12px !important;
    border-color: #3b4468 !important;
    color: #e5ecff !important;
    font-size: 12px;
}

/* プレースホルダーメッセージ */
.preview-placeholder {
    color: #9ca3c7;
    font-size: 13px;
}

/* スクロールバー調整（メッセージカード） */
.message-card::-webkit-scrollbar {
    width: 8px;
}
.message-card::-webkit-scrollbar-track {
    background: transparent;
}
.message-card::-webkit-scrollbar-thumb {
    background: #4b5563;
    border-radius: 4px;
}
.message-card::-webkit-scrollbar-thumb:hover {
    background: #6b7280;
}
</style>
""", unsafe_allow_html=True)


# ============================================
# セッション状態の初期化
# ============================================
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'generated_email' not in st.session_state:
    st.session_state.generated_email = None
if 'variation_count' not in st.session_state:
    st.session_state.variation_count = 0

# ============================================
# タイトル
# ============================================
st.title("✉️ ビジネスメール作成アシスタント")
st.markdown("---")

# ============================================
# サイドバー（設定）
# ============================================
with st.sidebar:
    # アプリ名＋新規作成ボタン
    st.markdown('<div class="sidebar-app-title">✉️ メール生成AI</div>', unsafe_allow_html=True)
    if st.button("+ 新規作成", use_container_width=True):
        st.session_state.messages = []
        st.session_state.generated_email = None
        st.session_state.variation_count = 0
        st.rerun()

    # --- テンプレート ---
    with st.container():
        st.markdown('<div class="nav-section">', unsafe_allow_html=True)
        st.markdown('<div class="nav-label">テンプレート</div>', unsafe_allow_html=True)

        template_display = st.radio(
            "テンプレート",
            [
                "📩 依頼メール",
                "🤝 交渉メール",
                "🙏 お礼メール",
                "🙇‍♂️ 謝罪メール",
                "👋 挨拶メール",
                "✏️ その他"
            ],
            index=0,
            label_visibility="collapsed",
            key="template_radio"
        )

        st.markdown('</div>', unsafe_allow_html=True)

    display_to_template = {
        "📩 依頼メール": "依頼",
        "🤝 交渉メール": "交渉",
        "🙏 お礼メール": "お礼",
        "🙇‍♂️ 謝罪メール": "謝罪",
        "👋 挨拶メール": "挨拶",
        "✏️ その他": "その他",
    }
    template = display_to_template[template_display]

    custom_template = None
    if template == "その他":
        custom_template = st.text_input("カスタムテンプレート", placeholder="例: 報告")
        template = custom_template if custom_template else "その他"

    # --- トーン（6種類） ---
    with st.container():
        st.markdown('<div class="nav-section">', unsafe_allow_html=True)
        st.markdown('<div class="nav-label">トーン</div>', unsafe_allow_html=True)

        tone_display = st.radio(
            "トーン",
            [
                "😊 カジュアル／フレンドリー（同僚・社内フラット向け）",
                "📄 標準ビジネス（最も一般的）",
                "📘 フォーマル（社外顧客／上位者／依頼交渉）",
                "🙏 厳粛・儀礼的（謝罪・不祥事・クレーム対応）",
                "⏱️ 緊急・簡潔（即時対応が必要な通知）",
                "🌿 柔らかめ（関係維持・お礼・広報向け）"
            ],
            index=1,  # デフォルト：標準ビジネス
            label_visibility="collapsed",
            key="tone_radio"
        )

        st.markdown('</div>', unsafe_allow_html=True)

    display_to_tone = {
        "😊 カジュアル／フレンドリー（同僚・社内フラット向け）": "カジュアル／フレンドリー",
        "📄 標準ビジネス（最も一般的）": "標準ビジネス",
        "📘 フォーマル（社外顧客／上位者／依頼交渉）": "フォーマル",
        "🙏 厳粛・儀礼的（謝罪・不祥事・クレーム対応）": "厳粛・儀礼的",
        "⏱️ 緊急・簡潔（即時対応が必要な通知）": "緊急・簡潔",
        "🌿 柔らかめ（関係維持・お礼・広報向け）": "柔らかめ",
    }
    tone = display_to_tone[tone_display]

    # --- 相手 ---
    with st.container():
        st.markdown('<div class="nav-section">', unsafe_allow_html=True)
        st.markdown('<div class="nav-label">相手</div>', unsafe_allow_html=True)

        recipient_display = st.radio(
            "相手",
            [
                "👔 上司",
                "👥 同僚",
                "📋 部下",
                "🏢 社外企業社員",
                "🤝 取引先",
                "✏️ その他"
            ],
            index=0,
            label_visibility="collapsed",
            key="recipient_radio"
        )

        st.markdown('</div>', unsafe_allow_html=True)

    display_to_recipient = {
        "👔 上司": "上司",
        "👥 同僚": "同僚",
        "📋 部下": "部下",
        "🏢 社外企業社員": "社外企業社員",
        "🤝 取引先": "取引先",
        "✏️ その他": "その他",
    }
    recipient = display_to_recipient[recipient_display]

    custom_recipient = None
    if recipient == "その他":
        custom_recipient = st.text_input("カスタム相手", placeholder="例: 顧客")
        recipient = custom_recipient if custom_recipient else "その他"

    st.markdown("---")
    st.caption("© 2024 メール生成AI")

# ============================================
# メインエリア（2カラム）
# ============================================
col1, col2 = st.columns([3, 2])

# ============================================
# 左側：チャットエリア
# ============================================
with col1:
    st.subheader("💬 メッセージ")
    
    chat_container = st.container(height=400)
    
    with chat_container:
        if not st.session_state.messages:
            st.info(
                "👋 こんにちは！ビジネスメールの作成をお手伝いします。\n\n"
                "左側からメールの種類、トーン、相手を選択して、具体的な内容を入力してください。"
            )
        
        for msg in st.session_state.messages:
            if msg['role'] == 'user':
                st.chat_message("user").write(msg['content'])
            else:
                st.chat_message("assistant").write(msg['content'])
    
    # メッセージ入力
    with st.form("message_form", clear_on_submit=True):
        user_message = st.text_area(
            "メッセージを入力",
            placeholder="例：取引先に感謝を伝えるメールを作成したい",
            height=100,
            label_visibility="collapsed"
        )
        
        submitted = st.form_submit_button("✓ 送信", use_container_width=True)
        
        if submitted and user_message:
            # バリデーション
            if template == "その他" and not custom_template:
                st.error("⚠️ カスタムテンプレートを入力してください")
            elif recipient == "その他" and not custom_recipient:
                st.error("⚠️ カスタム相手を入力してください")
            else:
                # ユーザーメッセージを追加
                st.session_state.messages.append({
                    'role': 'user',
                    'content': user_message
                })
                
                # AI応答を追加（トーンは短いラベルで表示）
                response = f"{template}メールを「{tone}」なトーンで、{recipient}宛に作成しました！右側のプレビューをご覧ください。"
                st.session_state.messages.append({
                    'role': 'assistant',
                    'content': response
                })
                
                # メール生成
                st.session_state.variation_count = 0
                st.session_state.generated_email = generate_email(
                    template, tone, recipient, user_message, variation=0
                )
                
                st.rerun()

# ============================================
# 右側：プレビューエリア
# ============================================
with col2:
    st.subheader("📄 プレビュー")
    
    if st.session_state.generated_email is None:
        st.info("メールを生成すると、ここにプレビューが表示されます。")
    else:
        email = st.session_state.generated_email
        
        with st.container():
            st.markdown("**件名**")
            st.text(email['subject'])
            st.markdown("---")
            
            st.markdown("**本文**")
            st.text_area(
                "本文プレビュー",
                email['body'],
                height=300,
                label_visibility="collapsed"
            )
            st.markdown("---")
            
            st.markdown(
                f"""
                <div class="advice-box">
                    <strong>💡 アドバイス</strong><br>
                    {email['advice']}
                </div>
                """,
                unsafe_allow_html=True
            )
            
            st.markdown("")
            
            col_btn1, col_btn2 = st.columns(2)
            
            # コピー（手動コピー）
            with col_btn1:
                if st.button("📋 コピー"):
                    full_text = f"件名: {email['subject']}\n\n{email['body']}"
                    st.info("以下のテキストをコピーしてご利用ください。")
                    st.text_area("コピー用テキスト", full_text, height=150)
            
            # 再生成
            with col_btn2:
                if st.button("🔄 再生成"):
                    # 再生成しています... メッセージ
                    st.session_state.messages.append({
                        'role': 'assistant',
                        'content': 'メールを再生成しています...'
                    })
                    
                    # 直近の user メッセージを後ろから探す
                    last_user_message = None
                    for msg in reversed(st.session_state.messages):
                        if msg['role'] == 'user':
                            last_user_message = msg['content']
                            break
                    
                    if last_user_message:
                        st.session_state.variation_count += 1
                        st.session_state.generated_email = generate_email(
                            template,
                            tone,
                            recipient,
                            last_user_message,
                            variation=st.session_state.variation_count
                        )
                        
                        # 完了メッセージ
                        st.session_state.messages.append({
                            'role': 'assistant',
                            'content': f'新しいバージョン（バリエーション {st.session_state.variation_count + 1}）を生成しました！プレビューをご確認ください。'
                        })
                    
                    st.rerun()


