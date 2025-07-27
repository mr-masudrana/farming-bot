import telebot
import time
import firebase_admin
from firebase_admin import credentials, db

TOKEN = "8136077266:AAGKD8aUT0O52tkEHA_ANYESthXOD6GZxnY"
ADMIN_ID = 7259866148  # আপনার টেলিগ্রাম আইডি এখানে দিন
EARN_AMOUNT = 1
REF_BONUS = 2
COOLDOWN = 3600  # 1 ঘন্টা

bot = telebot.TeleBot(TOKEN)

cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://chatapp-fd388-default-rtdb.firebaseio.com'
})

def get_user_ref(user_id):
    return db.reference(f'users/{user_id}')

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    args = message.text.split()

    user_ref = get_user_ref(user_id)
    user = user_ref.get()

    if not user:
        ref_by = args[1] if len(args) > 1 else None
        user_ref.set({
            'balance': 0,
            'last_earn': 0,
            'ref_by': ref_by,
            'ref_count': 0
        })
        if ref_by and ref_by != user_id:
            ref_user = get_user_ref(ref_by)
            ref_data = ref_user.get()
            if ref_data:
                ref_user.update({
                    'balance': ref_data['balance'] + REF_BONUS,
                    'ref_count': ref_data.get('ref_count', 0) + 1
                })
        bot.send_message(message.chat.id, "✅ আপনি সফলভাবে রেজিস্টার হয়েছেন!")
    else:
        bot.send_message(message.chat.id, "🔄 আপনি আগেই রেজিস্টার করেছেন!")

@bot.message_handler(commands=['balance'])
def balance(message):
    user_id = str(message.chat.id)
    user = get_user_ref(user_id).get()
    if user:
        bot.send_message(message.chat.id, f"💰 আপনার ব্যালেন্স: {user['balance']} পয়েন্ট")
    else:
        bot.send_message(message.chat.id, "❗ প্রথমে /start দিয়ে রেজিস্টার করুন।")

@bot.message_handler(commands=['refer'])
def refer(message):
    user_id = str(message.chat.id)
    user = get_user_ref(user_id).get()
    if user:
        ref_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
        bot.send_message(message.chat.id, f"🔗 আপনার রেফারেল লিংক:\n{ref_link}\n👥 রেফার করেছেন: {user.get('ref_count', 0)} জন")
    else:
        bot.send_message(message.chat.id, "❗ প্রথমে /start দিয়ে রেজিস্টার করুন।")

@bot.message_handler(commands=['earn'])
def earn(message):
    user_id = str(message.chat.id)
    user_ref = get_user_ref(user_id)
    user = user_ref.get()
    now = int(time.time())
    if user:
        if now - user.get('last_earn', 0) >= COOLDOWN:
            user_ref.update({
                'balance': user['balance'] + EARN_AMOUNT,
                'last_earn': now
            })
            bot.send_message(message.chat.id, f"✅ আপনি {EARN_AMOUNT} পয়েন্ট পেয়েছেন!")
        else:
            wait_time = COOLDOWN - (now - user['last_earn'])
            bot.send_message(message.chat.id, f"⏳ অনুগ্রহ করে {int(wait_time/60)} মিনিট পরে আবার চেষ্টা করুন।")
    else:
        bot.send_message(message.chat.id, "❗ প্রথমে /start দিয়ে রেজিস্টার করুন।")

@bot.message_handler(commands=['withdraw'])
def withdraw(message):
    user_id = str(message.chat.id)
    user = get_user_ref(user_id).get()
    if user:
        bot.send_message(message.chat.id, "💸 উইথড্র করতে আপনার বিকাশ/নগদ নম্বর পাঠান।")
        bot.register_next_step_handler(message, process_withdraw)
    else:
        bot.send_message(message.chat.id, "❗ প্রথমে /start দিয়ে রেজিস্টার করুন।")

def process_withdraw(message):
    user_id = str(message.chat.id)
    amount = get_user_ref(user_id).get()['balance']
    bot.send_message(ADMIN_ID, f"📤 উইথড্র রিকোয়েস্ট:\n👤 ইউজার: {user_id}\n💰 এমাউন্ট: {amount}\n📞 নাম্বার: {message.text}")
    bot.send_message(message.chat.id, "✅ আপনার উইথড্র রিকোয়েস্ট জমা হয়েছে। ২৪ ঘণ্টার মধ্যে যোগাযোগ করা হবে।")

@bot.message_handler(commands=['admin'])
def admin(message):
    if message.chat.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "👑 অ্যাডমিন কমান্ড:\n/add ID AMOUNT – ব্যালেন্স অ্যাড\n/deduct ID AMOUNT – ব্যালেন্স কমান")

@bot.message_handler(commands=['add'])
def add(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        _, uid, amount = message.text.split()
        ref = get_user_ref(uid)
        data = ref.get()
        if data:
            ref.update({'balance': data['balance'] + int(amount)})
            bot.send_message(message.chat.id, "✅ ব্যালেন্স অ্যাড হয়েছে")
        else:
            bot.send_message(message.chat.id, "❌ ইউজার পাওয়া যায়নি")
    except:
        bot.send_message(message.chat.id, "❗ সঠিকভাবে লিখুন: /add ID AMOUNT")

@bot.message_handler(commands=['deduct'])
def deduct(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        _, uid, amount = message.text.split()
        ref = get_user_ref(uid)
        data = ref.get()
        if data:
            ref.update({'balance': data['balance'] - int(amount)})
            bot.send_message(message.chat.id, "✅ ব্যালেন্স কমানো হয়েছে")
        else:
            bot.send_message(message.chat.id, "❌ ইউজার পাওয়া যায়নি")
    except:
        bot.send_message(message.chat.id, "❗ সঠিকভাবে লিখুন: /deduct ID AMOUNT")

bot.polling()