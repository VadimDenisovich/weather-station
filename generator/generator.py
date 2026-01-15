"""
Генератор данных погодной станции

Этот скрипт генерирует реалистичные показания погодной станции
и записывает их в базу данных PostgreSQL с заданной периодичностью.
"""

import os
import time
import random
import math
from datetime import datetime
from decimal import Decimal
import psycopg2
from psycopg2 import sql


# Конфигурация подключения к БД из переменных окружения
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'dbname': os.getenv('DB_NAME', 'weather_db'),
    'user': os.getenv('DB_USER', 'weather_user'),
    'password': os.getenv('DB_PASSWORD', 'weather_pass')
}

# Интервал генерации данных в секундах
GENERATION_INTERVAL = int(os.getenv('GENERATION_INTERVAL', 1))

# Направления ветра
WIND_DIRECTIONS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']

# Условия погоды с вероятностями (для реалистичности)
WEATHER_CONDITIONS = [
    ('Ясно', 0.25),
    ('Малооблачно', 0.20),
    ('Облачно', 0.20),
    ('Пасмурно', 0.15),
    ('Небольшой дождь', 0.10),
    ('Дождь', 0.05),
    ('Гроза', 0.03),
    ('Туман', 0.02)
]


class WeatherDataGenerator:
    """Класс для генерации реалистичных погодных данных"""
    
    def __init__(self):
        # Базовые значения для плавного изменения показаний
        self.base_temperature = random.uniform(15, 25)
        self.base_humidity = random.uniform(40, 70)
        self.base_pressure = random.uniform(1000, 1025)
        self.base_wind_speed = random.uniform(1, 5)
        self.current_direction_idx = random.randint(0, len(WIND_DIRECTIONS) - 1)
        self.time_counter = 0
        
    def _get_seasonal_factor(self):
        """Возвращает сезонный коэффициент на основе текущего времени"""
        hour = datetime.now().hour
        # Симуляция суточного цикла температуры
        # Максимум около 14:00, минимум около 4:00
        return math.sin((hour - 4) * math.pi / 12)
    
    def _weighted_choice(self, choices):
        """Выбор элемента с учётом весов"""
        total = sum(weight for _, weight in choices)
        r = random.uniform(0, total)
        upto = 0
        for choice, weight in choices:
            if upto + weight >= r:
                return choice
            upto += weight
        return choices[-1][0]
    
    def generate(self):
        """Генерирует одну запись погодных данных"""
        self.time_counter += 1
        seasonal_factor = self._get_seasonal_factor()
        
        # Температура: -10 до +35°C с плавным изменением
        temperature_variation = random.gauss(0, 0.5)
        self.base_temperature += temperature_variation * 0.1
        self.base_temperature = max(-10, min(35, self.base_temperature))
        temperature = round(self.base_temperature + seasonal_factor * 5 + random.gauss(0, 0.3), 2)
        
        # Влажность: 20-100% (обратная корреляция с температурой)
        humidity_variation = random.gauss(0, 1)
        self.base_humidity += humidity_variation * 0.2
        # При высокой температуре влажность обычно ниже
        humidity_adjustment = -seasonal_factor * 10
        self.base_humidity = max(20, min(100, self.base_humidity + humidity_adjustment * 0.1))
        humidity = round(self.base_humidity + random.gauss(0, 2), 2)
        humidity = max(20, min(100, humidity))
        
        # Давление: 980-1040 гПа с медленным изменением
        pressure_variation = random.gauss(0, 0.3)
        self.base_pressure += pressure_variation * 0.05
        self.base_pressure = max(980, min(1040, self.base_pressure))
        pressure = round(self.base_pressure + random.gauss(0, 0.5), 2)
        
        # Скорость ветра: 0-25 м/с с порывами
        wind_variation = random.gauss(0, 0.5)
        self.base_wind_speed += wind_variation * 0.1
        self.base_wind_speed = max(0, min(20, self.base_wind_speed))
        # Иногда порывы ветра
        gust = random.random() < 0.1
        wind_speed = round(self.base_wind_speed * (1.5 if gust else 1) + random.gauss(0, 0.3), 2)
        wind_speed = max(0, min(25, wind_speed))
        
        # Направление ветра: медленно меняется
        if random.random() < 0.05:  # 5% шанс изменения направления
            self.current_direction_idx = (self.current_direction_idx + random.choice([-1, 1])) % len(WIND_DIRECTIONS)
        wind_direction = WIND_DIRECTIONS[self.current_direction_idx]
        
        # Состояние погоды: зависит от давления и влажности
        if pressure < 1000 and humidity > 70:
            # Низкое давление и высокая влажность - вероятнее осадки
            weather_choices = [
                ('Пасмурно', 0.3),
                ('Небольшой дождь', 0.3),
                ('Дождь', 0.25),
                ('Гроза', 0.1),
                ('Туман', 0.05)
            ]
        elif pressure > 1020:
            # Высокое давление - хорошая погода
            weather_choices = [
                ('Ясно', 0.5),
                ('Малооблачно', 0.35),
                ('Облачно', 0.15)
            ]
        else:
            weather_choices = WEATHER_CONDITIONS
            
        weather_condition = self._weighted_choice(weather_choices)
        
        return {
            'temperature': temperature,
            'humidity': humidity,
            'pressure': pressure,
            'wind_speed': wind_speed,
            'wind_direction': wind_direction,
            'weather_condition': weather_condition
        }


