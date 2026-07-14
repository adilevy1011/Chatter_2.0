import resend

def send_reset_email(target_email, username, token):
    try:
        # Construct the live link pointing to your new custom domain
        reset_link = f"https://chatter-2.com/reset-password.html?token={token}"
        
        print(f"[RESEND] Sending transactional recovery routing to {target_email}")
        resend.Emails.send({
            "from": "Chatter App <security@chatter-2.com>", 
            "to": target_email,
            "subject": "Reset Your Chatter Password",
            "html": f"""
                <p>Hello {username},</p>
                <p>We received a request to reset your password for your Chatter account.</p>
                <p>Click the link below to set a new password. This link expires in 1 hour:</p>
                <p><a href="{reset_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">Reset Password</a></p>
                <p>If you did not request this, please ignore this email.</p>
            """
        })
        return True
    except Exception as e:
        print(f"[RESEND ERROR] Failed to deliver recovery outbound envelope: {e}")
        return False

