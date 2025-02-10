import asyncio
import datetime
import random
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext

# قائمة المستخدمين مع أوقات التذكير
users = {}

# قائمة رسائل التذكير العشوائية
reminder_messages = [
    "⏳ حان وقت التبرع! لا تؤجل الخير، يمكنك التبرع الآن والمساهمة في مساعدة الآخرين.",
    "🚀 وقت العطاء! لا تؤجل الخير، تبرع الآن.",
    "💙 تذكير يومي: ساعد شخصًا اليوم بالتبرع!",
    "⏳ لا تنسَ التبرع، مساهمتك تُحدث فرقًا.",
]

# روابط التبرع
vodafone_cash_link = "https://vodafone.com.eg/donation-link"  # استبدل بالرابط الصحيح
instapay_link = "https://www.instapay.com/donation"  # استبدل بالرابط الصحيح

# 🔹 دالة قراءة الإنجاز اليومي من ملف Excel
def get_daily_achievement():
    try:
        df = pd.read_excel("achievements.xlsx", engine="openpyxl")  # قراءة ملف Excel
        today = datetime.datetime.now().strftime("%Y-%m-%d")  # تاريخ اليوم

        for _, row in df.iterrows():
            if str(row["التاريخ"]) == today:
                return row["الإنجاز"]
    except FileNotFoundError:
        print("❌ لم يتم العثور على ملف الإنجازات achievements.xlsx")
        return None
    except Exception as e:
        print(f"❌ خطأ أثناء قراءة ملف الإنجازات: {e}")
        return None
    return None  # إذا لم يتم العثور على إنجاز لليوم

# 🔹 دالة إرسال التذكيرات تلقائيًا مع الإنجاز اليومي
async def reminder_job(app: Application):
    print("🔄 وظيفة التذكير تعمل بشكل صحيح...")
    while True:
        now = datetime.datetime.now().strftime("%H:%M")

        # قراءة الإنجاز اليومي
        daily_achievement = get_daily_achievement()
        if daily_achievement:
            achievement_message = f"🌟 إنجاز اليوم: {daily_achievement}"
        else:
            achievement_message = "📌 لم يتم تسجيل إنجاز لهذا اليوم."

        for user_id, data in users.items():
            print(f"⏰ التحقق من التذكيرات - الآن: {now}, وقت المستخدم: {data['time']}")
            if data['time'] == now:
                message = random.choice(reminder_messages)
                donation_links = f"\n\n📌 **طرق التبرع السهلة:**\n🔗 [فودافون كاش]({vodafone_cash_link})\n🔗 [إنستا باي]({instapay_link})"
                full_message = f"{message}\n\n{achievement_message}{donation_links}"
                
                await app.bot.send_message(chat_id=user_id, text=full_message, parse_mode="Markdown")
                print(f"📩 تم إرسال تذكير + إنجاز اليوم إلى {user_id}")
                
        await asyncio.sleep(60)  # التحقق كل دقيقة

# 🔹 دالة بدء البوت
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("مرحبًا! استخدم /set لضبط وقت التذكير.")

# 🔹 دالة عرض قائمة اختيار الساعة بنظام 12 ساعة
async def set_reminder(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton(str(h), callback_data=f"hour_{h}")] for h in range(1, 13)]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🕰 اختر الساعة (نظام 12 ساعة):", reply_markup=reply_markup)

# 🔹 دالة معالجة اختيار الساعة
async def hour_selected(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    selected_hour = query.data.split("_")[1]
    context.user_data["hour"] = selected_hour

    keyboard = [
        [InlineKeyboardButton("AM", callback_data="period_AM"), InlineKeyboardButton("PM", callback_data="period_PM")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("🌞 اختر الفترة:", reply_markup=reply_markup)

# 🔹 دالة معالجة اختيار AM/PM
async def period_selected(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    period = query.data.split("_")[1]
    context.user_data["period"] = period

    keyboard = [
        [InlineKeyboardButton("00", callback_data="minute_00"), InlineKeyboardButton("15", callback_data="minute_15"),
         InlineKeyboardButton("30", callback_data="minute_30"), InlineKeyboardButton("45", callback_data="minute_45")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("⏳ اختر الدقائق:", reply_markup=reply_markup)

# 🔹 دالة معالجة اختيار الدقائق وتسجيل التوقيت
async def minute_selected(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    minutes = query.data.split("_")[1]

    hour_12 = int(context.user_data["hour"])
    period = context.user_data["period"]

    if period == "PM" and hour_12 != 12:
        hour_24 = hour_12 + 12
    elif period == "AM" and hour_12 == 12:
        hour_24 = 0
    else:
        hour_24 = hour_12

    time_24 = f"{hour_24:02}:{minutes}"
    users[query.message.chat_id] = {"time": time_24, "donations": 0}
    print(f"✅ تم ضبط التذكير لـ {query.message.chat_id} على {time_24}")

    await query.message.reply_text(f"✅ تم ضبط التذكير على {hour_12}:{minutes} {period} ({time_24} بنظام 24 ساعة).")

# 🔹 إعداد البوت
TOKEN = "7825004828:AAEd9kzdejbzG9NO8yahHVe7xai7x_b94Ks"  # استبدل التوكن هنا
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("set", set_reminder))
app.add_handler(CallbackQueryHandler(hour_selected, pattern="^hour_"))
app.add_handler(CallbackQueryHandler(period_selected, pattern="^period_"))
app.add_handler(CallbackQueryHandler(minute_selected, pattern="^minute_"))

# 🔹 تشغيل التذكيرات في الخلفية
async def main():
    asyncio.create_task(reminder_job(app))
    await app.run_polling()

if __name__ == "__main__":
    import platform
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    import nest_asyncio
import asyncio

nest_asyncio.apply()  # حل مشكلة Event Loop في Windows والبيئات التي تدعم Async

if __name__ == "__main__":
    import platform
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

