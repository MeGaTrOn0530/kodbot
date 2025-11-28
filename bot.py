# TELEGRAM BOT - Xabar Yuborish Boti
# pip install python-telegram-bot telethon python-dotenv

import asyncio
import random
import os
import signal
import sys
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID", "25381456"))
API_HASH = os.getenv("API_HASH", "59650da4e918373ca46c417a6ac97526")

if not BOT_TOKEN:
    print("❌ Iltimos, BOT_TOKEN environment variable'ni o'rnating!")
    print("Bot tokenni @BotFather dan oling: https://t.me/BotFather")
    sys.exit(1)

# Holatlar
WAITING_PHONE, WAITING_CODE, WAITING_PASSWORD, WAITING_TARGET, WAITING_MESSAGE, WAITING_COUNT, WAITING_START_CODE, WAITING_END_CODE = range(8)

class TelegramBot:
    def __init__(self, bot_token, api_id, api_hash):
        """
        Telegram botni boshlash
        """
        self.bot_token = bot_token
        try:
            self.app = Application.builder().token(bot_token).build()
        except Exception as e:
            print(f"❌ Application initialization xatosi: {e}")
            sys.exit(1)
        
        # Foydalanuvchi ma'lumotlari
        self.user_data = {}
        
        # API sozlamalar
        self.API_ID = api_id
        self.API_HASH = api_hash
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /start komandasi
        """
        user_id = update.effective_user.id
        
        keyboard = [
            [InlineKeyboardButton("🔐 Telegram ga ulash", callback_data='connect')],
            [InlineKeyboardButton("📝 Matn yuborish", callback_data='send_text')],
            [InlineKeyboardButton("🔢 Kodlar yuborish", callback_data='send_codes')],
            [InlineKeyboardButton("ℹ️ Yordam", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = """
🎬 **TELEGRAM MESSAGE SENDER BOT**

Xush kelibsiz! Bu bot orqali Telegram foydalanuvchilariga xabarlar yuborishingiz mumkin.

**Qanday ishlaydi?**
1️⃣ Telegram ga ulanish
2️⃣ Xabar yuborish rejimini tanlash
3️⃣ Xabarlarni yuborish

