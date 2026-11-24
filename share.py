"""
share.py : 앱 공유 (QR 코드) 화면

[이 화면은 어떤 과정이야?]
1) qrcode 라이브러리로 앱 주소를 QR 코드 그림으로 바꾼다.
2) 화면에 크게 띄워서, 발표할 때 친구들이 휴대폰 카메라로 찍고 바로 접속하게 한다.
3) QR 그림을 파일로 내려받아 포스터나 피치덱에 넣을 수도 있다.
"""

import io

import qrcode
import streamlit as st

APP_URL = "https://kicklog.streamlit.app"  # 앱 주소가 바뀌면 여기만 고치면 된다

st.title("📱 킥로그 공유하기")
st.caption("휴대폰 카메라로 찍으면 바로 들어올 수 있어요")

# QR 코드 만들기: box_size는 칸 하나의 크기, border는 바깥 여백
qr = qrcode.QRCode(box_size=12, border=2)
qr.add_data(APP_URL)
qr.make(fit=True)
img = qr.make_image(fill_color="#0f5132", back_color="white")

buf = io.BytesIO()
img.save(buf, format="PNG")
png = buf.getvalue()

left, mid, right = st.columns([1, 3, 1])
mid.image(png, width="stretch")

st.markdown(f"<h3 style='text-align:center;'>{APP_URL.replace('https://', '')}</h3>",
            unsafe_allow_html=True)
st.code(APP_URL, language=None)  # 오른쪽 위 복사 버튼으로 주소를 복사할 수 있다

st.download_button("QR 코드 그림 받기 (PNG)", data=png, file_name="kicklog_qr.png",
                   mime="image/png", width="stretch")
