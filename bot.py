import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# === НАСТРОЙКИ ===
BOT_TOKEN = "8731906672:AAGDHrBZNvzhaLkzBoqy56gEcNLAWjLxWWo"
ADMIN_IDS = [1928686265] 
OWNER_USERNAME = "@exp1d" 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === БАЗА ДАННЫХ (SQLite) ===
def init_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS boosters (
                        user_id INTEGER PRIMARY KEY, 
                        username TEXT, 
                        status TEXT DEFAULT '🟢 Свободен')''')
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_boosters():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, status FROM boosters")
    res = cursor.fetchall()
    conn.close()
    return res

def update_booster_status(user_id, status):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE boosters SET status = ? WHERE user_id = ?", (status, user_id))
    conn.commit()
    conn.close()

# === КЛАВИАТУРЫ ===
def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Выбрать услугу", callback_data="services")],
        [InlineKeyboardButton(text="🕘 Занятость бустеров", callback_data="boosters_status")],
        [InlineKeyboardButton(text="📄 Правила и требования", callback_data="rules"),
         InlineKeyboardButton(text="🤝 Поддержка / Отзывы", callback_data="support")]
    ])

def services_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Буст звания", callback_data="boost_rank")],
        [InlineKeyboardButton(text="🪙 Буст Серебра", callback_data="boost_silver")],
        [InlineKeyboardButton(text="📶 Буст уровня", callback_data="boost_level")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ])

def checkout_kb(service_name):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, всё верно", callback_data=f"pay_{service_name}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="services")]
    ])

def payment_methods_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Напрямую через Владельца", callback_data="pay_direct")],
        [InlineKeyboardButton(text="💳 Платформа FunPay", callback_data="pay_funpay")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="services")]
    ])

def booster_panel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Поставить статус 'Свободен'", callback_data="status_free")],
        [InlineKeyboardButton(text="🔴 Поставить статус 'Занят'", callback_data="status_busy")]
    ])

# === КЛИЕНТСКАЯ ЧАСТЬ ===

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    add_user(message.from_user.id)
    text = (
        "Привет! Добро пожаловать в официальный бот DG | Boost Standoff ⚡️\n\n"
        "Здесь ты можешь быстро заказать буст звания, уровня или серебра, "
        "проверить занятость наших бустеров и оформить заказ в пару кликов!\n\n"
        "Навигация по кнопкам ниже 👇"
    )
    await message.answer(text, reply_markup=main_menu_kb())

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    text = "Главное меню. Навигация по кнопкам ниже 👇"
    await callback.message.edit_text(text, reply_markup=main_menu_kb())

@dp.callback_query(F.data ==


"services")
async def show_services(callback: types.CallbackQuery):
    await callback.message.edit_text("Выберите категорию услуг:", reply_markup=services_menu_kb())

@dp.callback_query(F.data == "boost_rank")
async def show_rank_prices(callback: types.CallbackQuery):
    text = (
        "⚡️ Прайс на буст звания (Действует акция до 28 сентября!):\n\n"
        "🥈 Bronze - Silver: ~50₽~ 25₽\n"
        "🏅 Bronze - Gold: ~150₽~ 75₽\n"
        "🐥 Bronze - Phoenix: ~300₽~ 150₽\n"
        "🔫 Bronze - Ranger: ~400₽~ 200₽\n"
        "🏆 Bronze - Champion: ~720₽~ 360₽\n"
        "🥋 Bronze - Master: ~800₽~ 400₽\n"
        "⚜️ Bronze - Elite: ~1200₽~ 600₽\n"
        "🌏 Bronze - Legend: ~2000₽~ 1000₽\n\n"
        "Выберите нужное звание для оформления заказа (или нажмите Далее для подтверждения):"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Перейти к оформлению", callback_data="confirm_Rank")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="services")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="MarkdownV2")

@dp.callback_query(F.data == "boost_silver")
async def show_silver_prices(callback: types.CallbackQuery):
    text = "⚡️ Прайс за буст/фарм серебра:\n\n🪙 1.000 Серебра — 200₽"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Заказать серебро", callback_data="confirm_Silver")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="services")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "boost_level")
async def show_level_prices(callback: types.CallbackQuery):
    text = (
        "⚡️ Прайс за буст уровня:\n\n"
        "📶 1 Уровень — 10₽\n\n"
        "(Цена может измениться в зависимости от текущего уровня. При заказе от 300₽ — "
        "прокачка уровня до рейтинговых игр в подарок!)"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📶 Заказать уровень", callback_data="confirm_Level")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="services")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data.startswith("confirm_"))
async def confirm_order(callback: types.CallbackQuery):
    service = callback.data.split("_")[1]
    text = (
        f"Вы выбрали: Буст {service}. Пожалуйста, подтвердите, что ваш аккаунт "
        "соответствует требованиям (нет активных банов, уровень позволяет играть в рейтинг). Всё верно?"
    )
    await callback.message.edit_text(text, reply_markup=checkout_kb(service))

@dp.callback_query(F.data.startswith("pay_") & ~F.data.in_({"pay_direct", "pay_funpay"}))
async def select_payment(callback: types.CallbackQuery):
    await callback.message.edit_text("Выберите способ оплаты:", reply_markup=payment_methods_kb())

@dp.callback_query(F.data == "pay_direct")
async def pay_direct(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Написать Владельцу", url=f"https://t.me/{OWNER_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="back_to_main")]
    ])
    await callback.message.edit_text("Свяжитесь с владельцем для перевода средств и старта буста:", reply_markup=kb)

@dp.callback_query(F.data == "pay_funpay")
async def pay_funpay(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Перейти на FunPay", url="https://funpay.com/твоя_ссылка")],
        [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="back_to_main")]
    ])
    text = "Оплатите заказ на нашей странице FunPay и следуйте инструкциям на сайте."
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "boosters_status")
async def show_boosters_status(callback: types.CallbackQuery):
    boosters = get_boosters()
    text = "🕘 Текущая загруженность нашей команды:\n\n"
    if not boosters:
        text += "Пока нет данных о бустерах."


    else:
        for username, status in boosters:
            text += f"👤 {username} — {status}\n"
            
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить статус", callback_data="boosters_status")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)

# === ПАНЕЛЬ БУСТЕРА ===
@dp.message(Command("bpanel"))
async def booster_panel_cmd(message: types.Message):
    await message.answer("🤖 Панель бустера:\n\nУправляй своей занятостью кнопками ниже:", reply_markup=booster_panel_kb())

@dp.callback_query(F.data.startswith("status_"))
async def change_status(callback: types.CallbackQuery):
    new_status = "🟢 Свободен" if callback.data == "status_free" else "🔴 Занят"
    update_booster_status(callback.from_user.id, new_status)
    await callback.answer(f"Твой статус изменен на: {new_status}", show_alert=True)
    await callback.message.edit_text(f"🤖 Панель бустера:\n\nТвой текущий статус: {new_status}", reply_markup=booster_panel_kb())

# === АДМИН ПАНЕЛЬ ===
@dp.message(Command("admin"))
async def admin_panel_cmd(message: types.Message):
    if message.from_user.id in ADMIN_IDS:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 Управление ценами", callback_data="admin_prices")],
            [InlineKeyboardButton(text="👥 Управление бустерами", callback_data="admin_boosters")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")]
        ])
        await message.answer("👑 Добро пожаловать в Админ-панель DG | Boost!\nВыберите действие:", reply_markup=kb)

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS: return
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    users_count = cursor.fetchone()[0]
    conn.close()
    await callback.answer(f"Всего пользователей в боте: {users_count}", show_alert=True)

# Запуск бота
async def main():
    init_db()
    
    # Ваш ID привязан к вашей учетной записи бустера для проверки панели управления
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO boosters (user_id, username) VALUES (1928686265, '@exp1d')")
    cursor.execute("INSERT OR IGNORE INTO boosters (user_id, username) VALUES (2, '@BOP18rus')")
    cursor.execute("INSERT OR IGNORE INTO boosters (user_id, username) VALUES (3, '@GIBDDBLOODY')")
    conn.commit()
    conn.close()

    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())