def connect_to_db():
    """Создаёт подключение к базе данных с повторными попытками"""
    max_retries = 30
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            print(f"✓ Успешное подключение к базе данных на попытке {attempt + 1}")
            return conn
        except psycopg2.OperationalError as e:
            print(f"⏳ Попытка {attempt + 1}/{max_retries}: База данных недоступна. Ожидание {retry_delay} сек...")
            time.sleep(retry_delay)
    
    raise Exception("Не удалось подключиться к базе данных после всех попыток")


def insert_weather_data(conn, data):
    """Вставляет запись погодных данных в БД"""
    query = """
        INSERT INTO weather_data 
        (temperature, humidity, pressure, wind_speed, wind_direction, weather_condition)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, timestamp
    """
    
    with conn.cursor() as cur:
        cur.execute(query, (
            data['temperature'],
            data['humidity'],
            data['pressure'],
            data['wind_speed'],
            data['wind_direction'],
            data['weather_condition']
        ))
        result = cur.fetchone()
        conn.commit()
        return result


def main():
    """Основная функция генератора данных"""
    print("=" * 60)
    print("🌤️  Генератор данных погодной станции")
    print("=" * 60)
    print(f"Подключение к БД: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")
    print(f"Интервал генерации: {GENERATION_INTERVAL} сек")
    print("=" * 60)
    
    # Подключение к БД
    conn = connect_to_db()
    
    # Создание генератора
    generator = WeatherDataGenerator()
    
    records_count = 0
    
    try:
        print("\n📊 Начало генерации данных...\n")
        
        while True:
            # Генерация данных
            weather_data = generator.generate()
            
            # Вставка в БД
            record_id, timestamp = insert_weather_data(conn, weather_data)
            records_count += 1
            
            # Вывод информации
            print(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] "
                  f"ID:{record_id:6d} | "
                  f"🌡️ {weather_data['temperature']:+6.1f}°C | "
                  f"💧 {weather_data['humidity']:5.1f}% | "
                  f"📊 {weather_data['pressure']:7.1f} гПа | "
                  f"💨 {weather_data['wind_speed']:4.1f} м/с {weather_data['wind_direction']:2s} | "
                  f"☁️ {weather_data['weather_condition']}")
            
            # Периодический вывод статистики
            if records_count % 60 == 0:
                print(f"\n📈 Статистика: сгенерировано {records_count} записей\n")
            
            # Ожидание перед следующей генерацией
            time.sleep(GENERATION_INTERVAL)
            
    except KeyboardInterrupt:
        print(f"\n\n⚠️ Генератор остановлен. Всего записей: {records_count}")
    finally:
        conn.close()
        print("🔌 Соединение с БД закрыто")


if __name__ == "__main__":
    main()
