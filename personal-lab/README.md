# LifeGame Lab

Для основной модели и другого аккаунта: [точка входа и ветка передачи](../LABORATORY_HANDOFF.md). В Git подготовлен [компактный набор доказательств](evidence/month-pilot-001/INDEX.md) с [переносимым анализом](evidence/month-pilot-001/REVIEW.md); он отличается от полного локального verification/. Для проверки: `python3 personal-lab/evidence/verify.py`. Статус отправки — в квитанции передачи после проверки GitHub.

Копия **Personal 1.2.0** для согласованных улучшений в этом чате и продолжения с другого аккаунта. Первая задача — LAB-000: создание копии и правил работы. Новые продуктовые функции пока не добавлены.

[Точка подключения и схема работы](../docs/DEVELOPMENT_HANDOFF.md) · [Журнал изменений](CHANGELOG.md) · [Исходный срез и хеши](BASELINE.json) · [Правила помощника](AGENTS.md)

Основная версия остаётся в `personal/`. История решений исходной Personal — [DECISIONS.md](../personal/DECISIONS.md), устройство — [README.md](../personal/README.md). Старые результаты публикации и приёмки не означают публикацию или приёмку лаборатории.

## Отличия копии

- В заголовке приложения, вкладке и PWA — LifeGame Lab.
- Ключи браузера: `lifegame-personal-lab-meta-v1`, `lifegame-personal-lab-my-v1`, `lifegame-personal-lab-demo-v1`; копии данных используют соответствующие `-last-good` и `-daily`.
- Собственные Web Lock, имя офлайн-кэша и service worker в scope папки. Данные основной Personal автоматически не подхватываются.
- Механики, награды и формат ручного импорта/экспорта `personal-1`/v2 сохранены. Это совместимость исходного среза, а не обещание совместимости будущих версий.

## Запуск и проверки

Из корня репозитория:

```sh
python3 -m http.server 8041 --bind 127.0.0.1
```

Путь приложения на этом сервере — `/personal-lab/`. Сборка и backend не нужны. После восстановления облачной машины сервер нужно запустить заново.

В другой сессии, из того же корня, последовательно:

```sh
python3 personal-lab/tests/browser.py
python3 personal-lab/tests/update-live.py
python3 personal-lab/tests/locations-live.py
python3 personal-lab/tests/offline.py
python3 personal-lab/tests/isolation.py
```

Нужны Python Playwright и `/usr/bin/chromium`. Сценарии используют вымышленные данные и временные контексты, блокируют внешние запросы. Последние два сами запускают временные HTTP-серверы. Отчёты и снимки находятся в игнорируемой `verification/`. Для LAB-000 прошли 118/118 групп; подробные результаты и ограничения фиксируются в CHANGELOG.

## Продолжение с другого аккаунта

Нужен доступ к репозиторию и коммиту с лабораторией. Прочитать документ передачи и журнал, сверить Git и продолжить здесь. Автоматического переноса между аккаунтами или в основную Personal нет. Пользовательские сохранения остаются в конкретном браузере и origin.

Лаборатория пока подготовлена локально; отправка в Git и публикация в рамках LAB-000 не выполнялись.

## LAB-002: цифровые пользователи

[Протокол и сравнение трёх вариантов](research/LAB-002-digital-month/PROTOCOL.md) · [Фактический пилот 3 × 7](research/LAB-002-digital-month/RESULTS.md) · [Независимый UX-анализ](research/LAB-002-digital-month/ANALYSIS.md) · [Масштабирование на 16 × 30](research/LAB-002-digital-month/SCALE.md).

Готовые задания: [инженеру/оркестратору](research/LAB-002-digital-month/PROMPT-RUNNER.md), [отдельному пользователю](research/LAB-002-digital-month/PROMPT-USER.md), [для независимых вариантов Arena](research/LAB-002-digital-month/PROMPT-ARENA.md). Команды исполняемого стенда — [README-DRIVER.md](research/LAB-002-digital-month/README-DRIVER.md). Исходные артефакты в игнорируемой verification/. Месячный опыт пока не выполнен; код приложения не менялся.
