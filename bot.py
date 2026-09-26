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

# === СОСТОЯНИЯ ===
class AdminStates(StatesGroup):
    waiting_for_broadcast = State()
    waiting_for_price_text = State()
    waiting_for_booster_id = State()
    waiting_for_booster_username = State()
    waiting_for_del_booster_id = State()

class OrderStates(StatesGroup):
    waiting_for_payment = State()
    waiting_for_game_id = State()
    waiting_for_confirmation = State()

# === БАЗА ДАННЫХ ===
def init_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS boosters (
                        user_id INTEGER PRIMARY KEY, 
                        username TEXT, 
                        status TEXT DEFAULT '🟢 Свободен')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    
    default_rank = (
        "⚡️ <b>Прайс на буст звания:</b>\n\n"
        "🥈 Bronze - Silver: 25₽\n"
        "🏅 Bronze - Gold: 75₽\n"
        "🐥 Bronze - Phoenix: 150₽\n"
        "🔫 Bronze - Ranger: 200₽\n"
        "🏆 Bronze - Champion: 360₽\n"
        "🥋 Bronze - Master: 400₽\n"
        "⚜️ Bronze - Elite: 600₽\n"
        "🌏 Bronze - Legend: 1000₽"
    )
    default_silver = "⚡️ <b>Прайс за буст/фарм серебра:</b>\n\n🪙 1.000 Серебра — 200₽"
    default_level = "⚡️ <b>Прайс за буст уровня:</b>\n\n📶 1 Уровень — 10₽"
    
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('price_rank', ?)", (default_rank,))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('price_silver', ?)", (default_silver,))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('price_level', ?)", (default_level,))
    
    conn.commit()
    conn.close()

def get_setting(key):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else "Текст не установлен."

def set_setting(key, value):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value = ? WHERE key = ?", (value, key))
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    res = cursor.fetchall()
    conn.close()
    return [row[0] for row in res]

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
        [InlineKeyboardButton(text="📄 Правила и Соглашение", callback_data="rules"),
         InlineKeyboardButton(text="🤝 Поддержка", callback_data="support")]
    ])

def services_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Буст звания", callback_data="boost_rank")],
        [InlineKeyboardButton(text="🪙 Буст Серебра", callback_data="boost_silver")],
        [InlineKeyboardButton(text="📶 Буст уровня", callback_data="boost_level")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ])

def order_payment_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Напрямую через Владельца", callback_data="paym_Direct")],
        [InlineKeyboardButton(text="💳 FunPay", callback_data="paym_FunPay")],
        [InlineKeyboardButton(text="🎮 Playerok", callback_data="paym_Playerok")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_order")]
    ])

def final_confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Заказать", callback_data="submit_order")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_order")]
    ])

def booster_panel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Поставить статус 'Свободен'", callback_data="status_free")],
        [InlineKeyboardButton(text="🔴 Поставить статус 'Занят'", callback_data="status_busy")]
    ])

def admin_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Управление ценами", callback_data="admin_prices")],
        [InlineKeyboardButton(text="👥 Управление бустерами", callback_data="admin_boosters")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")]
    ])

# === КЛИЕНТСКИЕ КОМАНДЫ ===
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    add_user(message.from_user.id)
    await message.answer("Привет! Добро пожаловать в официальный бот DG | Boost Standoff ⚡️\nЗдесь ты можешь оформить заказ в пару кликов!", reply_markup=main_menu_kb())

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Главное меню 👇", reply_markup=main_menu_kb())

@dp.callback_query(F.data == "services")
async def show_services(callback: types.CallbackQuery):
    await callback.message.edit_text("Выберите категорию услуг:", reply_markup=services_menu_kb())

@dp.callback_query(F.data == "boost_rank")
async def show_rank_prices(callback: types.CallbackQuery):
    text = get_setting('price_rank')
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать заказ", callback_data="confirm_Звания")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="services")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data == "boost_silver")
async def show_silver_prices(callback: types.CallbackQuery):
    text = get_setting('price_silver')
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать заказ", callback_data="confirm_Серебра")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="services")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data == "boost_level")
async def show_level_prices(callback: types.CallbackQuery):
    text = get_setting('price_level')
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать заказ", callback_data="confirm_Уровня")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="services")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

