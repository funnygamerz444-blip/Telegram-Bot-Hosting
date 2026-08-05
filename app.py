import telebot
import requests
import random
import json
import os
import time
from datetime import datetime, timedelta, timezone
from flask import Flask, request

# --------------------- BOT CONFIG ---------------------
API_TOKEN = '8897085401:AAGKBqYHum_eLUO-VQ1AKbCWMcVh6amhVJs'
bot = telebot.TeleBot(API_TOKEN)

OWNER_ID = 8589721704
CHANNELS_TO_CHECK = ['@ldr_ysn86', '@ldr_ysn_like_group']

CHANNEL_BUTTONS = [
    ("Join Update Channel", "https://t.me/ldr_ysn86"),
    ("Join Support Group", "https://t.me/ldr_ysn_like_group")
]

DATA_FILE = 'bot-data.json'
DAILY_LIMIT = 5  # Daily Free Limit
COOLDOWN_TIME = 10   # Cooldown for testing

# Image URLs as requested
SUCCESS_PHOTO = "https://www.image2url.com/r2/default/images/png-to-jpg-1785910300427-21342662-26d3-4544-8f27-1667eea5a535.jpg"
ERROR_PHOTO = "https://www.image2url.com/r2/default/images/png-to-jpg-1785910355074-55070836-bcb9-47ba-bdab-e20b4247f73b.jpg"

# --------------------- WEB SERVICE (FLASK SERVER) ---------------------
app = Flask('')

@app.route('/')
def home():
    return "I am alive and LDR Like Bot is running 24/7!"

@app.route(f'/{API_TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    else:
        return "Invalid Request", 403

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
                    'daily_bonus': data.get('daily_bonus', {}),
                    'ref_daily_limit': data.get('ref_daily_limit', {}),
                    'like_attempts': data.get('like_attempts', {})
                }
        except:
            return {'users_data': {}, 'referrals': {}, 'total_users': [], 'daily_bonus': {}, 'ref_daily_limit': {}, 'like_attempts': {}}
    return {'users_data': {}, 'referrals': {}, 'total_users': [], 'daily_bonus': {}, 'ref_daily_limit': {}, 'like_attempts': {}}

def save_data():
    data = {
        'users_data': users_data,
        'referrals': referrals,
        'total_users': total_users,
        'daily_bonus': daily_bonus,
        'ref_daily_limit': ref_daily_limit,
        'like_attempts': like_attempts
    }
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Data save error: {e}")

db = load_data()
users_data = db['users_data']
referrals = db['referrals']
total_users = db['total_users']
daily_bonus = db['daily_bonus']
ref_daily_limit = db['ref_daily_limit']
like_attempts = db.get('like_attempts', {})

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

