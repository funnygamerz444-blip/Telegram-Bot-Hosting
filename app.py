import telebot
import requests
import random
import json
import os
import time
from datetime import datetime, timedelta, timezone
from flask import Flask
import threading

# --------------------- WEB SERVICE (FLASK SERVER) ---------------------
app = Flask('')

@app.route('/')
def home():
    return "I am alive and Bot is running!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = threading.Thread(target=run)
    t.start()
# ----------------------------------------------------------------------

# --------------------- BOT CONFIG ---------------------
API_TOKEN = '8897085401:AAFlXYw5NMd2xBtgC8R1XCDZxboQ3MLsfMM'
bot = telebot.TeleBot(API_TOKEN)

OWNER_ID = 8589721704
CHANNELS_TO_CHECK = ['@ldr_ysn86']

CHANNEL_BUTTONS = [
    ("Join Update Channel", "https://t.me/ldr_ysn86"),
    ("Join Support Group", "https://t.me/ldr_ysn86")
]

DATA_FILE = 'bot-data.json'
DAILY_LIMIT = 2  # দৈনিক ফ্রি লিমিট
COOLDOWN_TIME = 300  # ৫ মিনিট কুলডাউন

# --------------------- DATA PERSISTENCE ---------------------
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                return {
                    'users_data': data.get('users_data', {}),
                    'referrals': data.get('referrals', {}),
                    'total_users': data.get('total_users', []),
                    'daily_bonus': data.get('daily_bonus', {})
                }
        except:
            return {'users_data': {}, 'referrals': {}, 'total_users': [], 'daily_bonus': {}}
    return {'users_data': {}, 'referrals': {}, 'total_users': [], 'daily_bonus': {}}

def save_data():
    data = {
        'users_data': users_data,
        'referrals': referrals,
        'total_users': total_users,
        'daily_bonus': daily_bonus
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

db = load_data()
users_data = db['users_data']
referrals = db['referrals']
total_users = db['total_users']
daily_bonus = db['daily_bonus']

def get_ist_date():
    utc_now = datetime.now(timezone.utc)
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    if ist_now.hour < 4:
        return str((ist_now - timedelta(days=1)).date())
    return str(ist_now.date())

def get_current_time():
    utc_now = datetime.now(timezone.utc)
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    return ist_now.strftime('%I:%M %p')

# --------------------- FORCE JOIN FUNCTIONS ---------------------
def is_user_member(user_id):
    if user_id == OWNER_ID:
        return True
    try:
        for channel in CHANNELS_TO_CHECK:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        return True
    except:
        return True

def get_force_join_markup():
    markup = telebot.types.InlineKeyboardMarkup()
    for name, url in CHANNEL_BUTTONS:
        markup.add(telebot.types.InlineKeyboardButton(f"📢 {name}", url=url))
    markup.add(telebot.types.InlineKeyboardButton("🔄 Try Again & Verify", callback_data="verify_membership"))
    return markup

# --------------------- MAIN REPLY KEYBOARD (MENU) ---------------------
def get_main_menu_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        telebot.types.KeyboardButton("👤 My Profile"),
        telebot.types.KeyboardButton("🎁 Daily Bonus"),
        telebot.types.KeyboardButton("👥 Referral System"),
        telebot.types.KeyboardButton("🏆 Leaderboard"),
        telebot.types.KeyboardButton("⚡ Send Like"),
        telebot.types.KeyboardButton("🛠 Support")
    )
    return markup

# --------------------- HANDLERS: START & MENU ---------------------
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    str_user_id = str(user_id)

    if user_id not in total_users and user_id != OWNER_ID:
        total_users.append(user_id)
        save_data()

    args = message.text.split()
    if len(args) > 1 and user_id != OWNER_ID:
        ref_id = args[1]
        if ref_id != str_user_id and str_user_id not in referrals.get('tracked', []):
            if 'tracked' not in referrals:
                referrals['tracked'] = []
            referrals['tracked'].append(str_user_id)
            
            if ref_id not in referrals:
                referrals[ref_id] = {'count': 0, 'bonus_likes': 0}
            referrals[ref_id]['count'] += 1
            referrals[ref_id]['bonus_likes'] += 1  
            save_data()
            try:
                bot.send_message(int(ref_id), "🎁 *Referral Alert!*\nSomeone joined via your referral link! You got `+1` Extra Like Limit bonus! 🔥", parse_mode='Markdown')
            except:
                pass

    if not is_user_member(user_id):
        bot.reply_to(
            message,
            "⚠️ *Please join our official channel first to use this bot!*",
            parse_mode="Markdown",
            reply_markup=get_force_join_markup()
        )
        return

    bot.reply_to(
        message,
        "✅ *Welcome to LDR LIKE BOT✨!*\n\n"
        "নিচের মেনু বাটন থেকে আপনার প্রয়োজনীয় অপশনটি সিলেক্ট করুন অথবা `/like {region} {uid}` কমান্ড ব্যবহার করুন।",
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data == "verify_membership")
def handle_verify(call):
    user_id = call.from_user.id
    if is_user_member(user_id):
        bot.answer_callback_query(call.id, "✅ Verification Successful!")
        bot.edit_message_text(
            "🎉 *Verification Successful!*\n\nএখন আপনি নিচের মেনু ব্যবহার করতে পারেন।",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='Markdown'
        )
        bot.send_message(call.message.chat.id, "👇 মেনু থেকে অপশন বেছে নিন:", reply_markup=get_main_menu_keyboard())
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনো চ্যানেলে জয়েন করেননি!", show_alert=True)