# === ОФОРМЛЕНИЕ ЗАКАЗА В БОТЕ ===
@dp.callback_query(F.data.startswith("confirm_"))
async def start_other_order(callback: types.CallbackQuery, state: FSMContext):
    service_type = callback.data.split("_")[1]
    await state.update_data(service=service_type)
    await callback.message.edit_text(f"Вы выбрали: Буст {service_type}.\nКак будет происходить оплата?", reply_markup=order_payment_kb())
    await state.set_state(OrderStates.waiting_for_payment)

@dp.callback_query(OrderStates.waiting_for_payment, F.data.startswith("paym_"))
async def process_payment_method(callback: types.CallbackQuery, state: FSMContext):
    payment_map = {"Direct": "Владельцу", "FunPay": "FunPay", "Playerok": "Playerok"}
    await state.update_data(payment_method=payment_map[callback.data.split("_")[1]])
    await callback.message.edit_text("Отправьте ваш игровой ID (В Standoff 2):")
    await state.set_state(OrderStates.waiting_for_game_id)

@dp.message(OrderStates.waiting_for_game_id)
async def process_game_id(message: types.Message, state: FSMContext):
    await state.update_data(game_id=message.text)
    data = await state.get_data()
    text = f"🛒 Услуга: Буст {data['service']}\n💳 Оплата: {data['payment_method']}\n🎮 ID: {data['game_id']}\n\nВсё верно?"
    await message.answer(text, reply_markup=final_confirm_kb())
    await state.set_state(OrderStates.waiting_for_confirmation)

@dp.callback_query(OrderStates.waiting_for_confirmation, F.data == "submit_order")
async def submit_order(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    username = f"@{callback.from_user.username}" if callback.from_user.username else callback.from_user.first_name
    admin_text = f"🔥 <b>Новый заказ!</b>\n👤 От: {username}\n🛒 Услуга: Буст {data['service']}\n🎮 ID: <code>{data['game_id']}</code>\n💳 Оплата: {data['payment_method']}"
    admin_order_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принять", callback_data=f"ord_acc_{callback.from_user.id}"),
         InlineKeyboardButton(text="❌ Отказать", callback_data=f"ord_rej_{callback.from_user.id}")]
    ])
    
    for admin_id in ADMIN_IDS:
        try: await bot.send_message(admin_id, admin_text, reply_markup=admin_order_kb, parse_mode="HTML")
        except: pass
            
    await callback.message.edit_text("✅ Заказ отправлен на проверку!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В меню", callback_data="back_to_main")]]))
    await state.clear()

@dp.callback_query(F.data == "cancel_order")
async def cancel_order(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Заказ отменен.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В меню", callback_data="back_to_main")]]))

# === ПРИНЯТИЕ/ОТКЛОНЕНИЕ ЗАКАЗА (С САЙТА ИЛИ ИЗ БОТА) ===
@dp.callback_query(F.data.startswith("ord_acc_"))
async def accept_order_handler(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS: return
    client_id = int(callback.data.split("_")[2])
    await callback.message.edit_text(f"{callback.message.html_text}\n\n<b>[✅ ЗАКАЗ ПРИНЯТ]</b>", parse_mode="HTML", reply_markup=None)
    try:
        if client_id != 0: # Если ID 0 - заказ с сайта без привязки Telegram ID
            await bot.send_message(client_id, "Приветствую! Недавно вы делали заказ буста аккаунта в игре Standoff 2. Администратор полностью изучил указанную информацию и принялся за заказ! Скоро вам отпишут сотрудники команды.")
        await callback.answer("Принято!")
    except:
        await callback.answer("Заказ принят, но ЛС клиента закрыты.")

@dp.callback_query(F.data.startswith("ord_rej_"))
async def reject_order_handler(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS: return
    client_id = int(callback.data.split("_")[2])
    await callback.message.edit_text(f"{callback.message.html_text}\n\n<b>[❌ ОТМЕНЕН]</b>", parse_mode="HTML", reply_markup=None)
    try:
        if client_id != 0:
            await bot.send_message(client_id, "К сожалению, ваш заказ был отклонен администратором.")
    except: pass

# === ИНФОБЛОКИ ===
@dp.callback_query(F.data == "boosters_status")
async def show_boosters_status(callback: types.CallbackQuery):
    boosters = get_boosters()
    text = "🕘 Загруженность команды:\n\n" + ("\n".join([f"👤 {u} — {s}" for u, s in boosters]) if boosters else "Нет данных.")
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]]))

