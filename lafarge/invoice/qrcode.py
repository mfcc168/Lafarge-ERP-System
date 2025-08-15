from io import BytesIO

import qrcode


def generate_whatsapp_qr_code(phone_number, encrypted_customer_id):
    whatsapp_url = f"https://wa.me/{phone_number}?text=Code:{encrypted_customer_id}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(whatsapp_url)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')

    img_buffer = BytesIO()
    img.save(img_buffer, format="PNG")
    img_buffer.seek(0)

    return img_buffer
