"""CLI to send a Telegram message. Used by Node server.js on exit. Usage: python send_telegram_cli.py "message" """
import sys

def main():
    msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "No message"
    try:
        from telegram_message_sender import send_message_to_users
        import asyncio
        asyncio.run(send_message_to_users(msg))
    except Exception as e:
        print(f"Telegram send failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