@dp.callback_query(F.data == "rules")
async def show_rules(callback: types.CallbackQuery):
    text = "📜 <b>Правила:</b>\n1. Гарантируем конфиденциальность.\n2. Не заходить на аккаунт во время буста.\n3. Возврат только до начала работы."
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]]), parse_mode="HTML")

@dp.callback_query(F.data == "support")
async def show_support(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Поддержка", url=f"https://t.me/{OWNER_USERNAME.replace('@', '')}")], [InlineKeyboardButton(text="Назад", callback_data="back_to_main")]])
    await callback.message.edit_text("Напишите нашему администратору.", reply_markup=kb)

# === ПАНЕЛЬ БУСТЕРА ===
@dp.message(Command("bpanel"))
async def booster_panel_cmd(message: types.Message):
    await message.answer("🤖 Панель бустера:", reply_markup=booster_panel_kb())

@dp.callback_query(F.data.startswith("status_"))
async def change_status(callback: types.CallbackQuery):
    new_status = "🟢 Свободен" if callback.data == "status_free" else "🔴 Занят"
    update_booster_status(callback.from_user.id, new_status)
    await callback.message.edit_text(f"🤖 Панель бустера:\nТвой статус: {new_status}", reply_markup=booster_panel_kb())

# === АДМИН ПАНЕЛЬ ===
@dp.message(Command("admin"))
async def admin_panel_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    if message.from_user.id in ADMIN_IDS:
        await message.answer("👑 Админ-панель:", reply_markup=admin_main_kb())

@dp.callback_query(F.data == "admin_prices")
async def admin_prices_menu(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Звания", callback_data="editprice_price_rank")],
        [InlineKeyboardButton(text="🪙 Серебро", callback_data="editprice_price_silver")],
        [InlineKeyboardButton(text="📶 Уровень", callback_data="editprice_price_level")]
    ])
    await callback.message.edit_text("Выберите категорию:", reply_markup=kb)

@dp.callback_query(F.data.startswith("editprice_"))
async def edit_price_start(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(editing_key=callback.data.split("editprice_")[1])
    await callback.message.edit_text("Отправьте новый прайс (можно с HTML):")
    await state.set_state(AdminStates.waiting_for_price_text)

@dp.message(AdminStates.waiting_for_price_text)
async def save_new_price(message: types.Message, state: FSMContext):
    data = await state.get_data()
    set_setting(data['editing_key'], message.text)
    await message.answer("✅ Прайс обновлен в боте!")
    await state.clear()

@dp.callback_query(F.data == "admin_boosters")
async def admin_boosters_menu(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить", callback_data="add_booster"), InlineKeyboardButton(text="➖ Удалить", callback_data="del_booster")],
        [InlineKeyboardButton(text="📋 Список", callback_data="list_boosters")]
    ])
    await callback.message.edit_text("Управление бустерами:", reply_markup=kb)

@dp.callback_query(F.data == "list_boosters")
async def list_boosters_admin(callback: types.CallbackQuery):
    boosters = get_boosters()
    text = "📋 Бустеры:\n" + ("\n".join([f"{u}" for u, s in boosters]) if boosters else "Пусто.")
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="admin_boosters")]]))

@dp.callback_query(F.data == "add_booster")
async def add_booster_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Отправьте ID:")
    await state.set_state(AdminStates.waiting_for_booster_id)

@dp.message(AdminStates.waiting_for_booster_id)
async def add_booster_id(message: types.Message, state: FSMContext):
    await state.update_data(new_booster_id=int(message.text))
    await message.answer("Отправьте @username:")
    await state.set_state(AdminStates.waiting_for_booster_username)

@dp.message(AdminStates.waiting_for_booster_username)
async def add_booster_username(message: types.Message, state: FSMContext):
    data = await state.get_data()
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO boosters (user_id, username) VALUES (?, ?)", (data['new_booster_id'], message.text))
    conn.commit()
    conn.close()
    await message.answer("✅ Добавлен!")
    await state.clear()

@dp.callback_query(F.data == "del_booster")
async def del_booster_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Отправьте ID для удаления:")
    await state.set_state(AdminStates.waiting_for_del_booster_id)

@dp.message(AdminStates.waiting_for_del_booster_id)
async def del_booster_id(message: types.Message, state: FSMContext):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM boosters WHERE user_id = ?", (int(message.text),))
    conn.commit()
    conn.close()
    await message.answer("✅ Удален!")
    await state.clear()

async def main():
    init_db()
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO boosters (user_id, username) VALUES (1928686265, '@exp1d')")
    conn.commit()
    conn.close()

    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())