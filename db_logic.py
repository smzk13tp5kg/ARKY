import streamlit as st
from supabase import create_client,Client
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
st.title("DB入力テスト")
st.subheader("入力開始")
#初回生成時の追加
response=supabase.table("test-arky").select("id").order("id",desc=True).limit(1).execute()
max_id=response.data[0]["id"]
response=supabase.table("test-arky").select("generatedid").order("generatedid",desc=True).limit(1).execute()
max_generatedid=response.data[0]["generatedid"]
id=max_id+1
generatedid=max_generatedid+1
regeneratedid="2"
template="お礼"
tone="フォーマル"
recipient="上司"
message="資料"
subject="確認依頼"
body="明後日までに資料確認お願いします"
if st.button("入力"):
            # DBにデータを保存（ユーザーIDなし）
            supabase.table("test-arky").insert({
                "regeneratedid": regeneratedid,
                "template": template,
                "tone": tone,
                "recipient": recipient,
                "id":id,
                "message":message,
                "subject":subject,
                "body":body,
                "generatedid":generatedid
            }).execute()

            st.success("入力完了しました！")
#再生成の時の追加
response=supabase.table("test-arky").select("id").order("id",desc=True).limit(1).execute()
max_id=response.data[0]["id"]
response=supabase.table("test-arky").select("generatedid").order("generatedid",desc=True).limit(1).execute()
max_generatedid=response.data[0]["generatedid"]
regen_response=supabase.table("test-arky").select("regeneratedid").eq("generatedid",max_generatedid).order("regeneratedid",desc=True).limit(1).execute()
max_regeneratedid=regen_response.data[0]["regeneratedid"]
id=max_id+1
generatedid=max_generatedid
regeneratedid=max_regeneratedid+1
template="お礼"
tone="フォーマル"
recipient="上司"
message="資料"
subject="確認依頼"
body="明後日までに資料確認お願いします"
if st.button("再入力"):
            # DBにデータを保存（ユーザーIDなし）
            supabase.table("test-arky").insert({
                "regeneratedid": regeneratedid,
                "template": template,
                "tone": tone,
                "recipient": recipient,
                "id":id,
                "message":message,
                "subject":subject,
                "body":body,
                "generatedid":generatedid
            }).execute()

            st.success("入力完了しました！")