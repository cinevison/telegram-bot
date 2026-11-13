from datetime import datetime, timedelta, timezone
import logging
import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# ==================== [ কনফিগারেশন ] ====================
TOKEN = "9000903496:AAHF2wHsxrdr06p8tD1Y19BFa12AuDNZOvY"
ADMIN_ID = 6813663734

# একাধিক চ্যানেলের কনফিগারেশন ডিকশনারি
CHANNELS = {
    "cat1": {
        "name": "Channel 1 (mooi moyee)",
        "chat_id": -1004456149199,
        "price": "10 টাকা",
        "number": "01639238799"
    },
    "cat2": {
        "name": "Channel 2 (Habitual Desire)",
        "chat_id":-1004465424125,  # দ্বিতীয় চ্যানেলের আইডি দিন
        "price": "20 টাকা",
        "number": "01639238799"
    }
}
# ========================================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# রেন্ডারের জন্য ফ্লাস্ক সার্ভার সেটআপ
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Multi-Channel Telegram Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app_flask.run(host='0.0.0.0', port=port)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [
        [InlineKeyboardButton(f"{info['name']} - {info['price']}", callback_data=f"select_{key}")]
        for key, info in CHANNELS.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🌟 প্রিমিয়াম চ্যানেলে স্বাগতম! 🌟\n\nনিচ থেকে আপনার পছন্দের প্যাকেজটি সিলেক্ট করুন:",
        reply_markup=reply_markup
    )

async def select_channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    channel_key = query.data.split("_")[1]
    
    if channel_key not in CHANNELS:
        await query.edit_message_text("❌ ভুল প্যাকেজ সিলেক্ট করা হয়েছে। আবার /start দিন।")
        return

    context.user_data["selected_channel"] = channel_key
    channel_info = CHANNELS[channel_key]

    await query.edit_message_text(
        f"✅ সিলেক্টেড প্যাকেজ: **{channel_info['name']}**\n"
        f"💰 মেম্বারশিপ ফি: {channel_info['price']}\n"
        f"📱 বিকাশ/নগদ (Personal): `{channel_info['number']}`\n\n"
        f"টাকা পাঠিয়ে TrxID এখানে পাঠান।",
        parse_mode="Markdown"
    )

async def receive_trx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channel_key = context.user_data.get("selected_channel")
    if not channel_key or channel_key not in CHANNELS:
        await update.message.reply_text("⚠️ অনুগ্রহ করে প্রথমে /start কমান্ড দিয়ে একটি প্যাকেজ সিলেক্ট করুন।")
        return

    user = update.effective_user
    trx_id = update.message.text
    channel_info = CHANNELS[channel_key]

    await update.message.reply_text("⏳ অ্যাডমিনের কাছে তথ্য পাঠানো হয়েছে, অনুগ্রহ করে অপেক্ষা করুন।")

    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}_{channel_key}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}_{channel_key}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🔔 **নতুন পেমেন্ট রিকোয়েস্ট!**\n\n"
             f"📦 প্যাকেজ: {channel_info['name']} ({channel_info['price']})\n"
             f"👤 নাম: {user.first_name}\n"
             f"🆔 আইডি: `{user.id}`\n"
             f"🧾 TrxID: `{trx_id}`",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    context.user_data.pop("selected_channel", None)

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_")
    action = parts[0]
    target_user_id = int(parts[1])
    channel_key = parts[2]

    channel_info = CHANNELS.get(channel_key)
    if not channel_info:
        await query.edit_message_text(text=f"{query.message.text}\n\n⚠️ ত্রুটি: চ্যানেল কনফিগারেশন পাওয়া যায়নি።")
        return

    if action == "approve":
        try:
            expire_store = datetime.now(timezone.utc) + timedelta(hours=1)
            link = await context.bot.create_chat_invite_link(
                chat_id=channel_info["chat_id"],
                expire_date=expire_store,
                member_limit=1
            )
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🎉 **{channel_info['name']}** এর পেমেন্ট সফল!\n\n"
                     f"নিচের লিংকে ক্লিক করে চ্যানেলে যুক্ত হন (লিংকটি ১ ঘণ্টা কার্যকর থাকবে এবং ১ বার ব্যবহার করা যাবে):\n\n{link.invite_link}",
                parse_mode="Markdown"
            )
            await query.edit_message_text(text=f"{query.message.text}\n\n✅ **অনুমোদিত**", parse_mode="Markdown")
        except Exception as e:
            await query.edit_message_text(text=f"ত্রুটি: বট চ্যানেলে অ্যাডমিন আছে কিনা এবং পারমিশন ঠিক আছে কিনা দেখুন।\nError: {e}")

    elif action == "reject":
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"❌ দুঃখিত, আপনার **{channel_info['name']}** প্যাকেজের পেমেন্ট ভেরিফাই করা যায়নি। সঠিক তথ্য দিয়ে পুনরায় চেষ্টা করুন。",
            parse_mode="Markdown"
        )
        await query.edit_message_text(text=f"{query.message.text}\n\n❌ **প্রত্যাখ্যাত**", parse_mode="Markdown")

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(select_channel_callback, pattern=r"^select_"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern=r"^(approve|reject)_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_trx))

    app.run_polling()
