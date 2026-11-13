# Итоговый отчёт калибровочного прогона (`CALIBRATION-REPORT.md`)

- **Прогон**: `atlas-run-2026-11-12`
- **Версия конвейера и таксономии**: `LifeGame-Atlas-Hybrid-v2.1.1+lab.1` (`protocol_version: 2.1`, `taxonomy_version: 2.1`, `rubric_version: 2.1`)
- **Дата завершения калибровки**: `2026-11-12`

## 1. Что реально сделано и счётчики каждой стадии

Калибровочный прогон выполнен в точном соответствии с `CALIBRATION_START.md` и `FIRST_RUN.md` на реальных внешних источниках без синтетических заглушек и без выдумывания находок ради квоты:

| Стадия конвейера | Выходной артефакт / папка | Счётчики | Статус проверки (`atlas.py`) |
| :--- | :--- | :--- | :--- |
| **1. Поиск: `CAL-SEARCH-01`** (`C05, C08` — Захват и календарное планирование) | `accepted/CAL-SEARCH-01/attempt-001/` | **5** источников, **12** находок, **0** лидов | `validate`: `0` ошибок |
| **2. Поиск: `CAL-SEARCH-02`** (`C09, C12` — Нагрузка, энергия и возврат после срывов) | `accepted/CAL-SEARCH-02/attempt-001/` | **15** источников, **15** находок, **2** лида | `validate`: `0` ошибок |
| **3. Поиск: `CAL-SEARCH-03`** (`C21, C22` — Игровой прогресс, награды и экономики) | `accepted/CAL-SEARCH-03/attempt-001/` | **11** источников, **12** находок, **2** лида | `validate`: `0` ошибок |
| **4. Поиск: `CAL-SEARCH-04`** (`C28, C29` — Контроль данных, офлайн и восстановление) | `accepted/CAL-SEARCH-04/attempt-001/` | **5** источников, **11** находок, **0** лидов | `validate`: `0` ошибок |
| **5. Слияние входов (`merge`)** | `datasets/calibration-search-all4/` | **36** источников, **50** находок | `validate`: `0` ошибок |
| **6. Бюджетированное шардирование (`shard`)** | `shards/calibration-shards-50findings/` | **23** шарда (`max_records=15`, `max_bytes=120000`, `prompt_reserve_bytes=93896`), **2** части индекса | `0` потерь ID, `0` oversized |
| **7. Нормализация, дедупликация и анализ (`normalize + analyze`)** | `datasets/calibration-complete-v1/` | **49** элементов (`45` ранжируемых, `3` анти-паттерна, `1` составная система), **50** записей `merge_map`, **8** связей `relations` | `validate --complete`: `0` ошибок |
| **8. Стерилизация слепого пакета и двойная слепая оценка (`prepare-blind + rate`)** | `blind_packets/calibration_blind_elements.jsonl` + `ratings.jsonl` + `decisions.jsonl` | **45** стерилизованных карточек, **90** слепых оценок (`45 × 2`), **2** разрешённых расхождения (`spread=2`) | `validate --complete`: `0` ошибок |
| **9. Пробный расчёт и отбор (`rank`)** | `releases/calibration-pilot-v1/` | `eligible=45`, `selected=45`, `target_reached=false` (ожидаемо при цели `200`), `anti_patterns_cataloged=3` | `rank`: `0` ошибок |
| **10. Криптографическая опечатка (`seal + verify`)** | `BUNDLE_MANIFEST.json` | Полная побайтовая проверка SHA-256 всех файлов прогона | `verify`: `0` ошибок |

## 2. Пойманные ошибки и потери внешних исполнителей (`arena.ai`)

В ходе совместного прогона пакетов `CAL-SEARCH-03` (2 модели на `arena.ai`) и `CAL-SEARCH-02` (4 модели в 2 батлах на `arena.ai`) приёмочный фильтр `SYSTEM.md` выявил три типовые проблемы внешних поисковых моделей:

1. **Угадывание URL-путей (slug-guessing) по реальным заголовкам статей**:
   - В `CAL-SEARCH-03` Модель A выдала вымышленный URL `https://gamescrye.com/2025/05/31/progression-design-that-avoids-the-grind/` вместо реального `https://gamescrye.com/blog/designing-a-progression-focused-game-without-the-grind/` и усекла путь `https://appscale.blog/en/blog/game-economy-sinks-faucets-inflation-design-2026`.
   - В `CAL-SEARCH-02` Модель 1 выдала `https://blog.duolingo.com/streak-freezes/` и `https://www.morgen.so/blog/minimum-viable-day` вместо реальных `https://blog.duolingo.com/protecting-streaks-from-site-issues/` и `https://www.morgen.so/blog-posts/sometimes-we-all-need-a-minimum-viable-day`.
   - **Решение**: Все URL проверялись оркестратором через поиск; подтверждённые статьи привязаны к их точным каноническим URL, а неподтверждённые ссылки отсеяны в `leads.jsonl` (оригиналы ответов сохранены в `incoming/`).
