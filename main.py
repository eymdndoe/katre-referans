from keep_alive import keep_alive

keep_alive()

import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes
)

# --- AYARLAR ---
BOT_TOKEN = "8481698848:AAFw55fXXVwmDQt56UyAxQJ1ukfCocnoUf8"
ADMIN_ID = 6484811971
BOT_USERNAME = "KatreSmsOnayBot"
REQUIRED_CHANNEL = "@KatreSms"
REQUIRED_GROUP = "https://t.me/KatreSmsChat"  # Yeni grup
REQUIRED_GROUP_ID = "-1002900454087"  # Bu ID'yi gerçek grup ID'si ile değiştirin

# --- VERİ DOSYALARI ---
USERS_FILE = "users.json"
STOCK_FILE = "stock.json"
BANNED_FILE = "banned.json"

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def load_banned():
    try:
        with open(BANNED_FILE, "r") as f:
            return json.load(f)
    except:
        return {"banned_users": []}

def save_banned(banned_data):
    with open(BANNED_FILE, "w") as f:
        json.dump(banned_data, f, indent=2)

def load_stock():
    try:
        with open(STOCK_FILE, "r") as f:
            return json.load(f)
    except:
        return {"numbers": []}

def save_stock(stock):
    with open(STOCK_FILE, "w") as f:
        json.dump(stock, f, indent=2)

def get_greeting():
    import datetime
    now = datetime.datetime.now()
    hour = now.hour
    
    if 5 <= hour < 12:
        return "🌅 Günaydın!"
    elif 12 <= hour < 18:
        return "☀️ İyi günler!"
    elif 18 <= hour < 22:
        return "🌆 İyi akşamlar!"
    else:
        return "🌙 İyi geceler!"

def calculate_level(tokens):
    """Jeton sayısına göre seviye hesapla"""
    if tokens < 10:
        return 1, 10 - tokens  # Seviye 1, kalan jeton
    elif tokens < 30:  # 10 + 20 = 30
        return 2, 30 - tokens  # Seviye 2, kalan jeton
    elif tokens < 60:  # 10 + 20 + 30 = 60
        return 3, 60 - tokens  # Seviye 3, kalan jeton
    elif tokens < 100:  # 10 + 20 + 30 + 40 = 100
        return 4, 100 - tokens
    elif tokens < 150:  # +50 = 150
        return 5, 150 - tokens
    elif tokens < 210:  # +60 = 210
        return 6, 210 - tokens
    elif tokens < 280:  # +70 = 280
        return 7, 280 - tokens
    elif tokens < 360:  # +80 = 360
        return 8, 360 - tokens
    elif tokens < 450:  # +90 = 450
        return 9, 450 - tokens
    else:
        return 10, 0  # Maksimum seviye

def get_level_emoji(level):
    """Seviyeye göre emoji döndür"""
    emojis = {
        1: "🥉", 2: "🥈", 3: "🥇", 4: "💎", 5: "👑",
        6: "🏆", 7: "⭐", 8: "🌟", 9: "💫", 10: "🎖️"
    }
    return emojis.get(level, "🏅")

# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = str(user.id)
    users = load_users()
    banned = load_banned()

    # Ban kontrolü
    if user_id in banned["banned_users"]:
        await update.message.reply_text(
            "🚫 Üzgünüz, botumuz tarafından engellendiniz.\n"
            "Daha fazla bilgi için admin ile iletişime geçin → @SiberSubeden"
        )
        return

    # Referans parametresini al ve geçici kaydet
    ref_id = None
    if context.args:
        ref_id = context.args[0].replace("ref", "")

    # Eğer kullanıcı daha önce kaydedilmemişse, referans bilgisini geçici olarak kaydet
    if user_id not in users:
        users[user_id] = {
            "name": user.first_name,
            "tokens": 0,
            "temp_ref": ref_id if ref_id and ref_id != user_id and ref_id in users else None
        }
        save_users(users)

    # Kanal doğrulaması
    try:
        member = await context.bot.get_chat_member(REQUIRED_CHANNEL, user.id)
        if member.status not in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
            keyboard = [[InlineKeyboardButton("✅ Kanala Katıl", url=f"https://t.me/{REQUIRED_CHANNEL[1:]}")]]
            await update.message.reply_text(
                "🚨 Botu kullanmak için önce kanala katılmalısın.\n"
                "Kanala katıldıktan sonra tekrar /start yazman yeterli.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
    except:
        await update.message.reply_text("⚠️ Kanal bulunamadı veya bot yetkisi yok.")
        return

    # Grup doğrulaması
    try:
        member = await context.bot.get_chat_member(REQUIRED_GROUP_ID, user.id)
        if member.status not in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
            keyboard = [[InlineKeyboardButton("✅ Gruba Katıl", url=REQUIRED_GROUP)]]
            await update.message.reply_text(
                "🚨 Botu kullanmak için önce doğrulama grubuna katılmalısın.\n"
                "Gruba katıldıktan sonra tekrar /start yazman yeterli.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
    except:
        await update.message.reply_text("⚠️ Doğrulama grubu bulunamadı veya bot yetkisi yok.")
        return

    # Kullanıcı hem kanala hem gruba üye, referans kontrolü yap
    user_data = users[user_id]
    if user_data.get("temp_ref") and user_data["temp_ref"] in users:
        inviter_id = user_data["temp_ref"]
        inviter_name = users[inviter_id]["name"]
        
        # Davet edene jeton ekle
        users[inviter_id]["tokens"] += 1
        
        # Referans bilgisini temizle
        users[user_id]["temp_ref"] = None
        save_users(users)
        
        # Davet edene mesaj gönder
        try:
            await context.bot.send_message(
                chat_id=inviter_id,
                text=f"🎉 Referansınız sayıldı!\n"
                     f"👤 Davet edilen: {user.first_name}\n"
                     f"🎁 +1 jeton kazandınız!"
            )
        except:
            pass  # Mesaj gönderilemezse sessizce devam et
        
        # Davet edilene mesaj gönder
        greeting = get_greeting()
        await update.message.reply_text(
            f"{greeting}\n"
            f"🎉 Başarıyla {inviter_name} tarafından davet edildiniz!\n"
            f"Hoş geldin {user.first_name}!"
        )
    else:
        # Normal hoş geldin mesajı
        greeting = get_greeting()
        await update.message.reply_text(f"{greeting}\nHoş geldin {user.first_name}!")

    # Menü aç
    await show_menu(update, users[user_id]["tokens"], user_id)

# --- MENÜ ---
async def show_menu(update: Update, tokens: int, user_id: str):
    level, remaining = calculate_level(tokens)
    level_emoji = get_level_emoji(level)
    
    keyboard = [
        [InlineKeyboardButton("🎁 Jetonlarım", callback_data="my_tokens")],
        [InlineKeyboardButton("🎯 Referans Linkim", callback_data="my_ref")],
        [InlineKeyboardButton("📱 Numara Al", callback_data="get_number")],
    ]
    text = (f"📋 Menü\n\n"
            f"👤 Kullanıcı ID: {user_id}\n"
            f"🎁 Jeton Sayın: {tokens}\n"
            f"{level_emoji} Seviye: {level}")
    
    if level < 10:
        text += f"\n📈 Bir sonraki seviye için: {remaining} jeton kaldı"
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def menu_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    users = load_users()
    banned = load_banned()

    # Ban kontrolü
    if user_id in banned["banned_users"]:
        await query.edit_message_text(
            "🚫 Üzgünüz, botumuz tarafından engellendiniz.\n"
            "Daha fazla bilgi için admin ile iletişime geçin → @SiberSubeden"
        )
        return

    if query.data == "my_tokens":
        tokens = users[user_id]["tokens"]
        await query.edit_message_text(
            f"🎁 Jeton sayın: {tokens}",
            reply_markup=query.message.reply_markup
        )

    elif query.data == "my_ref":
        link = f"https://t.me/{BOT_USERNAME}?start=ref{user_id}"
        await query.edit_message_text(
            f"🎯 Referans linkin:\n{link}",
            reply_markup=query.message.reply_markup
        )

    elif query.data == "get_number":
        tokens = users[user_id]["tokens"]
        if tokens >= 10:
            # Stok kontrolü
            stock = load_stock()
            if not stock["numbers"]:
                await query.edit_message_text(
                    "❌ Üzgünüz! Şu anda numara stoğumuz bulunmuyor.\n"
                    "Admin ile iletişime geçebilirsiniz → @SiberSubeden",
                    reply_markup=query.message.reply_markup
                )
                return
            
            # Stoktan bir numara al
            number = stock["numbers"].pop(0)
            save_stock(stock)
            
            # Jetonu düş
            users[user_id]["tokens"] -= 10
            save_users(users)
            
            # Numarayı kullanıcıya gönder
            await query.edit_message_text(
                f"🎉 Numara başarıyla alındı!\n\n"
                f"📱 Numaranız: `{number}`\n\n"
                f"Kullanım talimatları için admin ile iletişime geçin → @SiberSubeden\n"
                f"🎁 Kalan jeton: {users[user_id]['tokens']}",
                reply_markup=query.message.reply_markup,
                parse_mode="Markdown"
            )
            
            # Admin'e bildirim gönder
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"📱 Numara Alımı!\n\n"
                         f"👤 Kullanıcı: {users[user_id]['name']} ({user_id})\n"
                         f"📱 Alınan numara: {number}\n"
                         f"📦 Kalan stok: {len(stock['numbers'])}"
                )
            except:
                pass
        else:
            await query.edit_message_text(
                "❌ Yetersiz jeton. En az 10 jeton gerekli.",
                reply_markup=query.message.reply_markup
            )

# --- ADMIN PANELİ ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Yetkin yok.")
        return

    stock = load_stock()
    stock_count = len(stock["numbers"])
    
    keyboard = [
        [InlineKeyboardButton("👥 Kullanıcı Listesi", callback_data="adm_list")],
        [InlineKeyboardButton("➕➖ Jeton Yönet", callback_data="adm_tokens")],
        [InlineKeyboardButton("🎁 Herkese Jeton Ver", callback_data="adm_give_all")],
        [InlineKeyboardButton("📢 Herkese Bildirim", callback_data="adm_broadcast")],
        [InlineKeyboardButton("📦 Stok Yönet ({stock_count})", callback_data="adm_stock")],
        [InlineKeyboardButton("🚫 Ban Yönetimi", callback_data="adm_ban")],
        [InlineKeyboardButton("📂 JSON Dışa Aktar", callback_data="adm_export")],
    ]
    await update.message.reply_text(
        f"⚙️ Admin Paneli\n\n📦 Mevcut stok: {stock_count} numara",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("🚫 Yetkin yok.")
        return

    users = load_users()
    stock = load_stock()

    if query.data == "adm_list":
        text = "👥 Kullanıcılar:\n\n"
        for uid, info in users.items():
            text += f"ID: {uid} | Ad: {info['name']} | Jeton: {info['tokens']}\n"
        await query.edit_message_text(text, reply_markup=query.message.reply_markup)

    elif query.data == "adm_tokens":
        text = (
            "➕➖ Jeton Yönetimi\n\n"
            "Komutları kullan:\n"
            "`/addtokens <user_id> <sayı>`\n"
            "`/removetokens <user_id> <sayı>`"
        )
        await query.edit_message_text(text, reply_markup=query.message.reply_markup, parse_mode="Markdown")

    elif query.data == "adm_give_all":
        text = (
            "🎁 Herkese Jeton Ver\n\n"
            "Komutu kullan:\n"
            "`/giveall <sayı>`\n\n"
            "Örnek: `/giveall 5` (herkese 5 jeton verir)"
        )
        await query.edit_message_text(text, reply_markup=query.message.reply_markup, parse_mode="Markdown")

    elif query.data == "adm_broadcast":
        text = (
            "📢 Herkese Bildirim Gönder\n\n"
            "Komutu kullan:\n"
            "`/broadcast <mesajınız>`\n\n"
            "Örnek: `/broadcast Yeni güncelleme geldi!`\n"
            "Tüm kullanıcılara mesajınız iletilecek."
        )
        await query.edit_message_text(text, reply_markup=query.message.reply_markup, parse_mode="Markdown")

    elif query.data == "adm_stock":
        stock_count = len(stock["numbers"])
        text = (
            f"📦 Stok Yönetimi\n\n"
            f"Mevcut stok: {stock_count} numara\n\n"
            "Komutları kullan:\n"
            "`/addstock <numara1> <numara2> ...`\n"
            "`/clearstock` - Tüm stoğu temizle\n"
            "`/showstock` - Stoku göster\n\n"
            "Örnek: `/addstock +905551234567 +905551234568`"
        )
        await query.edit_message_text(text, reply_markup=query.message.reply_markup, parse_mode="Markdown")

    elif query.data == "adm_ban":
        banned = load_banned()
        banned_count = len(banned["banned_users"])
        text = (
            f"🚫 Ban Yönetimi\n\n"
            f"Banlı kullanıcı sayısı: {banned_count}\n\n"
            "Komutları kullan:\n"
            "`/ban <user_id>` - Kullanıcıyı banla\n"
            "`/unban <user_id>` - Banı kaldır\n"
            "`/banlist` - Banlı kullanıcıları listele\n\n"
            "Örnek: `/ban 123456789`"
        )
        await query.edit_message_text(text, reply_markup=query.message.reply_markup, parse_mode="Markdown")

    elif query.data == "adm_export":
        with open(USERS_FILE, "rb") as f:
            await query.message.reply_document(f, filename="users.json")

# --- STOK KOMUTLARI ---
async def add_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Kullanım: /addstock <numara1> <numara2> ...")
        return
    
    stock = load_stock()
    added_numbers = []
    
    for number in context.args:
        if number not in stock["numbers"]:
            stock["numbers"].append(number)
            added_numbers.append(number)
    
    save_stock(stock)
    
    if added_numbers:
        await update.message.reply_text(
            f"✅ {len(added_numbers)} numara stoğa eklendi!\n\n"
            f"📱 Eklenen numaralar:\n" + "\n".join(added_numbers) + 
            f"\n\n📦 Toplam stok: {len(stock['numbers'])}"
        )
    else:
        await update.message.reply_text("⚠️ Hiçbir yeni numara eklenmedi. (Zaten mevcut)")

async def clear_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    stock = load_stock()
    cleared_count = len(stock["numbers"])
    stock["numbers"] = []
    save_stock(stock)
    
    await update.message.reply_text(f"🗑️ Stok temizlendi! {cleared_count} numara silindi.")

async def show_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    stock = load_stock()
    if not stock["numbers"]:
        await update.message.reply_text("📦 Stok boş!")
        return
    
    stock_text = "📦 Mevcut Stok:\n\n" + "\n".join(stock["numbers"])
    stock_text += f"\n\n📊 Toplam: {len(stock['numbers'])} numara"
    
    if len(stock_text) > 4000:  # Telegram mesaj limiti
        await update.message.reply_text(f"📦 Toplam stok: {len(stock['numbers'])} numara\n(Çok fazla numara olduğu için liste gösterilemiyor)")
    else:
        await update.message.reply_text(stock_text)

# --- BAN KOMUTLARI ---
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Kullanım: /ban <user_id>")
        return
    
    user_id = context.args[0]
    users = load_users()
    banned = load_banned()
    
    if user_id not in users:
        await update.message.reply_text("🚫 Kullanıcı bulunamadı.")
        return
    
    if user_id in banned["banned_users"]:
        await update.message.reply_text("⚠️ Kullanıcı zaten banlı.")
        return
    
    banned["banned_users"].append(user_id)
    save_banned(banned)
    
    user_name = users[user_id]["name"]
    
    # Kullanıcıya bildirim gönder
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="🚫 Botumuz tarafından engellendiniz.\n"
                 "Daha fazla bilgi için admin ile iletişime geçin → @SiberSubeden"
        )
        await update.message.reply_text(f"✅ {user_name} ({user_id}) başarıyla banlandı ve bildirim gönderildi.")
    except:
        await update.message.reply_text(f"✅ {user_name} ({user_id}) başarıyla banlandı. (Bildirim gönderilemedi)")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Kullanım: /unban <user_id>")
        return
    
    user_id = context.args[0]
    users = load_users()
    banned = load_banned()
    
    if user_id not in banned["banned_users"]:
        await update.message.reply_text("⚠️ Kullanıcı zaten banlı değil.")
        return
    
    banned["banned_users"].remove(user_id)
    save_banned(banned)
    
    user_name = users.get(user_id, {}).get("name", "Bilinmeyen")
    
    # Kullanıcıya bildirim gönder
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ Banınız kaldırılmıştır!\n"
                 "Artık botu tekrar kullanabilirsiniz. /start yazarak başlayın."
        )
        await update.message.reply_text(f"✅ {user_name} ({user_id}) banı kaldırıldı ve bildirim gönderildi.")
    except:
        await update.message.reply_text(f"✅ {user_name} ({user_id}) banı kaldırıldı. (Bildirim gönderilemedi)")

