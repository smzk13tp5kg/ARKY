import streamlit as st
from datetime import datetime
import random

# クリップボード操作（ローカル専用扱い）
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

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
    
    # 本文の表現バリエーション
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
    .main {
        background-color: #f5f7fa;
    }
    .stButton>button {
        width: 100%;
        background-color: #1a73e8;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 12px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #1557b0;
    }
    .advice-box {
        background-color: #e8f5e9;
        border-left: 3px solid #4caf50;
        padding: 15px;
        border-radius: 4px;
        margin-top: 15px;
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
    st.header("⚙️ メール設定")
    
    # 新規作成ボタン
    if st.button("➕ 新規作成"):
        st.session_state.messages = []
        st.session_state.generated_email = None
        st.session_state.variation_count = 0
        st.rerun()
    
    st.markdown("---")
    
    # テンプレート選択
    st.subheader("📧 テンプレート")
    template_options = ["依頼", "交渉", "お礼", "謝罪", "挨拶", "その他"]
    template = st.selectbox(
        "メールの種類",
        template_options,
        label_visibility="collapsed"
    )
    
    custom_template = None
    if template == "その他":
        custom_template = st.text_input("カスタムテンプレート", placeholder="例: 報告")
        template = custom_template if custom_template else "その他"
    
    st.markdown("---")
    
    # トーン選択
    st.subheader("🎨 トーン")
    tone_options = ["下書", "カジュアル", "フォーマル"]
    tone = st.selectbox(
        "文体のトーン",
        tone_options,
        index=2,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # 相手選択
    st.subheader("👤 相手")
    recipient_options = ["上司", "同僚", "部下", "社外企業社員", "取引先", "その他"]
    recipient = st.selectbox(
        "送信先",
        recipient_options,
        label_visibility="collapsed"
    )
    
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
    
    # チャット履歴表示
    chat_container = st.container(height=400)
    
    with chat_container:
        if not st.session_state.messages:
            st.info("👋 こんにちは！ビジネスメールの作成をお手伝いします。\n\n左側からメールの種類、トーン、相手を選択して、具体的な内容を入力してください。")
        
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
                
                # AI応答を追加
                response = f"{template}メールを{tone}なトーンで、{recipient}宛に作成しました！右側のプレビューをご覧ください。"
                st.session_state.messages.append({
                    'role': 'assistant',
                    'content': response
                })
                
                # メール生成
                st.session_state.variation_count = 0  # 新規メッセージなので0にリセット
                st.session_state.generated_email = generate_email(
                    template, tone, recipient, user_message, variation=0
                )
                
                st.rerun()

# ============================================
# 右側：プレビューエリア
# ============================================
with col2:
    st.subheader("📄 プレビュー")
    
    if st.session_state.generated_email:
        email = st.session_state.generated_email
        
        # プレビューボックス
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
            
            # アドバイス
            st.markdown(f"""
            <div class="advice-box">
                <strong>💡 アドバイス</strong><br>
                {email['advice']}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("")
            
            # ボタン
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("📋 コピー"):
                    full_text = f"件名: {email['subject']}\n\n{email['body']}"
                    if PYPERCLIP_AVAILABLE:
                        # ローカルなど pyperclip が使える環境向け
                        pyperclip.copy(full_text)
                        st.success("✓ クリップボードにコピーしました！")
                    else:
                        # Web版など pyperclip が使えない環境向け
                        st.info("この環境では自動コピーが使えません。以下のテキストを手動でコピーしてください。")
                        st.text_area("以下をコピーしてください:", full_text, height=150)
            
            with col_btn2:
                if st.button("🔄 再生成"):
                    if len(st.session_state.messages) >= 2:
                        # 「再生成しています...」メッセージを追加
                        st.session_state.messages.append({
                            'role': 'assistant',
                            'content': 'メールを再生成しています...'
                        })
                        
                        # 直近のユーザーメッセージ（簡易版：今の仕様前提で -3 を使用）
                        last_user_message = st.session_state.messages[-3]['content']
                        
                        # バリエーションカウントを増やして別の表現を生成
                        st.session_state.variation_count += 1
                        st.session_state.generated_email = generate_email(
                            template, tone, recipient, last_user_message, 
                            variation=st.session_state.variation_count
                        )
                        
                        # 「生成完了」メッセージを追加
                        st.session_state.messages.append({
                            'role': 'assistant',
                            'content': f'新しいバージョン（バリエーション {st.session_state.variation_count + 1}）を生成しました！プレビューをご確認ください。'
                        })
                        
                        st.rerun()
    else:
        st.info("メールを生成すると、ここにプレビューが表示されます。")