# --------------------- TEXT MENU BUTTON HANDLERS ---------------------
@bot.message_handler(func=lambda message: message.text in ["👤 My Profile", "🎁 Daily Bonus", "👥 Referral System", "🏆 Leaderboard", "⚡ Send Like", "🛠 Support"])
def handle_menu_buttons(message):
    user_id = message.from_user.id
    str_user_id = str(user_id)
    text = message.text

    if not is_user_member(user_id):
        bot.reply_to(message, "⚠️ Please join our official channel first!", reply_markup=get_force_join_markup())
        return

    if text == "👤 My Profile":
        ref_data = referrals.get(str_user_id, {'count': 0, 'bonus_likes': 0})
        ref_count = ref_data['count']
        bonus_limit = ref_data['bonus_likes']
        total_limit = DAILY_LIMIT + bonus_limit
        
        profile_text = (
            f"👤 *YOUR PROFILE*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 User ID: `{user_id}`\n"
            f"📛 Name: {message.from_user.first_name}\n"
            f"🎁 Referral Count: `{ref_count}`\n"
            f"⚡ Total Daily Limit: `{total_limit}` Likes\n"
            f"━━━━━━━━━━━━━━━━━━━━━"
        )
        bot.reply_to(message, profile_text, parse_mode='Markdown')

    elif text == "🎁 Daily Bonus":
        today = get_ist_date()
        if daily_bonus.get(str_user_id) == today:
            bot.reply_to(message, "❌ আপনি আজকের ডেইলি বোনাস আগেই নিয়ে ফেলেছেন! কাল আবার ট্রাই করুন।", parse_mode='Markdown')
        else:
            daily_bonus[str_user_id] = today
            if str_user_id not in referrals:
                referrals[str_user_id] = {'count': 0, 'bonus_likes': 0}
            referrals[str_user_id]['bonus_likes'] += 1  
            save_data()
            bot.reply_to(message, "🎉 অভিনন্দন! আপনি আজকের ডেইলি বোনাস হিসেবে **+1 Extra Like Limit** সফলভাবে পেয়েছেন! 🔥", parse_mode='Markdown')

    elif text == "👥 Referral System":
        bot_username = bot.get_me().username
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        ref_data = referrals.get(str_user_id, {'count': 0, 'bonus_likes': 0})
        
        ref_msg = (
            f"👥 *REFERRAL SYSTEM*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"প্রতিটি রেফারে পাবেন বোনাস লাইক লিমিট!\n\n"
            f"🔗 *Your Ref Link:*\n`{ref_link}`\n\n"
            f"📊 Total Referred Users: `{ref_data['count']}`\n"
            f"🎁 Earned Bonus Limits: `{ref_data['bonus_likes']}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━"
        )
        bot.reply_to(message, ref_msg, parse_mode='Markdown')

    elif text == "🏆 Leaderboard":
        sorted_refs = sorted(referrals.items(), key=lambda x: x[1].get('count', 0) if isinstance(x[1], dict) else 0, reverse=True)[:5]
        lb_text = "🏆 *TOP REFERRAL LEADERBOARD*\n━━━━━━━━━━━━━━━━━━━━━\n"
        
        rank = 1
        for uid, data in sorted_refs:
            if uid != 'tracked' and isinstance(data, dict):
                lb_text += f"{rank}. User ID `{uid}` ➔ `{data['count']}` Referrals\n"
                rank += 1
        if rank == 1:
            lb_text += "এখনো কেউ লিডারবোর্ডে নেই!"
        
        bot.reply_to(message, lb_text, parse_mode='Markdown')

    elif text == "⚡ Send Like":
        bot.reply_to(message, "🎮 লাইক পাঠানোর সঠিক নিয়ম:\n\n`/like {region} {uid}`\n\nউদাহরণ:\n`/like bd 3140070800`", parse_mode='Markdown')

    elif text == "🛠 Support":
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("💬 Join Support Group", url="https://t.me/ldr_ysn86"))
        bot.reply_to(message, "🛠 কোনো সমস্যা হলে আমাদের সাপোর্ট গ্রুপে যোগাযোগ করুন:", reply_markup=markup)

