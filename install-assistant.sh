#!/bin/bash

set -e

echo "[1/5] Клонируем репозиторий..."
git clone https://github.com/byagge/assistant.git assistant_project
cd assistant_project

echo "[2/5] Перемещаем Main.py в папку assistant/"
mkdir -p assistant
mv Main.py assistant/

echo "[3/5] Создаем и активируем виртуальное окружение..."
python3 -m venv env
source env/bin/activate

echo "[4/5] Устанавливаем зависимости..."
cat > requirements.txt << EOF
aiohappyeyeballs==2.6.1
aiohttp==3.11.18
aiosignal==1.3.2
attrs==25.3.0
Brotli==1.1.0
certifi==2025.4.26
charset-normalizer==3.4.2
frozenlist==1.6.0
g4f==0.5.2.4
idna==3.10
multidict==6.4.3
nest-asyncio==1.6.0
propcache==0.3.1
pycryptodome==3.22.0
pyTelegramBotAPI==4.27.0
python-dateutil==2.9.0.post0
requests==2.32.3
schedule==1.2.2
six==1.17.0
telebot==0.0.5
urllib3==2.4.0
yarl==1.20.0
EOF

pip install --upgrade pip
pip install -r requirements.txt

echo "[5/5] Запускаем бота..."
python assistant/Main.py