# --------------------- HANDLERS: START ---------------------
@bot.message_handler(commands=['start'])
def handle_start(message):
    try:
        user_id = message.from_user.id
        str_user_id = str(user_id)

        if user_id not in total_users and user_id != OWNER_ID:
            total_users.append(user_id)
            save_data()

        args = message.text.split()
        today = get_ist_date()

        if len(args) > 1 and user_id != OWNER_ID:
            ref_id = args[1]
            if ref_id != str_user_id and str_user_id not in referrals.get('tracked', []):
                if 'tracked' not in referrals:
                    referrals['tracked'] = []
                referrals['tracked'].append(str_user_id)
                
                if ref_id not in referrals:
                    referrals[ref_id] = {'count': 0}
                referrals[ref_id]['count'] += 1

                if ref_id not in ref_daily_limit:
                    ref_daily_limit[ref_id] = {'date': today, 'bonus': 0}
                
                if ref_daily_limit[ref_id]['date'] != today:
                    ref_daily_limit[ref_id] = {'date': today, 'bonus': 0}
                
                ref_daily_limit[ref_id]['bonus'] += 1
                save_data()

                try:
                    bot.send_message(int(ref_id), "🎁 *Referral Alert!*\nSomeone joined via your referral link! You got `+1` Extra Like Limit bonus for today! 🔥", parse_mode='Markdown')
                except:
                    pass

        if not is_user_member(user_id):
            bot.reply_to(
                message,
                "⚠️ *Please join both of our channels/groups first to use this bot!*",
                parse_mode="Markdown",
                reply_markup=get_force_join_markup()
            )
            return

        welcome_text = (
            "🎉 *Welcome to LDR Like Bot!*\n\n"
            "Please choose an option from the menu below:"
        )
        bot.reply_to(message, welcome_text, parse_mode='Markdown', reply_markup=get_main_menu_keyboard())
    except Exception as e:
        print(f"Start error: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "verify_membership")
def handle_verify(call):
    try:
        user_id = call.from_user.id
        if is_user_member(user_id):
            bot.answer_callback_query(call.id, "✅ Verification Successful!")
            try:
                bot.edit_message_text(
                    "🎉 *Verification Successful!*\n\nNow you can use the menu below.",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    parse_mode='Markdown'
                )
            except:
                pass
            bot.send_message(call.message.chat.id, "👇 Choose an option from the menu:", reply_markup=get_main_menu_keyboard())
        else:
            bot.answer_callback_query(call.id, "❌ You have not joined all required channels/groups yet!", show_alert=True)
    except Exception as e:
        print(f"Verify error: {e}")

# --------------------- INDIVIDUAL BUTTON HANDLERS ---------------------
@bot.message_handler(func=lambda message: message.text == "👤 My Profile")
def menu_my_profile(message):
    try:
        user_id = message.from_user.id
        str_user_id = str(user_id)
        today = get_ist_date()

        if not is_user_member(user_id):
            bot.reply_to(message, "⚠️ Please join our official channels/groups first!", reply_markup=get_force_join_markup())
            return

        ref_data = referrals.get(str_user_id, {'count': 0})
        ref_count = ref_data['count']
        
        user_ref_limit = 0
        if str_user_id in ref_daily_limit and ref_daily_limit[str_user_id]['date'] == today:
            user_ref_limit = ref_daily_limit[str_user_id]['bonus']

        total_limit = DAILY_LIMIT + user_ref_limit
        
        profile_text = (
            "🔐 *MY PROFILE*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 User ID: `{user_id}`\n"
            f"📛 Name: {message.from_user.first_name}\n"
            f"🎁 Total Referrals: `{ref_count}`\n"
            f"⚡ Today's Total Limit: `{total_limit}` Likes\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🤖 Bot By: `LDR-YSN`"
        )

        # Telegram DP Fetching Logic
        try:
            photos = bot.get_user_profile_photos(user_id, limit=1)
            if photos.total_count > 0:
                file_id = photos.photos[0][-1].file_id
                bot.send_photo(message.chat.id, file_id, caption=profile_text, parse_mode='Markdown')
                return
        except:
            pass

        # If no profile photo found, send text only
        bot.reply_to(message, profile_text, parse_mode='Markdown')

    except Exception as e:
        print(f"Profile error: {e}")

@bot.message_handler(func=lambda message: message.text == "🎁 Daily Bonus")
def menu_daily_bonus(message):
    try:
        user_id = message.from_user.id
        str_user_id = str(user_id)
        today = get_ist_date()

        if not is_user_member(user_id):
            bot.reply_to(message, "⚠️ Please join our official channels/groups first!", reply_markup=get_force_join_markup())
            return

        if daily_bonus.get(str_user_id) == today:
            bonus_text = (
                "🎁 *DAILY BONUS*\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "❌ You have already claimed today's daily bonus! Try again tomorrow.\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "🤖 Bot By: `LDR-YSN`"
            )
            bot.reply_to(message, bonus_text, parse_mode='Markdown')
        else:
            daily_bonus[str_user_id] = today
            if str_user_id not in ref_daily_limit or ref_daily_limit[str_user_id]['date'] != today:
                ref_daily_limit[str_user_id] = {'date': today, 'bonus': 0}
            ref_daily_limit[str_user_id]['bonus'] += 1
            save_data()
            bonus_text = (
                "🎁 *DAILY BONUS*\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "🎉 Congratulations! You have successfully received **+1 Extra Like Limit** for today as a daily bonus! 🔥\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "🤖 Bot By: `LDR-YSN`"
            )
            bot.reply_to(message, bonus_text, parse_mode='Markdown')
    except Exception as e:
        print(f"Bonus error: {e}")

@bot.message_handler(func=lambda message: message.text == "👥 Referral System")
def menu_referral(message):
    try:
        user_id = message.from_user.id
        str_user_id = str(user_id)

        if not is_user_member(user_id):
            bot.reply_to(message, "⚠️ Please join our official channels/groups first!", reply_markup=get_force_join_markup())
            return

        bot_username = bot.get_me().username
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        ref_data = referrals.get(str_user_id, {'count': 0})
        
        ref_msg = (
            f"👥 *REFERRAL SYSTEM*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"Invite friends and get extra like limits for today!\n\n"
            f"🔗 *Your Ref Link:*\n`{ref_link}`\n\n"
            f"📊 Total Referred Users: `{ref_data['count']}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 Bot By: `LDR-YSN`"
        )
        bot.reply_to(message, ref_msg, parse_mode='Markdown')
    except Exception as e:
        print(f"Referral error: {e}")

@bot.message_handler(func=lambda message: message.text == "🏆 Leaderboard")
def menu_leaderboard(message):
    try:
        user_id = message.from_user.id
        if not is_user_member(user_id):
            bot.reply_to(message, "⚠️ Please join our official channels/groups first!", reply_markup=get_force_join_markup())
            return

        sorted_refs = sorted(referrals.items(), key=lambda x: x[1].get('count', 0) if isinstance(x[1], dict) else 0, reverse=True)[:5]
        lb_text = "🏆 *TOP REFERRAL LEADERBOARD*\n━━━━━━━━━━━━━━━━━━━━━\n"
        
        rank = 1
        for uid, data in sorted_refs:
            if uid != 'tracked' and isinstance(data, dict):
                lb_text += f"{rank}. User ID `{uid}` ➔ `{data['count']}` Referrals\n"
                rank += 1
        if rank == 1:
            lb_text += "No one is on the leaderboard yet!\n"
        
        lb_text += "━━━━━━━━━━━━━━━━━━━━━\n🤖 Bot By: `LDR-YSN`"
        bot.reply_to(message, lb_text, parse_mode='Markdown')
    except Exception as e:
        print(f"Leaderboard error: {e}")

@bot.message_handler(func=lambda message: message.text == "⚡ Send Like")
def menu_send_like(message):
    try:
        user_id = message.from_user.id
        if not is_user_member(user_id):
            bot.reply_to(message, "⚠️ Please join our official channels/groups first!", reply_markup=get_force_join_markup())
            return

        like_guide = (
            "⚡ *SEND LIKE SYSTEM*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🎮 Correct format to send likes:\n\n"
            "`/like {region} {uid}`\n\n"
            "Example:\n"
            "`/like bd 3140070800`\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🤖 Bot By: `LDR-YSN`"
        )
        bot.reply_to(message, like_guide, parse_mode='Markdown')
    except Exception as e:
        print(f"Send like menu error: {e}")

@bot.message_handler(func=lambda message: message.text == "🛠 Support")
def menu_support(message):
    try:
        user_id = message.from_user.id
        if not is_user_member(user_id):
            bot.reply_to(message, "⚠️ Please join our official channels/groups first!", reply_markup=get_force_join_markup())
            return

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("💬 Join Support Group", url="https://t.me/ldr_ysn_like_group"))
        support_text = (
            "🛠 *SUPPORT CENTER*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "If you face any issues, please contact our support group below:\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🤖 Bot By: `LDR-YSN`"
        )
        bot.reply_to(message, support_text, parse_mode='Markdown', reply_markup=markup)
    except Exception as e:
        print(f"Support error: {e}")

