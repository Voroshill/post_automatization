-- Оптимизация базы данных для работы с 10,000+ записей
-- Выполнить после создания таблиц

-- 1. Создание индексов для быстрой курсорной пагинации
CREATE INDEX IF NOT EXISTS idx_users_status_id ON users(status, id);
CREATE INDEX IF NOT EXISTS idx_users_id ON users(id);

-- 2. Индексы для поиска
CREATE INDEX IF NOT EXISTS idx_users_firstname ON users(firstname);
CREATE INDEX IF NOT EXISTS idx_users_secondname ON users(secondname);
CREATE INDEX IF NOT EXISTS idx_users_unique_id ON users(unique_id);
CREATE INDEX IF NOT EXISTS idx_users_mobile_phone ON users(mobile_phone);
CREATE INDEX IF NOT EXISTS idx_users_work_phone ON users(work_phone);
CREATE INDEX IF NOT EXISTS idx_users_company ON users(company);
CREATE INDEX IF NOT EXISTS idx_users_department ON users(department);
CREATE INDEX IF NOT EXISTS idx_users_otdel ON users(otdel);
CREATE INDEX IF NOT EXISTS idx_users_appointment ON users(appointment);

-- 3. Составные индексы для сложных запросов
CREATE INDEX IF NOT EXISTS idx_users_status_search ON users(status, firstname, secondname);
CREATE INDEX IF NOT EXISTS idx_users_upload_date ON users(upload_date);

-- 4. Индексы для фильтрации по статусу
CREATE INDEX IF NOT EXISTS idx_users_pending ON users(id) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_users_dismissed ON users(id) WHERE status = 'dismissed';
CREATE INDEX IF NOT EXISTS idx_users_approved ON users(id) WHERE status = 'approved';
CREATE INDEX IF NOT EXISTS idx_users_rejected ON users(id) WHERE status = 'rejected';

-- 5. Оптимизация для SQLite (если используется)
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 268435456;

-- 6. Анализ статистики для оптимизатора запросов
ANALYZE;

-- 7. Создание представлений для часто используемых запросов
CREATE VIEW IF NOT EXISTS v_pending_users AS
SELECT * FROM users WHERE status = 'pending' ORDER BY id;

CREATE VIEW IF NOT EXISTS v_dismissed_users AS
SELECT * FROM users WHERE status = 'dismissed' ORDER BY id;

-- 8. Индексы для внешних ключей (если есть)
-- CREATE INDEX IF NOT EXISTS idx_users_boss_id ON users(boss_id);

-- 9. Оптимизация для поиска по тексту (если поддерживается)
-- CREATE INDEX IF NOT EXISTS idx_users_fulltext ON users USING gin(to_tsvector('russian', firstname || ' ' || secondname || ' ' || COALESCE(thirdname, '')));

-- 10. Настройки для PostgreSQL (если используется)
-- ALTER TABLE users SET (fillfactor = 90);
-- VACUUM ANALYZE users;