Boshlash uchun quyidagi tugmalardan birini tanlang:
        """
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Tugma bosish hodisalari
        """
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if query.data == 'connect':
            await query.edit_message_text("📱 Telefon raqamingizni kiriting (+998901234567 formatda):")
            return WAITING_PHONE
        
        elif query.data == 'send_text':
            # Ulanishni tekshirish
            if user_id not in self.user_data or 'client' not in self.user_data[user_id]:
                await query.edit_message_text("❌ Avval Telegram ga ulanish kerak! /start buyrug'ini yuboring va 'Telegram ga ulash' tugmasini bosing.")
                return ConversationHandler.END
            
            await query.edit_message_text("🤖 Xabar yuborish uchun bot username kiriting (@example):")
            return WAITING_TARGET
        
        elif query.data == 'send_codes':
            # Ulanishni tekshirish
            if user_id not in self.user_data or 'client' not in self.user_data[user_id]:
                await query.edit_message_text("❌ Avval Telegram ga ulanish kerak! /start buyrug'ini yuboring va 'Telegram ga ulash' tugmasini bosing.")
                return ConversationHandler.END
            
            await query.edit_message_text("🤖 Xabar yuborish uchun bot username kiriting (@example):")
            context.user_data['mode'] = 'codes'
            return WAITING_TARGET
        
        elif query.data == 'help':
            help_text = """
ℹ️ **YORDAM**

**Komandalar:**
/start - Botni boshlash
/cancel - Amalni bekor qilish

**Qanday ishlatiladi:**

1️⃣ **Telegram ga ulanish**
   - Telefon raqamingizni kiriting
   - SMS kodni kiriting
   - Agar 2FA yoqilgan bo'lsa, parolni kiriting

2️⃣ **Matn yuborish**
   - Bot username kiriting
   - Yuborish uchun matnni kiriting
   - Necha marta yuborishni kiriting

3️⃣ **Kodlar yuborish**
   - Bot username kiriting
   - Boshlang'ich kodni kiriting
   - Oxirgi kodni kiriting
   - Kodlar ketma-ket yuboriladi

**Ogohlantirish:**
Bu bot haqiqiy xabarlar yuboradi! Faqat ruxsat etilgan botlarga xabar yuboring.
            """
            await query.edit_message_text(help_text, parse_mode='Markdown')
            return ConversationHandler.END
    
    async def receive_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Telefon raqamini qabul qilish
        """
        user_id = update.effective_user.id
        phone = update.message.text.strip()
        
        if not phone.startswith('+'):
            await update.message.reply_text("❌ Telefon raqam + belgisi bilan boshlanishi kerak! Qayta kiriting:")
            return WAITING_PHONE
        
        # User data yaratish
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        
        self.user_data[user_id]['phone'] = phone
        
        try:
            # Telegram clientni yaratish
            session_name = f"session_{user_id}"
            client = TelegramClient(session_name, self.API_ID, self.API_HASH)
            
            await client.connect()
            
            if not await client.is_user_authorized():
                # SMS kod so'rash
                await client.send_code_request(phone)
                self.user_data[user_id]['client'] = client
                
                await update.message.reply_text("📨 SMS kod yuborildi! Kodni kiriting:")
                return WAITING_CODE
            else:
                self.user_data[user_id]['client'] = client
                await update.message.reply_text("✅ Muvaffaqiyatli ulandi! /start buyrug'ini yuboring.")
                return ConversationHandler.END
                
        except Exception as e:
            await update.message.reply_text(f"❌ Xatolik: {str(e)}\n\nQayta urinish uchun /start buyrug'ini yuboring.")
            return ConversationHandler.END
    
    async def receive_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        SMS kodni qabul qilish
        """
        user_id = update.effective_user.id
        code = update.message.text.strip()
        
        if user_id not in self.user_data or 'client' not in self.user_data[user_id]:
            await update.message.reply_text("❌ Xatolik! /start dan qayta boshlang.")
            return ConversationHandler.END
        
        try:
            client = self.user_data[user_id]['client']
            phone = self.user_data[user_id]['phone']
            
            self.user_data[user_id]['code'] = code
            
            await client.sign_in(phone, code)
            await update.message.reply_text("✅ Muvaffaqiyatli ulandi! /start buyrug'ini yuboring.")
            return ConversationHandler.END
            
        except SessionPasswordNeededError:
            await update.message.reply_text("🔒 Ikki bosqichli autentifikatsiya (2FA) parol kerak! Parolni kiriting:")
            return WAITING_PASSWORD
        except PhoneCodeInvalidError:
            await update.message.reply_text("❌ Noto'g'ri kod! Qayta kiriting:")
            return WAITING_CODE
        except Exception as e:
            await update.message.reply_text(f"❌ Xatolik: {str(e)}\n\nQayta urinish uchun /start buyrug'ini yuboring.")
            return ConversationHandler.END
    
    async def receive_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        2FA parolni qabul qilish
        """
        user_id = update.effective_user.id
        password = update.message.text.strip()
        
        if user_id not in self.user_data or 'client' not in self.user_data[user_id]:
            await update.message.reply_text("❌ Xatolik! /start dan qayta boshlang.")
            return ConversationHandler.END
        
        try:
            client = self.user_data[user_id]['client']
            code = self.user_data[user_id].get('code')
            
            if code:
                await client.sign_in(phone=self.user_data[user_id]['phone'], code=code, password=password)
            else:
                await client.sign_in(password=password)
            
            await update.message.reply_text("✅ Muvaffaqiyatli ulandi! /start buyrug'ini yuboring.")
            return ConversationHandler.END
            
        except Exception as e:
            await update.message.reply_text(f"❌ Xatolik: {str(e)}\n\nNoto'g'ri parol yoki boshqa xatolik. /start dan qayta boshlang.")
            return ConversationHandler.END
    
    async def receive_target(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Maqsad bot username qabul qilish
        """
        target = update.message.text.strip()
        
        if not target.startswith('@'):
            target = '@' + target
        
        context.user_data['target'] = target
        
        # Rejimni tekshirish va holat qaytarish
        if context.user_data.get('mode') == 'codes':
            await update.message.reply_text("🔢 Boshlang'ich kodni kiriting (masalan: 1):")
            return WAITING_START_CODE
        else:
            await update.message.reply_text("📝 Yuborish uchun matnni kiriting:")
            return WAITING_MESSAGE
    
    async def receive_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Yuborish uchun matnni qabul qilish
        """
        message = update.message.text.strip()
        context.user_data['message'] = message
        
        await update.message.reply_text("🔢 Necha marta yuborish kerak? (masalan: 10):")
        return WAITING_COUNT
    
    async def receive_count(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Yuborish sonini qabul qilish
        """
        try:
            count = int(update.message.text.strip())
            if count <= 0:
                raise ValueError()
            
            user_id = update.effective_user.id
            target = context.user_data['target']
            message = context.user_data['message']
            
            await update.message.reply_text(f"🚀 Yuborish boshlandi!\n\n📝 Matn: {message}\n🔢 Soni: {count}\n🤖 Maqsad: {target}")
            
            # Xabarlarni yuborish
            client = self.user_data[user_id]['client']
            
            successful = 0
            failed = 0
            
            for i in range(1, count + 1):
                try:
                    await client.send_message(target, message)
                    successful += 1
                    
                    if i % 10 == 0:
                        await update.message.reply_text(f"📊 Progress: {i}/{count} (✅{successful} ❌{failed})")
                    
                    # Kutish
                    if i < count:
                        delay = random.uniform(0.1, 0.4)
                        await asyncio.sleep(delay)
                        
                        # Har 50 dan keyin 10 soniya
                        if count >= 50 and i % 50 == 0:
                            await update.message.reply_text("☕ 10 soniya tanaffus...")
                            await asyncio.sleep(10)
                    
                except Exception as e:
                    failed += 1
                    await asyncio.sleep(3)
            
            # Natija
            await update.message.reply_text(f"🏁 TUGADI!\n\n✅ Muvaffaqiyatli: {successful}\n❌ Xato: {failed}\n📈 Foiz: {(successful/count)*100:.1f}%")
            
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text("❌ To'g'ri son kiriting! Qayta kiriting:")
            return WAITING_COUNT
    
    async def receive_start_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Boshlang'ich kodni qabul qilish
        """
        try:
            start_code = int(update.message.text.strip())
            if start_code <= 0:
                raise ValueError()
            
            context.user_data['start_code'] = start_code
            await update.message.reply_text("🔢 Oxirgi kodni kiriting (masalan: 400):")
            return WAITING_END_CODE
            
        except ValueError:
            await update.message.reply_text("❌ To'g'ri son kiriting! Qayta kiriting:")
            return WAITING_START_CODE
    
    async def receive_end_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Oxirgi kodni qabul qilish va yuborishni boshlash
        """
        try:
            end_code = int(update.message.text.strip())
            start_code = context.user_data['start_code']
            
            if end_code <= start_code:
                raise ValueError("Oxirgi kod boshlang'ichdan katta bo'lishi kerak!")
            
            user_id = update.effective_user.id
            target = context.user_data['target']
            
            codes = list(range(start_code, end_code + 1))
            total = len(codes)
            
            await update.message.reply_text(f"🚀 Kodlar yuborish boshlandi!\n\n🔢 Oraliq: {start_code} → {end_code}\n📊 Jami: {total}\n🤖 Maqsad: {target}")
            
            # Kodlarni yuborish
            client = self.user_data[user_id]['client']
            
            successful = 0
            failed = 0
            
            for i, code in enumerate(codes, 1):
                try:
                    await client.send_message(target, str(code))
                    successful += 1
                    
                    if i % 20 == 0:
                        await update.message.reply_text(f"📊 Progress: {i}/{total} (✅{successful} ❌{failed})")
                    
                    # Kutish
                    if i < total:
                        delay = random.uniform(0.1, 0.4)
                        await asyncio.sleep(delay)
                        
                        # Har 50 dan keyin 10 soniya
                        if total >= 50 and i % 50 == 0:
                            await update.message.reply_text("☕ 10 soniya tanaffus...")
                            await asyncio.sleep(10)
                    
                except Exception as e:
                    failed += 1
                    await asyncio.sleep(3)
            
            # Natija
            await update.message.reply_text(f"🏁 TUGADI!\n\n✅ Muvaffaqiyatli: {successful}\n❌ Xato: {failed}\n📈 Foiz: {(successful/total)*100:.1f}%")
            
            return ConversationHandler.END
            
        except ValueError as e:
            await update.message.reply_text(f"❌ {str(e)}\n\nQayta kiriting:")
            return WAITING_END_CODE
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Amalni bekor qilish
        """
        await update.message.reply_text("❌ Amal bekor qilindi. /start buyrug'ini yuboring.")
        return ConversationHandler.END
    
    def setup_handlers(self):
        """
        Handler'larni sozlash
        """
        # Connect conversation handler
        connect_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.button_handler, pattern='^connect$')],
            states={
                WAITING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_phone)],
                WAITING_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_code)],
                WAITING_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_password)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        
        # Send text conversation handler
        send_text_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.button_handler, pattern='^send_text$')],
            states={
                WAITING_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_target)],
                WAITING_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_message)],
                WAITING_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_count)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        
        # Send codes conversation handler
        send_codes_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.button_handler, pattern='^send_codes$')],
            states={
                WAITING_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_target)],
                WAITING_START_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_start_code)],
                WAITING_END_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_end_code)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        
        # Handlerlarni qo'shish
        self.app.add_handler(CommandHandler('start', self.start))
        self.app.add_handler(connect_handler)
        self.app.add_handler(send_text_handler)
        self.app.add_handler(send_codes_handler)
        self.app.add_handler(CallbackQueryHandler(self.button_handler))
        self.app.add_handler(CommandHandler('cancel', self.cancel))
    
    def run(self):
        """
        Botni ishga tushirish
        """
        self.setup_handlers()
        print("🤖 Bot ishga tushdi! Polling boshlanmoqda...")
        try:
            asyncio.run(self.app.run_polling(allowed_updates=Update.ALL_TYPES))
        except Exception as e:
            print(f"❌ Bot ishga tushtirishda xatolik: {e}")
            raise

def signal_handler(sig, frame):
    print('\n🛑 Bot to\'xtatildi (SIGTERM/SIGINT)')
    sys.exit(0)

# BOTNI ISHGA TUSHIRISH
if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        print("🚀 Telegram Bot Ishga Tushmoqda...")
        print(f"📌 Bot Token: {BOT_TOKEN[:10]}...")
        bot = TelegramBot(BOT_TOKEN, API_ID, API_HASH)
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("\n🛑 Bot to'xtatildi")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Botda xatolik yuz berdi: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
