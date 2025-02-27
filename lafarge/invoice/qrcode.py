import qrcode
from io import BytesIO

def generate_whatsapp_qr_code(phone_number, encrypted_customer_id):
    # Create the WhatsApp URL with the phone number and encrypted customer ID
    whatsapp_url = f"https://wa.me/{phone_number}?text=Code:{encrypted_customer_id}"

    # Generate the QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(whatsapp_url)
    qr.make(fit=True)

    # Create an image from the QR code
    img = qr.make_image(fill='black', back_color='white')

    # Save the image to a BytesIO object
    img_buffer = BytesIO()
    img.save(img_buffer, format="PNG")
    img_buffer.seek(0)

    return img_buffer