async def ban_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    banned = load_banned()
    users = load_users()
    
    if not banned["banned_users"]:
        await update.message.reply_text("📝 Banlı kullanıcı bulunmuyor.")
        return
    
    ban_text = "🚫 Banlı Kullanıcılar:\n\n"
    for user_id in banned["banned_users"]:
        user_name = users.get(user_id, {}).get("name", "Bilinmeyen")
        ban_text += f"• {user_name} ({user_id})\n"
    
    ban_text += f"\n📊 Toplam: {len(banned['banned_users'])} kullanıcı"
    await update.message.reply_text(ban_text)

# --- JETON KOMUTLARI ---
async def add_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        user_id = context.args[0]
        count = int(context.args[1])
    except:
        await update.message.reply_text("⚠️ Kullanım: /addtokens <user_id> <sayı>")
        return

    users = load_users()
    if user_id not in users:
        await update.message.reply_text("🚫 Kullanıcı bulunamadı.")
        return

    users[user_id]["tokens"] += count
    save_users(users)
    
    # Kullanıcıya bildirim gönder
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎁 Size {count} jeton eklendi!\n"
                 f"💰 Yeni bakiyeniz: {users[user_id]['tokens']} jeton"
        )
        await update.message.reply_text(f"✅ {user_id} kullanıcısına {count} jeton eklendi ve bildirim gönderildi.")
    except:
        await update.message.reply_text(f"✅ {user_id} kullanıcısına {count} jeton eklendi. (Bildirim gönderilemedi)")