2. **Редирект-ссылки поисковых прокси (`vertexaisearch.cloud.google.com/grounding-api-redirect/...`)**:
   - В `CAL-SEARCH-02` Модель 4 вернула 11 качественных источников, но вместо прямых URL подставила временные ссылки редиректа Vertex Grounding API.
   - **Решение**: Оркестратор раскрыл редиректы по точным заголовкам и владельцам доменов (`keypup.io`, `envisionadhd.com`, `goalsandprogress.com`, `incitefulmed.com`, `morgen.so`) до постоянных канонических URL.
3. **Самодеятельность в кодах таксономии до включения шпаргалки enum-кодов в промпт**:
   - В `CAL-SEARCH-03` (без встроенного списка кодов в коротком промпте) обе модели выдумали свои коды (`F8_RECOVERY_PENALTY`, `F5_VALUE_AMBIGUITY`, `workflow`, `metric`), что сразу поймал `atlas.py validate`.
   - После добавления в промпт `CAL-SEARCH-02` явного перечня допустимых значений `kind`, `domain_code`, `phase_code` и `primary_friction_code`, **все 4 модели в двух батлах выдали 100% валидные коды с нуля (`0` ошибок схемы)**.

## 3. Проверка дедупликации, связей и слепой оценки

- **Глобальная дедупликация (`merge_map.jsonl`)**:
  - Находки `F-CAL02-003` (клиническое описание цикла *Push-and-Crash* от CDC) и `F-CAL02-015` (поведенческое исследование *Post-Lapse Overexertion of Self-Control* от Jenkins et al.) объединены в единый канонический анти-паттерн `E-CAL-015` (`decision: "canonical"` + `decision: "merged_variant"`), опирающийся сразу на два независимых источника (`S-CAL02-002` и `S-CAL02-015`).
  - Составная система `F-CAL02-009` (*Трёхуровневый режим дня «Золото / Серебро / Бронза»*, `kind: "method_system"`) оформлена со статусом `decision: "composite"` и связана отношениями `contains` (`REL-CAL-001`, `REL-CAL-002`) со своими атомарными компонентами (`E-CAL-021` *Tiny Habits Starter Step* и `E-CAL-008` *Flexible Time Buckets*).
- **Двойная слепая оценка и арбитраж расхождений (`ratings.jsonl` + `decisions.jsonl`)**:
  - Все 45 ранжируемых элементов прошли через стерилизацию `prepare-blind` и получили по две независимые слепые оценки (`cal-rater-A` и `cal-rater-B`).
  - По двум элементам (`E-CAL-004` *Flexible Defended Calendar Habits* и `E-CAL-024` *Sink-First Economy Design*) зафиксировано расхождение в 2 балла по критерию `burden` (оценка 4 за автоматизм в рутине против оценки 2 за сложность первичной настройки правил). Оба случая штатно перехвачены проверкой `find_disagreeing_reviewers` и закрыты мотивированными записями `rating_resolution` в `decisions.jsonl`.

## 4. Проверка бюджетирования шардов (`--prompt-reserve-bytes`)

- Суммарный объём передаваемых инструкций (`PROMPTS/02-ANALYZE.md` + `DATA_CONTRACT.md` + `TAXONOMY.md` + `taxonomy.json` + `SCORING.md`) составил **85 896 байт**.
- С учётом запаса в **8 000 байт** на обёртку `TASK.json` установлен параметр `--prompt-reserve-bytes 93896` при потолке пакета `--max-bytes 120000` (чистый бюджет на `findings + deduplicated sources` внутри одного шарда — до **26 104 байт**).
- Результат `atlas.py shard`: 50 находок автоматически разбиты на **23 шарда** (максимум 9 записей и **114 490 байт** полного пакета вместе с промптом и источниками), `oversized_records_count = 0`, навигационный индекс уложен в **2 части** по лимиту `30 000 байт`.

## 5. Узкие исправления перед массовой волной (по всем 32 категориям)

Архитектура и код `atlas.py` (`2.1.1+lab.1`) отработали без единого сбоя. Для перехода к массовой волне зафиксированы 3 операционных правила в шаблонах пасты (`outbound_packets/`):
1. **Всегда включать компактный блок допустимых enum-кодов** (`kind`, `domain_code`, `phase_code`, `primary_friction_code`, `source_type`) прямо в текст промпта для внешних моделей — это полностью обнуляет ошибки классификации на входе.
2. **Запрещать редирект-ссылки прокси** (`vertexaisearch.cloud.google.com`, `google.com/url`) строкой в промпте и автоматически резолвить их на приёмке через поиск по `title + owner`.
3. **Использовать расчётный резерв `--prompt-reserve-bytes 94000`** при шардировании массовой волны на бюджет пакета `120 000 байт`.
