import streamlit as st
import google.generativeai as genai
import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

@st.cache_data
def load_craft_rules():
    with open(Path(__file__).parent / "data" / "craft_rules.json", "r", encoding="utf-8") as f:
        return json.load(f)

craft_rules = load_craft_rules()

def authenticity_gate(user_message: str):
    violations = []
    for craft in craft_rules:
        if craft["id"].lower() in user_message.lower() or craft["name"].lower() in user_message.lower():
            for red_line in craft["red_lines"]:
                if red_line["keyword"].lower() in user_message.lower():
                    violations.append({
                        "craft": craft["name"],
                        "warning": red_line["warning"],
                        "alternatives": craft["can_personalize"],
                        "time": craft["estimated_time"]
                    })
    return violations

st.set_page_config(page_title="LocalViet Connect", page_icon="🇻🇳")

# === SESSION STATE ===
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "agreed_terms" not in st.session_state:
    st.session_state.agreed_terms = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_terms" not in st.session_state:
    st.session_state.show_terms = False

# === TERMS PAGE ===
def terms_page():
    st.title("📋 Điều khoản sử dụng")
    st.markdown("""
    ### 1. Chấp nhận điều khoản
    Khi sử dụng LocalViet Connect, bạn đồng ý với các điều khoản sau:
    
    ### 2. Tôn trọng di sản văn hóa
    - Không yêu cầu tạo ra sản phẩm vi phạm thuần phong mỹ tục Việt Nam
    - Tôn trọng quy tắc và cảnh báo từ các nghệ nhân
    
    ### 3. Sử dụng thông tin
    - Giá cả và thời gian chế tác có thể thay đổi theo thực tế
    
    ### 4. Bảo mật
    - Email của bạn chỉ dùng để định danh, không chia sẻ cho bên thứ ba
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Tôi đồng ý", use_container_width=True):
            st.session_state.agreed_terms = True
            st.session_state.show_terms = False
            st.rerun()
    with col2:
        if st.button("❌ Từ chối", use_container_width=True):
            st.session_state.show_terms = False
            st.rerun()

# === LOGIN PAGE ===
def login_page():
    st.title("🇻🇳 LocalViet Connect")
    st.caption("Trợ lý Văn hóa & Làng nghề Việt Nam")
    st.divider()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔐 Đăng nhập")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="example@gmail.com")
            name = st.text_input("Tên hiển thị", placeholder="Nguyễn Văn A")
            
            col_a, col_b = st.columns(2)
            with col_a:
                login_btn = st.form_submit_button("🚀 Vào ngay", use_container_width=True)
            with col_b:
                terms_btn = st.form_submit_button("📋 Điều khoản", use_container_width=True)
            
            if terms_btn:
                st.session_state.show_terms = True
                st.rerun()
            
            if login_btn:
                if email and name:
                    st.session_state.logged_in = True
                    st.session_state.agreed_terms = True
                    st.session_state.user_email = email
                    st.session_state.user_name = name
                    st.rerun()
                else:
                    st.error("Vui lòng nhập đầy đủ email và tên!")

# === MAIN APP ===
def main_app():
    with st.sidebar:
        st.header(f"👤 {st.session_state.user_name}")
        st.caption(f"📧 {st.session_state.user_email}")
        st.divider()
        if st.button("🚪 Đăng xuất", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        st.divider()
        st.caption("🇻🇳 LocalViet Connect v2.0")

    st.title("🇻🇳 LocalViet Connect")
    st.caption("Trợ lý Văn hóa & Làng nghề Việt Nam | Dịch đúng 'ý' hơn đúng 'chữ'")
    st.divider()

    SYSTEM_PROMPT = """Bạn là LocalViet Connect - Trợ lý Văn hóa & Làng nghề Việt Nam.
TÍNH CÁCH: Thân thiện, gần gũi, chuyên nghiệp.
QUY TẮC:
1. Không cho phép sản phẩm vi phạm thuần phong mỹ tục.
2. Trả lời ĐÚNG ngôn ngữ người dùng hỏi.
3. Khi giải thích phương ngữ: từ gốc + nghĩa + ví dụ + tip.
4. Khi khách hỏi làm đồ thủ công: KIỂM TRA quy tắc làng nghề trước."""

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=SYSTEM_PROMPT
    )

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Hỏi tôi về văn hóa, phương ngữ, làng nghề..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        violations = authenticity_gate(prompt)
        extra_context = ""
        if violations:
            v = violations[0]
            extra_context = f"""
[QUAN TRỌNG: Người dùng yêu cầu vi phạm quy tắc làng nghề.
- Làng nghề: {v['craft']}
- Vi phạm: {v['warning']}
- Được phép: {', '.join(v['alternatives'])}
Hãy TỪ CHỐI lịch sự và đề xuất thay thế.]
"""
        full_prompt = prompt + extra_context

        with st.chat_message("assistant"):
            with st.spinner("Đang trả lời..."):
                try:
                    response = model.generate_content(full_prompt)
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"Lỗi: {str(e)}")

# === ROUTER ===
if not st.session_state.logged_in:
    if st.session_state.show_terms:
        terms_page()
    else:
        login_page()
else:
    if not st.session_state.agreed_terms:
        terms_page()
    else:
        main_app()