async def remove_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        user_id = context.args[0]
        count = int(context.args[1])
    except:
        await update.message.reply_text("⚠️ Kullanım: /removetokens <user_id> <sayı>")
        return

    users = load_users()
    if user_id not in users:
        await update.message.reply_text("🚫 Kullanıcı bulunamadı.")
        return

    old_tokens = users[user_id]["tokens"]
    users[user_id]["tokens"] = max(0, users[user_id]["tokens"] - count)
    save_users(users)
    
    # Kullanıcıya bildirim gönder
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"📉 Hesabınızdan {count} jeton düşüldü.\n"
                 f"💰 Yeni bakiyeniz: {users[user_id]['tokens']} jeton"
        )
        await update.message.reply_text(f"✅ {user_id} kullanıcısından {count} jeton silindi ve bildirim gönderildi.")
    except:
        await update.message.reply_text(f"✅ {user_id} kullanıcısından {count} jeton silindi. (Bildirim gönderilemedi)")

async def give_all_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        count = int(context.args[0])
    except:
        await update.message.reply_text("⚠️ Kullanım: /giveall <sayı>")
        return

    users = load_users()
    success_count = 0
    total_users = len(users)
    
    await update.message.reply_text(f"🔄 {total_users} kullanıcıya {count} jeton gönderiliyor...")
    
    for user_id, user_data in users.items():
        users[user_id]["tokens"] += count
        # Her kullanıcıya bildirim gönder
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎁 Tebrikler! Size {count} jeton hediye edildi!\n"
                     f"💰 Yeni bakiyeniz: {users[user_id]['tokens']} jeton\n\n"
                     f"Admin tarafından tüm kullanıcılara dağıtıldı! 🎉"
            )
            success_count += 1
        except:
            pass  # Mesaj gönderilemezse sessizce devam et
    
    save_users(users)
    await update.message.reply_text(
        f"✅ Tamamlandı!\n"
        f"👥 Toplam kullanıcı: {total_users}\n"
        f"📨 Bildirim gönderilen: {success_count}\n"
        f"🎁 Verilen jeton: {count} (kullanıcı başına)"
    )

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Kullanım: /broadcast <mesajınız>")
        return
    
    # Mesajı birleştir
    message = " ".join(context.args)
    users = load_users()
    
    total_users = len(users)
    success_count = 0
    failed_count = 0
    
    await update.message.reply_text(f"📢 {total_users} kullanıcıya bildirim gönderiliyor...")
    
    # Her kullanıcıya mesaj gönder
    for user_id in users.keys():
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📢 **Admin Bildirimi**\n\n{message}\n\n——————————————\n🤖 {BOT_USERNAME}",
                parse_mode="Markdown"
            )
            success_count += 1
        except Exception as e:
            failed_count += 1
            # Hata detayını logla (opsiyonel)
            print(f"Mesaj gönderilemedi {user_id}: {e}")
    
    # Sonuç raporu
    await update.message.reply_text(
        f"✅ Bildirim Gönderimi Tamamlandı!\n\n"
        f"👥 Toplam kullanıcı: {total_users}\n"
        f"✅ Başarılı: {success_count}\n"
        f"❌ Başarısız: {failed_count}\n\n"
        f"📝 Gönderilen mesaj:\n\"{message}\""
    )

# --- MAIN ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_callbacks, pattern="^(my_tokens|my_ref|get_number)$"))

    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(admin_callbacks, pattern="^(adm_)"))
    app.add_handler(CommandHandler("addtokens", add_tokens))
    app.add_handler(CommandHandler("removetokens", remove_tokens))
    app.add_handler(CommandHandler("giveall", give_all_tokens))
    app.add_handler(CommandHandler("broadcast", broadcast_message))
    
    # Stok komutları
    app.add_handler(CommandHandler("addstock", add_stock))
    app.add_handler(CommandHandler("clearstock", clear_stock))
    app.add_handler(CommandHandler("showstock", show_stock))
    
    # Ban komutları
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("banlist", ban_list))

    print("🚀 Bot başlatılıyor...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
