-- Инициализация базы данных для погодной станции

-- Создание отдельной базы для Redash (метаданные)
CREATE DATABASE redash_db;

-- Таблица для хранения показаний погодной станции
CREATE TABLE IF NOT EXISTS weather_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    temperature DECIMAL(5,2) NOT NULL,        -- Температура в градусах Цельсия
    humidity DECIMAL(5,2) NOT NULL,           -- Влажность в процентах (0-100)
    pressure DECIMAL(7,2) NOT NULL,           -- Атмосферное давление в гПа (гектопаскалях)
    wind_speed DECIMAL(5,2) NOT NULL,         -- Скорость ветра в м/с
    wind_direction VARCHAR(10) NOT NULL,      -- Направление ветра (N, NE, E, SE, S, SW, W, NW)
    weather_condition VARCHAR(50) NOT NULL    -- Состояние погоды (Ясно, Облачно, Дождь и т.д.)
);

-- Индекс для быстрого поиска по времени
CREATE INDEX IF NOT EXISTS idx_weather_timestamp ON weather_data(timestamp);

-- Индекс для анализа по условиям погоды
CREATE INDEX IF NOT EXISTS idx_weather_condition ON weather_data(weather_condition);

-- Комментарии к таблице
COMMENT ON TABLE weather_data IS 'Показания погодной станции';
COMMENT ON COLUMN weather_data.temperature IS 'Температура воздуха в градусах Цельсия';
COMMENT ON COLUMN weather_data.humidity IS 'Относительная влажность воздуха в процентах';
COMMENT ON COLUMN weather_data.pressure IS 'Атмосферное давление в гектопаскалях';
COMMENT ON COLUMN weather_data.wind_speed IS 'Скорость ветра в метрах в секунду';
COMMENT ON COLUMN weather_data.wind_direction IS 'Направление ветра (N, NE, E, SE, S, SW, W, NW)';
COMMENT ON COLUMN weather_data.weather_condition IS 'Текущее состояние погоды';
