import logging
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
TOKEN = "9000903496:AAHF2wHsxrdr06p8tD1Y19BFa12AuDNZOvY"          # আপনার BotFather এর টোকেন
ADMIN_ID = 6813663734             # আপনার টেলিগ্রাম আইডি
CHANNEL_ID = -1004456149199        # প্রিমিয়াম চ্যানেলের আইডি (-100 সহ)
PRICE_AMOUNT = "10 টাকা"
BKASH_NAGAD_NUMBER = "01639238799"
# ========================================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🌟 **প্রিমিয়াম চ্যানেলে স্বাগতম!** 🌟\n\n"
        f"মেম্বারশিপ ফি: **{PRICE_AMOUNT}**\n"
        f"বিকাশ/নগদ (Personal): `{BKASH_NAGAD_NUMBER}`\n\n"
        f"টাকা পাঠিয়ে TrxID এখানে পাঠান।"
    )

async def receive_trx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    trx_id = update.message.text
    
    await update.message.reply_text("⏳ অ্যাডমিনের কাছে তথ্য পাঠানো হয়েছে, অনুগ্রহ করে অপেক্ষা করুন।")
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🔔 **নতুন পেমেন্ট রিকোয়েস্ট!**\n\n"
             f"👤 নাম: {user.first_name}\n"
             f"🆔 আইডি: `{user.id}`\n"
             f"🧾 TrxID: `{trx_id}`",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    action, target_user_id = query.data.split("_")
    target_user_id = int(target_user_id)
    
    if action == "approve":
        try:
            link = await context.bot.create_chat_invite_link(
                chat_id=CHANNEL_ID,
                member_limit=1
            )
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🎉 পেমেন্ট সফল! নিচের লিংকে ক্লিক করে প্রিমিয়াম চ্যানেলে যুক্ত হন:\n\n{link.invite_link}"
            )
            await query.edit_message_text(text=f"{query.message.text}\n\n✅ **অনুমোদিত**", parse_mode="Markdown")
        except Exception as e:
            await query.edit_message_text(text=f"ত্রুটি: বট চ্যানেলে অ্যাডমিন আছে কিনা এবং পারমিশন ঠিক আছে কিনা দেখুন।\nError: {e}")
            
    elif action == "reject":
        await context.bot.send_message(
            chat_id=target_user_id,
            text="িত, আপনার পেমেন্ট ভেরিফাই করা যায়নি। সঠিক তথ্য দিয়ে পুনরায় চেষ্টা করুন।"
        )
        await query.edit_message_text(text=f"{query.message.text}\n\n❌ **প্রত্যাখ্যাত**", parse_mode="Markdown")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_trx))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    app.run_polling()