# --------------------- LIKE HANDLER WITH PATTERN: 1st Success, 2nd Error, 3rd Success ---------------------
@bot.message_handler(commands=['like'])
def handle_like(message):
    global users_data, like_attempts
    try:
        user_id = message.from_user.id
        str_user_id = str(user_id)

        if not is_user_member(user_id):
            bot.reply_to(message, "⚠️ Please join our official channels/groups first!", reply_markup=get_force_join_markup())
            return

        args = message.text.split()
        if len(args) < 3:
            error_msg = (
                "❌ *LIKE SENT ERROR!*\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "Usage: `/like {region} {uid}`\n"
                "Example: `/like bd 3140070800`\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "🤖 Bot By: `LDR-YSN`"
            )
            bot.send_photo(message.chat.id, ERROR_PHOTO, caption=error_msg, parse_mode='Markdown')
            return

        region = args[1].lower()
        uid = args[2]

        supported_regions = ['ind', 'id', 'sg', 'my', 'ph', 'bd', 'br', 'ru', 'us', 'tw', 'vn', 'th', 'mea', 'pk', 'sac', 'na', 'eu']
        if region not in supported_regions:
            error_msg = (
                "❌ *LIKE SENT ERROR!*\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"Unsupported Region! Supported: {', '.join(supported_regions)}\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "🤖 Bot By: `LDR-YSN`"
            )
            bot.send_photo(message.chat.id, ERROR_PHOTO, caption=error_msg, parse_mode='Markdown')
            return

        today = get_ist_date()
        
        # Track attempt sequence for pattern: 1st Success, 2nd Error, 3rd Success
        if str_user_id not in like_attempts or like_attempts[str_user_id]['date'] != today:
            like_attempts[str_user_id] = {'date': today, 'step': 0}
        
        like_attempts[str_user_id]['step'] += 1
        current_step = like_attempts[str_user_id]['step']
        save_data()

        user_ref_bonus = 0
        if str_user_id in ref_daily_limit and ref_daily_limit[str_user_id]['date'] == today:
            user_ref_bonus = ref_daily_limit[str_user_id]['bonus']

        total_allowed_limit = DAILY_LIMIT + user_ref_bonus

        if user_id != OWNER_ID:
            if str_user_id not in users_data or users_data[str_user_id]['date'] != today:
                users_data[str_user_id] = {'date': today, 'count': 0, 'last_time': 0}
            
            last_time = users_data[str_user_id].get('last_time', 0)
            elapsed = time.time() - last_time
            if elapsed < COOLDOWN_TIME:
                remaining_sec = int(COOLDOWN_TIME - elapsed)
                mins, secs = divmod(remaining_sec, 60)
                cooldown_msg = (
                    "❌ *LIKE SENT ERROR!*\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n"
                    f"Cooldown Active! Please wait {mins}m {secs}s!\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n"
                    "🤖 Bot By: `LDR-YSN`"
                )
                bot.send_photo(message.chat.id, ERROR_PHOTO, caption=cooldown_msg, parse_mode='Markdown')
                return

            current_used = users_data[str_user_id]['count']
            if current_used >= total_allowed_limit:
                limit_msg = (
                    "❌ *LIKE SENT ERROR!*\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n"
                    f"Daily Limit Reached ({current_used}/{total_allowed_limit}). Try tomorrow or refer friends.\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n"
                    "🤖 Bot By: `LDR-YSN`"
                )
                bot.send_photo(message.chat.id, ERROR_PHOTO, caption=limit_msg, parse_mode='Markdown')
                return

        # 2nd Attempt Intentional Error Condition
        if current_step % 3 == 2:
            forced_error_msg = (
                "❌ *LIKE SENT ERROR!*\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "API Server Timeout or Connection Failed!\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "🤖 Bot By: `LDR-YSN`"
            )
            bot.send_photo(message.chat.id, ERROR_PHOTO, caption=forced_error_msg, parse_mode='Markdown')
            return

        sent_msg = bot.send_message(message.chat.id, "🔄 *Connecting to game server... [1/3]*", parse_mode='Markdown')
        time.sleep(0.3)

        try:
            bot.edit_message_text("⚡ *Fetching player data & processing... [2/3]*", chat_id=message.chat.id, message_id=sent_msg.message_id, parse_mode='Markdown')
        except:
            pass

        api_urls = [
            f"https://br-raja-info-v3.vercel.app/accinfo?uid={uid}&region={region}",
            f"https://das-ff-info.netlify.app/info?uid={uid}",
            f"https://star-info-api.lovable.app/functions/v1/info-api/accinfo?uid={uid}",
            f"https://jakir-all-rounder.vercel.app/info?uid={uid}&api_key=MNSTR",
            f"https://info.killersharmabot.online/player-info?uid={uid}"
        ]

        data = None
        for api_url in api_urls:
            try:
                response = requests.get(api_url, timeout=7, headers={'User-Agent': 'Mozilla/5.0'})
                if response.status_code == 200:
                    res_json = response.json()
                    if res_json:
                        data = res_json
                        break
            except:
                continue

        if not data:
            try:
                bot.delete_message(message.chat.id, sent_msg.message_id)
            except:
                pass
            error_msg = (
                "❌ *LIKE SENT ERROR!*\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "All API Servers are busy or player UID not found!\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "🤖 Bot By: `LDR-YSN`"
            )
            bot.send_photo(message.chat.id, ERROR_PHOTO, caption=error_msg, parse_mode='Markdown')
            return

        try:
            basic_info = data.get('basicInfo', data.get('accountInfo', data.get('player_info', data)))
            
            name = basic_info.get('nickname', basic_info.get('name', 'Unknown Player'))
            likes_after = int(basic_info.get('liked', basic_info.get('likes', 0)))
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
                "✅ *LIKE SENT SUCCESSFUL [3/3]*\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"👑 Nᴀᴍᴇ: {name}\n"
                f"🕹️ Uɪᴅ: {uid}\n"
                f"🌐 Rᴇɢɪᴏɴ: {region.upper()}\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"🤡 Before Like: {likes_before}\n"
                f"💀 Lɪᴋᴇs Get: {likes_given}\n"
                f"💯 Now Like: {likes_after}\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 Rᴇᴍᴀɪɴɪɴɢ: {remaining_likes}\n"
                f"⏰ Tɪᴍᴇ: {current_time}\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "🤖 Bot By: `LDR-YSN`"
            )

            try:
                bot.delete_message(message.chat.id, sent_msg.message_id)
            except:
                pass

            bot.send_photo(message.chat.id, SUCCESS_PHOTO, caption=template, parse_mode='Markdown')

        except Exception as e:
            try:
                bot.delete_message(message.chat.id, sent_msg.message_id)
            except:
                pass
            error_msg = (
                "❌ *LIKE SENT ERROR!*\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "Data parsing error or region mismatch!\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "🤖 Bot By: `LDR-YSN`"
            )
            bot.send_photo(message.chat.id, ERROR_PHOTO, caption=error_msg, parse_mode='Markdown')
    except Exception as e:
        print(f"Like command error: {e}")

# --------------------- RUNNER ---------------------
if __name__ == "__main__":
    print("🚀 LDR Like Bot is Running 24/7...")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
