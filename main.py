# motivational_bot_g4f.py
"""
Telegram-бот для мотивации с AI-поддержкой (g4f) и интеграцией Todoist через REST API.
Расширенный функционал:
- Анализ продуктивности по вечернему отчету с AI-оценкой
- Три стиля мотивации: жесткий, дружелюбный, аналитический
- Команды /status и /help
- Логирование всех сообщений и метрик в JSON-файл
"""
import os
import time
import schedule
import requests
import json
import random
from datetime import datetime, date
from dateutil import parser as date_parser

import telebot
from g4f.client import Client

# === Настройки ===
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TODOIST_TOKEN   = os.getenv('TODOIST_TOKEN')
CHAT_ID         = 6791533117
LOG_FILE        = os.getenv('LOG_FILE', 'bot_log.json')

# Инициализация
bot = telebot.TeleBot(TELEGRAM_TOKEN)
llm = Client(verify=False)

# Загрузить или инициализировать лог
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        log_data = json.load(f)
else:
    log_data = {'messages': [], 'daily_reports': {}}

# Стили мотивации
STYLES = {
    'hard': '🥵 Жесткая мотивация:',
    'soft': '☕️ Дружелюбная поддержка:',
    'analytic': '📊 Аналитическая мотивация:'
}

# === Вспомогательные функции ===

def log_event(event_type: str, content: str):
    entry = {'time': datetime.now().isoformat(), 'type': event_type, 'content': content}
    log_data['messages'].append(entry)
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)


def generate_message(prompt: str) -> str:
    resp = llm.chat.completions.create(
        model='gpt-4o',
        messages=[{'role': 'user', 'content': prompt}]
    )
    return resp.choices[0].message.content.strip()


def fetch_todo_count_for_today() -> int:
    """Подсчет задач на сегодня через REST API Todoist."""
    url = "https://api.todoist.com/rest/v2/tasks"
    headers = {"Authorization": f"Bearer {TODOIST_TOKEN}"}
    r = requests.get(url, headers=headers)
    tasks = r.json() if r.status_code == 200 else []
    today = date.today()
    return sum(1 for t in tasks if t.get('due') and date_parser.parse(t['due']['date']).date() == today)

# === Рассылки ===

def choose_style() -> str:
    return random.choice(list(STYLES.keys()))


def send_morning_message():
    count = fetch_todo_count_for_today()
    style = choose_style()
    prompt = (
        f"Доброе утро! Сегодня у тебя {count} задач в Todoist. "
        "Начни день эффективно: сосредоточься на главном и действуй!"
    )
    ai_text = generate_message(prompt)
    text = f"{STYLES[style]}\n{ai_text}"
    bot.send_message(CHAT_ID, text)
    log_event('morning', text)


def send_periodic_motivation():
    now = datetime.now().strftime('%H:%M')
    style = choose_style()
    prompt = (f"Сейчас {now}. Поддержи пользователя: напомни ему сохранять фокус и избегать прокрастинации.")
    ai_text = generate_message(prompt)
    text = f"{STYLES[style]}\n{ai_text}"
    bot.send_message(CHAT_ID, text)
    log_event('periodic', text)


def send_evening_report_prompt():
    prompt = (
        "Пора подвести итоги дня: попроси пользователя рассказать, что он сделал сегодня, "
        "какие успехи и наметки задач на завтра."
    )
    ai_text = generate_message(prompt)
    text = f"🌙 Вечерний отчёт:\n{ai_text}"
    bot.send_message(CHAT_ID, text)
    log_event('evening_prompt', text)

# === Обработка отчёта дня ===
@bot.message_handler(func=lambda m: m.text and m.text.startswith('Отчёт:'))
def handle_daily_report(message):
    report = message.text.replace('Отчёт:', '').strip()
    date_key = date.today().isoformat()
    # AI-оценка отчёта
    prompt = f"Оцени продуктивность по этому отчету: {report}"
    evaluation = generate_message(prompt)
    reply = f"Спасибо за отчёт! Моя оценка: {evaluation}"
    bot.send_message(message.chat.id, reply)
    # Сохранить
    log_data['daily_reports'][date_key] = {'report': report, 'evaluation': evaluation}
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    log_event('daily_report', report)

# === Telegram команды ===
@bot.message_handler(commands=['status'])
def cmd_status(message):
    count = fetch_todo_count_for_today()
    text = f"У вас {count} задач на сегодня. Держим курс на выполнение!"
    bot.send_message(message.chat.id, text)
    log_event('command', '/status')

@bot.message_handler(commands=['help'])
def cmd_help(message):
    text = (
        "/status — текущее количество задач\n"
        "/help — список команд\n"
        "Присылайте отчёт, начиная сообщение с 'Отчёт:'"
    )
    bot.send_message(message.chat.id, text)
    log_event('command', '/help')

# === Планировщик расписания ===

def send_goodnight_message():
    """
    Вечернее сообщение перед сном
    """
    prompt = (
        "Спокойной ночи, капитан. Вы сегодня отлично поработали! "
        "Отдыхайте, а завтра продолжим."
    )
    ai_text = generate_message(prompt)
    text = f"🌙 Спокойной ночи:
{ai_text}"
    bot.send_message(CHAT_ID, text)
    log_event('goodnight', text)


def schedule_jobs():
    schedule.every().day.at("08:30").do(send_morning_message)
    schedule.every().day.at("11:30").do(send_periodic_motivation)
    schedule.every().day.at("14:30").do(send_periodic_motivation)
    schedule.every().day.at("17:30").do(send_periodic_motivation)
    schedule.every().day.at("20:00").do(send_evening_report_prompt)
    schedule.every().day.at("21:30").do(send_goodnight_message)

# === Запуск ===
if __name__ == '__main__':
    schedule_jobs()
    # поток для расписания
    def run_schedule():
        while True:
            schedule.run_pending()
            time.sleep(30)

    import threading
    threading.Thread(target=run_schedule, daemon=True).start()

    print("🤖 AI мотивационный бот запущен. Ожидаю сообщений и расписание...")
    bot.infinity_polling()
