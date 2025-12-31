"""Two-Factor Authentication Utilities"""
import pyotp
import qrcode
from io import BytesIO
import base64
import secrets

def generate_secret_key():
    """Generate a random secret key for TOTP"""
    return pyotp.random_base32()

def generate_totp_uri(user, secret_key):
    """Generate TOTP URI for QR code"""
    return pyotp.totp.TOTP(secret_key).provisioning_uri(
        name=user.username,
        issuer_name='ICGVWA Portal'
    )

def generate_qr_code(uri):
    """Generate QR code image from URI"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def verify_totp_code(secret_key, code):
    """Verify TOTP code"""
    totp = pyotp.TOTP(secret_key)
    return totp.verify(code, valid_window=1)

def generate_backup_codes(count=10):
    """Generate backup recovery codes"""
    return [secrets.token_hex(4).upper() for _ in range(count)]

def verify_backup_code(backup_codes, code):
    """Verify and remove used backup code"""
    code = code.upper().replace('-', '').replace(' ', '')
    if code in backup_codes:
        backup_codes.remove(code)
        return True
    return False
