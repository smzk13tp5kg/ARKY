import streamlit as st

# ============================================
# メール生成関数
# ============================================
def generate_email(template, tone, recipient, message, variation=0):
    """メールを生成する（variation: 0=通常, 1=バリエーション1, 2=バリエーション2）"""
    
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

    greetings_variations = {
    '上司': [
        'お疲れ様です。',
        'お疲れ様でございます。',
        'いつもお世話になっております。'
    ],
    '同僚': [
        'お疲れ様です。',
        'お疲れさまです。',
        'こんにちは。'
    ],
    '部下': [
        'お疲れ様です。',
        'お疲れ様。',
        'こんにちは。'
    ],
    '社外企業社員': [
        'いつもお世話になっております。',
        '平素より大変お世話になっております。',
        'お世話になっております。'
    ],
    '取引先': [
        'いつもお世話になっております。',
        '平素より格別のご高配を賜り、厚く御礼申し上げます。',
        'お世話になっております。'
    ]
}


