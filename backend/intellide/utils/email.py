from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from intellide.config import SMTP_USER, SMTP_SERVER, SMTP_PORT, SMTP_PASSWORD


async def email_send_register_code(
        recipient: str,
        code: str,
) -> bool:
    """
    异步发送验证码邮件

    Args:
        recipient: 收件人邮箱地址
        code: 验证码
    
    Returns:
        bool: 发送成功返回True，否则返回False
    """
    try:
        # 创建邮件内容
        message = MIMEMultipart()
        message['From'] = SMTP_USER
        message['To'] = recipient
        message['Subject'] = 'Intellide验证码'
        # 邮件正文
        body = f"""
        <html>
        <body>
            <h2>Intellide验证码</h2>
            <p>您的验证码是: <strong>{code}</strong></p>
            <p>验证码有效期为5分钟，请勿将验证码泄露给他人。</p>
            <p>如果这不是您的操作，请忽略此邮件。</p>
        </body>
        </html>
        """
        # 添加HTML内容
        message.attach(MIMEText(body, 'html'))
        # 使用async with自动处理连接的关闭
        async with aiosmtplib.SMTP(hostname=SMTP_SERVER, port=SMTP_PORT, use_tls=True) as smtp:
            await smtp.login(SMTP_USER, SMTP_PASSWORD)
            await smtp.send_message(message)
        return True
    except:
        return False
