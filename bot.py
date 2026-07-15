import json
import telebot
from telebot import types
import requests
import time

with open('bot_settings.json', 'r') as f:
    settings = json.load(f)

BOT_TOKEN = '8886583166:AAEL0rssJ0H6BPaVd5oeaIadRhvdJ_rLQGo'
ADMIN_ID = str(settings['admin_telegram_id'])
API_URL = 'http://keycodm.atwebpages.com/bot_api.php'
WALLETS = settings['usdt_wallets']
PRICES = settings['prices']
APK_URL = settings.get('apk_url', 'http://keycodm.atwebpages.com/app.apk')

requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook')
time.sleep(1)

bot = telebot.TeleBot(BOT_TOKEN)
print("Bot started!")

def api(action, **params):
    params['action'] = action
    try:
        r = requests.get(API_URL, params=params, timeout=10)
        return r.json()
    except:
        return {'error': 'Server error'}

@bot.message_handler(commands=['start'])
def start(msg):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("FREE Trial", "Buy Plan", "Profile", "Support")
    bot.send_message(msg.chat.id, "CODM ELITE SHOP", reply_markup=kb)

@bot.message_handler(commands=['buy'])
def buy(msg):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("FREE Trial (1 time)", callback_data="trial"),
        types.InlineKeyboardButton("Week - 15$", callback_data="week"),
        types.InlineKeyboardButton("Month - 30$", callback_data="month"),
        types.InlineKeyboardButton("Cancel", callback_data="cancel")
    )
    bot.send_message(msg.chat.id, "Choose plan:", reply_markup=kb)

@bot.message_handler(commands=['profile'])
def profile(msg):
    d = api('profile', user_id=str(msg.from_user.id))
    has_trial = d.get('has_trial', False)
    keys = d.get('keys', [])
    
    text = f"YOUR PROFILE\n\n"
    text += f"ID: {msg.from_user.id}\n"
    text += f"Name: {msg.from_user.first_name}\n"
    text += f"Trial: {'USED' if has_trial else 'AVAILABLE'}\n\n"
    
    if keys:
        text += "Keys:\n"
        for k in keys:
            text += f"- {k.get('key','?')} | {k.get('type','?')}\n"
    else:
        text += "No purchased keys"
    
    bot.send_message(msg.chat.id, text)

@bot.message_handler(commands=['support'])
def support(msg):
    bot.send_message(msg.chat.id, "Support: @idkidk1010")

@bot.message_handler(commands=['test'])
def test(msg):
    if str(msg.chat.id) != ADMIN_ID:
        return
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("Test Trial", callback_data="adm_trial"),
        types.InlineKeyboardButton("Test Week", callback_data="adm_week"),
        types.InlineKeyboardButton("Test Month", callback_data="adm_month")
    )
    bot.send_message(msg.chat.id, "ADMIN TEST", reply_markup=kb)

# Text buttons
@bot.message_handler(func=lambda m: m.text and "Trial" in m.text)
def t_trial(msg):
    d = api('get_trial', user_id=str(msg.from_user.id))
    if d.get('key'):
        bot.send_message(msg.chat.id, f"KEY: {d['key']}\n6 hours\n1 device\n\nAPK: {APK_URL}")
    else:
        bot.send_message(msg.chat.id, d.get('error','Error'))

@bot.message_handler(func=lambda m: m.text and "Buy" in m.text)
def t_buy(msg): 
    buy(msg)

@bot.message_handler(func=lambda m: m.text and "Profile" in m.text)
def t_profile(msg): 
    profile(msg)

@bot.message_handler(func=lambda m: m.text and "Support" in m.text)
def t_support(msg): 
    support(msg)

# Callbacks
@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    d = call.data
    
    if d == 'cancel':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        return
    
    if d == 'trial':
        r = api('get_trial', user_id=str(call.from_user.id))
        if r.get('key'):
            bot.send_message(call.message.chat.id, f"KEY: {r['key']}\n6 hours\n1 device\n\nAPK: {APK_URL}")
            bot.answer_callback_query(call.id, "Sent!")
        else:
            bot.answer_callback_query(call.id, r.get('error','Error'), show_alert=True)
        return
    
    if d in ['week', 'month']:
        price = PRICES.get(d, 15)
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("TON", callback_data=f"net_{d}_TON"),
            types.InlineKeyboardButton("TRC20", callback_data=f"net_{d}_TRC20"),
            types.InlineKeyboardButton("BEP20", callback_data=f"net_{d}_BEP20"),
            types.InlineKeyboardButton("ERC20", callback_data=f"net_{d}_ERC20")
        )
        kb.add(
            types.InlineKeyboardButton("Back", callback_data="back"),
            types.InlineKeyboardButton("Cancel", callback_data="cancel")
        )
        bot.edit_message_text(f"{d.upper()} - {price}$\n\nChoose network:", call.message.chat.id, call.message.message_id, reply_markup=kb)
        return
    
    if d == 'back':
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("FREE Trial", callback_data="trial"),
            types.InlineKeyboardButton("Week - 15$", callback_data="week"),
            types.InlineKeyboardButton("Month - 30$", callback_data="month"),
            types.InlineKeyboardButton("Cancel", callback_data="cancel")
        )
        bot.edit_message_text("Choose plan:", call.message.chat.id, call.message.message_id, reply_markup=kb)
        return
    
    if d.startswith('net_'):
        _, plan, net = d.split('_')
        price = PRICES.get(plan, 15)
        wallet = WALLETS.get(net, 'Not set')
        
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("GET KEY (after payment)", callback_data=f"get_{plan}"))
        kb.add(types.InlineKeyboardButton("Back", callback_data=plan))
        kb.add(types.InlineKeyboardButton("Cancel", callback_data="cancel"))
        
        bot.edit_message_text(
            f"Send {price}$ USDT\n\nNetwork: {net}\nWallet: {wallet}\n\nClick GET KEY after sending payment",
            call.message.chat.id, call.message.message_id, reply_markup=kb)
        return
    
    if d.startswith('get_'):
        plan = d.replace('get_', '')
        r = api('get_paid_key', type=plan, user_id=str(call.from_user.id))
        
        if r.get('key'):
            dur = '30 days' if plan == 'month' else '7 days'
            dev = '5 devices' if plan == 'month' else '1 device'
            bot.send_message(call.message.chat.id, f"KEY: {r['key']}\n{dur}\n{dev}\n\nAPK: {APK_URL}")
            bot.edit_message_text("Sent! Check messages.", call.message.chat.id, call.message.message_id)
            try:
                bot.send_message(ADMIN_ID, f"SALE! {call.from_user.first_name} | {plan} | {PRICES.get(plan,15)}$")
            except:
                pass
        else:
            bot.answer_callback_query(call.id, r.get('error','Error'), show_alert=True)
        return
    
    if d.startswith('adm_'):
        if str(call.from_user.id) != ADMIN_ID:
            return
        plan = d.replace('adm_', '')
        act = 'get_trial' if plan == 'trial' else 'get_paid_key'
        r = api(act, type=plan, user_id='admin')
        if r.get('key'):
            bot.send_message(call.message.chat.id, f"TEST KEY: {r['key']}\nAPK: {APK_URL}")
            bot.answer_callback_query(call.id, "Sent!")
        return

print("Ready!")
bot.polling(none_stop=True)