# --------------------- LIKE HANDLER WITH COOLDOWN ---------------------
@bot.message_handler(commands=['like'])
def handle_like(message):
    global users_data
    user_id = message.from_user.id
    str_user_id = str(user_id)

    if not is_user_member(user_id):
        bot.reply_to(message, "⚠️ Please join our official channel first!", reply_markup=get_force_join_markup())
        return

    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "❌ Usᴀɢᴇ: `/like {region} {uid}`\nExᴀᴍᴘʟᴇ: `/like bd 3140070800`", parse_mode='Markdown')
        return

    region = args[1].lower()
    uid = args[2]

    supported_regions = ['ind', 'id', 'sg', 'my', 'ph', 'bd']
    if region not in supported_regions:
        bot.reply_to(message, f"❌ Invalid region! Supported: {', '.join(supported_regions)}", parse_mode='Markdown')
        return

    today = get_ist_date()
    ref_bonus = referrals.get(str_user_id, {}).get('bonus_likes', 0)
    total_allowed_limit = DAILY_LIMIT + ref_bonus

    if user_id != OWNER_ID:
        if str_user_id not in users_data or users_data[str_user_id]['date'] != today:
            users_data[str_user_id] = {'date': today, 'count': 0, 'last_time': 0}
        
        last_time = users_data[str_user_id].get('last_time', 0)
        elapsed = time.time() - last_time
        if elapsed < COOLDOWN_TIME:
            remaining_sec = int(COOLDOWN_TIME - elapsed)
            mins, secs = divmod(remaining_sec, 60)
            bot.reply_to(message, f"⏳ *Please wait {mins}m {secs}s before sending another request!*", parse_mode='Markdown')
            return

        current_used = users_data[str_user_id]['count']
        if current_used >= total_allowed_limit:
            bot.reply_to(message, f"❌ Daily limit reached! ({current_used}/{total_allowed_limit}). Try again tomorrow.", parse_mode='Markdown')
            return

    sent_msg = bot.reply_to(message, "⏳ *[ 1/3 ] Connecting to game server...*", parse_mode='Markdown')
    time.sleep(1)

    try:
        bot.edit_message_text("⚡ *[ 2/3 ] Sending likes to player profile...*", chat_id=message.chat.id, message_id=sent_msg.message_id, parse_mode='Markdown')
    except:
        pass

    api_url = f"http://br-raja-info-v3.vercel.app/accinfo?uid={uid}&region={region}"

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        bot.edit_message_text(f"❌ API connection error:\n`{str(e)}`", chat_id=message.chat.id, message_id=sent_msg.message_id, parse_mode='Markdown')
        return

    try:
        name = data['basicInfo']['nickname']
        likes_after = int(data['basicInfo']['liked'])
        likes_given = random.randint(110, 200)
        likes_before = max(0, likes_after - likes_given)

        if user_id != OWNER_ID:
            users_data[str_user_id]['count'] += 1
            users_data[str_user_id]['last_time'] = time.time()
            save_data()
            remaining_likes = total_allowed_limit - users_data[str_user_id]['count']
        else:
            remaining_likes = "♾️ UNLIMITED"

        current_time = get_current_time()

        template = (
            f"🎉 Lɪᴋᴇ Sᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ 👍\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"👑 Nᴀᴍᴇ: {name}\n"
            f"🕹️ Uɪᴅ: {uid}\n"
            f"🌐 Rᴇɢɪᴏɴ: {region.upper()}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤡 Before Like: {likes_before}\n"
            f"💀 Lɪᴋᴇs Get: {likes_given}\n"
            f"💯 Now Like: {likes_after}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 Rᴇᴍᴀɪɴɪɴɢ: {remaining_likes}\n"
            f"⏰ Tɪᴍᴇ: {current_time}"
        )
        if user_id == OWNER_ID:
            template += "\n━━━━━━━━━━━━━━━━━━━━━\n👑 OWNER UNLIMITED ACCESS 👑"

        bot.edit_message_text(template, chat_id=message.chat.id, message_id=sent_msg.message_id, parse_mode='Markdown')

    except KeyError:
        bot.edit_message_text("❌ Invalid UID or player not found.", chat_id=message.chat.id, message_id=sent_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Unexpected error:\n`{str(e)}`", chat_id=message.chat.id, message_id=sent_msg.message_id, parse_mode='Markdown')

# --------------------- RUNNER WITH AUTO RECONNECT ---------------------
if __name__ == "__main__":
    print("🚀 LDR LIKE BOT✨ Iꜱ Rᴜɴɴɪɴɢ 🏃‍♂️ (All Requested Features Added)")
    keep_alive()  # ফ্লাক সার্ভার ব্যাকগ্রাউন্ডে রান করবে
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=30)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)
