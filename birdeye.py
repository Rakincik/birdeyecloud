import streamlit as st
import tweepy
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import openai
import os

# Tema seçimi
theme = st.sidebar.radio("🎨 Tema Seçimi", ["Light Mode", "Dark Mode"])

if theme == "Dark Mode":
    st.markdown("""
    <style>
    body { background-color: #0E1117; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #161A23; }
    h1 { color: #61dafb; }
    hr { border-color: #333; }
    .stTextInput > div > div > input {
        background-color: #222;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    h1 { color: #1a73e8; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
<h1 style='text-align: center;'>🦅 <strong>BirdEye</strong></h1>
<p style='text-align: center; font-size:18px;'>Twitter profillerini analiz et, kelimeleri bulutla, GPT ile özetle!</p>
<hr style='margin-top:10px;'>
""", unsafe_allow_html=True)

api_key = st.secrets["API_KEY"]
api_secret = st.secrets["API_SECRET"]
bearer_token = st.secrets["BEARER_TOKEN"]
openai_api_key = st.secrets["OPENAI_API_KEY"]

st.sidebar.markdown("### 🔍 Twitter Kullanıcısı")
username = st.sidebar.text_input("Kullanıcı adı (@ olmadan):", placeholder="örnek: elonmusk")

if username:
    try:
        client = tweepy.Client(bearer_token=bearer_token)
        user = client.get_user(username=username, user_fields=["description", "location", "created_at", "public_metrics", "url", "verified"])
        user_data = user.data

        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("## 👤 Profil Bilgileri")
            st.success(f"**@{user_data.username}**")
            st.write(f"**Ad:** {user_data.name}")
            st.write(f"**Açıklama:** {user_data.description or 'Yok'}")
            st.write(f"**Konum:** {user_data.location or 'Bilinmiyor'}")
            st.write(f"**Web:** {user_data.url or 'Yok'}")
            st.write(f"**Doğrulama:** {'✔️' if user_data.verified else '❌'}")
            st.write(f"**Takipçi:** {user_data.public_metrics['followers_count']}")
            st.write(f"**Takip edilen:** {user_data.public_metrics['following_count']}")
            st.write(f"**Tweet Sayısı:** {user_data.public_metrics['tweet_count']}")

        tweets = client.get_users_tweets(user_data.id, max_results=20, tweet_fields=["text"])
        text_all = " ".join([tweet.text for tweet in tweets.data]) if tweets.data else ""

        with col2:
            if text_all:
                st.markdown("## ☁️ Kelime Bulutu")
                wordcloud = WordCloud(width=800, height=400, background_color='black' if theme == "Dark Mode" else 'white', colormap='plasma', collocations=False).generate(text_all)
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis("off")
                st.pyplot(fig)
            else:
                st.info("Bu kullanıcının analiz edilecek tweet verisi yok.")

        if openai_api_key:
            st.markdown("## 🤖 GPT Destekli Özet")
            openai.api_key = openai_api_key
            os.environ["OPENAI_API_KEY"] = openai_api_key

            bio = user_data.description or ""
            location = user_data.location or "Bilinmiyor"
            followers = user_data.public_metrics['followers_count']
            verified = "Evet" if user_data.verified else "Hayır"

            prompt = f"""
Aşağıdaki Twitter profil bilgilerine dayanarak kullanıcının kim olduğu, neyle ilgilendiği, kişisel mi yoksa profesyonel mi olduğu hakkında bir özet yaz:

- Kullanıcı adı: @{user_data.username}
- Bio: {bio}
- Konum: {location}
- Takipçi: {followers}
- Doğrulama: {verified}
- Tweetlerden örnekler: {text_all[:1000]}...
"""

            from openai import OpenAI
            client_ai = OpenAI()

            with st.spinner("GPT'den özet alınıyor..."):
                try:
                    response = client_ai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Sen sosyal medya profili analiz uzmanısın."},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    gpt_summary = response.choices[0].message.content
                    st.success("📌 Özet:")
                    st.info(gpt_summary)
                except Exception as e:
                    st.error(f"GPT özeti alınırken hata: {e}")

    except Exception as e:
        st.error(f"Hata oluştu: {e}")
