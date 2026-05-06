import streamlit as st
from groq import Groq
from datetime import datetime
import json, base64
from io import BytesIO
import requests
from huggingface_hub import InferenceClient

# =========================
# 🔑 API KEYS (SET HERE)
# =========================
GROQ_API_KEY = "xxx"  # Replace with your Groq API key
HF_API_KEY = "xxx"    # Replace with your Hugging Face API key

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Multi AI Tool PRO", layout="wide")

groq_client = Groq(api_key=GROQ_API_KEY)
hf_client = InferenceClient(api_key=HF_API_KEY)

MODEL_ID = "stabilityai/stable-diffusion-3-medium-diffusers"
FILTER_API_URL = "https://filters-zeta.vercel.app/api/filter"
NEGATIVE = "low quality, blurry, distorted, watermark, text"

# =========================
# SESSION STATE
# =========================
if "history" not in st.session_state:
    st.session_state.history = {"assistant": [], "math": [], "image": []}

# =========================
# SIDEBAR
# =========================
st.sidebar.title("⚡ Multi AI Tool")

tool = st.sidebar.radio(
    "Select Tool",
    ["AI Teaching Assistant", "Math Mastermind", "AI Image Generator"]
)

if st.sidebar.button("🗑 Clear History"):
    st.session_state.history = {"assistant": [], "math": [], "image": []}

# =========================
# EXPORT FUNCTION
# =========================
def export_history(data, filename):
    b64 = base64.b64encode(json.dumps(data, indent=2).encode()).decode()
    return f'<a href="data:file/json;base64,{b64}" download="{filename}">📥 Download</a>'

# =========================
# GROQ FUNCTION
# =========================
def ask_groq(prompt, system, model):
    res = groq_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]
    )
    return res.choices[0].message.content

# =========================
# IMAGE FUNCTIONS
# =========================
def check_prompt(prompt):
    try:
        r = requests.post(FILTER_API_URL, json={"prompt": prompt}, timeout=10)
        return r.json()
    except:
        return {"ok": True}

def enhance_prompt(prompt):
    return ask_groq(
        prompt,
        "Enhance this into a detailed cinematic image prompt with lighting, style, colors, camera angle.",
        model="llama-3.1-8b-instant"
    )

def generate_image(prompt):
    return hf_client.text_to_image(
        prompt=prompt,
        negative_prompt=NEGATIVE,
        model=MODEL_ID
    )

# =========================
# TOOL 1: AI TEACHING ASSISTANT
# =========================
if tool == "AI Teaching Assistant":
    st.title("🧠 AI Teaching Assistant")

    q = st.text_area("Ask anything:")

    if st.button("Ask"):
        if q:
            with st.spinner("Thinking..."):
                res = ask_groq(
                    q,
                    "You are a helpful AI teacher. Explain clearly with examples.",
                    model="llama-3.1-8b-instant"
                )

            st.write(res)

            st.session_state.history["assistant"].append({
                "q": q, "a": res, "time": str(datetime.now())
            })

    st.subheader("📜 History")
    for h in reversed(st.session_state.history["assistant"]):
        st.markdown(f"**Q:** {h['q']}")
        st.markdown(f"**A:** {h['a']}")
        st.markdown("---")

    st.markdown(export_history(st.session_state.history["assistant"], "assistant.json"), unsafe_allow_html=True)

# =========================
# TOOL 2: MATH MASTERMIND
# =========================
elif tool == "Math Mastermind":
    st.title("➗ Math Mastermind")

    q = st.text_area("Enter math problem:")

    if st.button("Solve"):
        if q:
            with st.spinner("Solving step by step..."):
                res = ask_groq(
                    q,
                    "You are a math expert. Solve step-by-step clearly with explanation.",
                    model="llama-3.3-70b-versatile"
                )

            st.write(res)

            st.session_state.history["math"].append({
                "q": q, "a": res, "time": str(datetime.now())
            })

    st.subheader("📜 History")
    for h in reversed(st.session_state.history["math"]):
        st.markdown(f"**Problem:** {h['q']}")
        st.markdown(f"**Solution:** {h['a']}")
        st.markdown("---")

    st.markdown(export_history(st.session_state.history["math"], "math.json"), unsafe_allow_html=True)

# =========================
# TOOL 3: AI IMAGE GENERATOR (REAL)
# =========================
elif tool == "AI Image Generator":
    st.title("🎨 AI Image Generator")

    prompt = st.text_area("Describe your image:")

    if st.button("Generate Image"):
        if prompt:
            check = check_prompt(prompt)

            if not check.get("ok", True):
                st.error("⚠️ Prompt blocked by safety filter")
            else:
                with st.spinner("Enhancing prompt..."):
                    final_prompt = enhance_prompt(prompt)

                st.markdown("### ✨ Enhanced Prompt")
                st.code(final_prompt)

                with st.spinner("Generating image..."):
                    try:
                        img = generate_image(final_prompt)

                        st.image(img, caption="Generated Image")

                        # Save history
                        st.session_state.history["image"].append({
                            "prompt": prompt,
                            "enhanced": final_prompt,
                            "time": str(datetime.now())
                        })

                        # Download
                        buf = BytesIO()
                        img.save(buf, format="PNG")

                        st.download_button(
                            "📥 Download Image",
                            buf.getvalue(),
                            "ai_image.png",
                            "image/png"
                        )

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

    st.subheader("📜 History")
    for h in reversed(st.session_state.history["image"]):
        st.markdown(f"**Prompt:** {h['prompt']}")
        st.markdown(f"**Enhanced:** {h['enhanced']}")
        st.markdown("---")

    st.markdown(export_history(st.session_state.history["image"], "image.json"), unsafe_allow_html=True)