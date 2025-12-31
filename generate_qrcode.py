import qrcode

# 网站地址
url = ""

# 生成二维码
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)
qr.add_data(url)
qr.make(fit=True)

# 创建图片
img = qr.make_image(fill_color="black", back_color="white")

# 保存图片
img.save("website_qrcode.png")
print("二维码已生成: website_qrcode.png")
