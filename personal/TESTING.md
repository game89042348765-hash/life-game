# Проверки Personal после выборочного переноса 1.1.0

11 ноября 2026. Только вымышленные данные, отдельные Chromium-контексты, локальный сервер; внешние запросы тестового браузера блокировались. Реальные сохранения пользователя не читались/не очищались.

**68/68 групп модели/UI, 2/2 групп живой смены локаций и 6/6 групп PWA прошли.**

## Модель и сквозной интерфейс

- Empty personal state and isolated keys — PASS.
- Exact reward reversal after editing reward — PASS.
- Double completion and double undo are refused — PASS.
- Constructor can be switched off (false result is not rollback) — PASS.
- Key star toggles both ways — PASS.
- Independent key and final explicit inDay off in editor — PASS.
- Repeat to once starts a new cycle — PASS.
- Completed calendar date cannot move, form survives — PASS.
- Goal/habit threshold and parent undo — PASS.
- Undo earlier habit tick also reverses dependent threshold — PASS.
- Habit is limited to one tick per day — PASS.
- Quest final and undo earlier step — PASS.
- Checklist distinct identical names retain IDs — PASS.
- Started quest cannot change its type — PASS.
- Completed quest target is protected — PASS.
- Bonus assignment has immutable terms — PASS.
- One-use reserve restores after undo — PASS.
- Used reward blocks whole completion undo — PASS.
- Purchase snapshot, one use and repeated use refused — PASS.
- Refund is exact and idempotent — PASS.
- Cannot undo coins already spent — PASS.
- Price word voluntary debt and exact compensation — PASS.
- Archived blocks and closed stages remove actionable items — PASS.
- Editing an archived link keeps its stage and goal — PASS.
- Stage closure moves task IDs containing underscores — PASS.
- Midnight rollover happens before completion mutation — PASS.
- Rest hides ordinary actions without a miss; calendar remains — PASS.
- Quota failure rolls back facts and ledger, retains durable data — PASS.
- Last-good copy is valid previous commit — PASS.
- Invalid import does not overwrite anything — PASS.
- Malicious HTML titles are rendered as text — PASS.
- Timer log is not repeatable — PASS.
- Focus hides another block without manufacturing a miss — PASS.
- Bonus bought without enough money is refused — PASS.
- Old Claude JSON can upgrade assignment snapshots — PASS.
- Broken preferences, references and prototype keys are rejected — PASS.
- Backup write failure refuses the whole operation — PASS.
- Goal can be abandoned and reactivated without money — PASS.
- Custom block deletion preserves linked actions and reward history — PASS.
- Habit level UI restores committed data after write failure — PASS.
- Locations: legacy personal v2 upgrades without changing facts or balances — PASS.
- Locations: manual choice without a schedule persists without artificial expiry — PASS.
- Locations: overnight weekday belongs to starting day — PASS.
- Locations: manual expiry waits for an actual weekday change — PASS.
- Locations: overlapping inactive boundaries do not interrupt manual choice — PASS.
- Locations: place and profile block filter keep universal tasks and forced actions — PASS.
- Locations: hidden section does not remove actions from the plan — PASS.
- Locations: no-miss rule uses the historical daily policy and visited places — PASS.
- Locations: default visibility filter still produces misses and calendar obligations — PASS.
- Locations: automatic tempo respects explicit daily choice — PASS.
- Styles: profile overrides and then restores general style — PASS.
- Locations: deleted place cleans live links but keeps historical name and money — PASS.
- Locations: invalid clock, IDs and profile parts cannot replace data — PASS.
- Hints: manual steps change only onboarding and keep money unchanged — PASS.
- UI: create strategy → stage → goal → key task → day → reload — PASS.
- UI: bonus catalog creation preserves parent task draft — PASS.
- Seven actual dates: schedules, rest, pause, remove, rollover and reviews — PASS.
- Two tabs: stale draft retained/refused and no duplicate payout — PASS.
- UI: real JSON download and file import roundtrip — PASS.
- Corrupt primary is preserved, raw download and recovery import work — PASS.
- Demo and test date remain separate from personal data — PASS.
- Mobile/desktop screens and editors: 320/375/390/768/1100px — PASS.
- UI locations: create profile → quick add → hidden/forced → complete → filter → reload — PASS.
- UI editor inherits block location without relinking existing tasks — PASS.
- UI hints: show target, pulse, complete/reload, reset, compact panel in three styles — PASS.
- Styles: all templates, local fonts, reload, 320/390/900px and location settings — PASS.
- Locations: fall-back DST repeated hour produces the real next change — PASS.
- No uncaught JavaScript exceptions — PASS.

## Автоматическая смена места и напоминания

- Actual schedule boundaries update the screen; manual choice expires at real next change — PASS.
- Other-place reminders wait without acknowledgement and appear after switching back — PASS.

## Настоящий service worker и офлайн

- Install service worker scoped to personal and create task — PASS.
- Offline reload, completion, persistent reward and second reload — PASS.
- All three styles and 14 local fonts are available offline — PASS.
- PWA update defers reload for open draft and preserves committed data — PASS.
- Foreground calendar reminder fires once and remains acknowledged on reload — PASS.
- No uncaught browser errors — PASS.

## Существенные результаты

Прежняя неделя 11–17 ноября2026 (Europe/Moscow) сохранила результат: **177 монет/177 XP, 16 активных фактов, 2 пропуска**. Модель дня/экономики не заменена источником. Локации по умолчанию ничего не скрывают и не имеют графика.

Проверены: обновление старого v2 без изменения facts/ledger; ручной и автоматический выбор; ночные правила/выходные/перекрытия; реальная смена экрана при12:01 и истечение ручного выбора при12:02; повтор часа DST America/New_York (1ноября2026, следующая смена06:00UTC); политика пропусков в истории дня; история названия удалённого места; приглушённое напоминание не подтверждается до показа в подходящем месте.

Три стиля ×320/390/900px, прежние экраны также320/375/390/768/1100px. Панель подсказок320×568 без выхода вверх за экран. Помощник показывает цель/подсветку, отметку/пропуск/возврат; прогресс переживает reload и не меняет монеты. Просмотрены мобильные снимки «Ночного квеста», «Стикеров», подсказок; горизонтального переполнения нет. Все14локальных шрифтов и все3темы доступны офлайн. Ошибок JS нет.

Диагностический API добавляется только в HTTP-ответ тестового контекста; в app.js его нет. PWA проверена без этого API, на отдельном временном origin. Прошлые отчёты сохранены в docs/history/2026-11-11-personal-before-lg110/.

## Повторить

Нужны Python/Playwright/Chromium. Из корня запустить локальный сервер8041, затем:

```sh
node --check personal/app.js
node --check personal/persistence.js
node --check personal/sw.js
python personal/tests/browser.py http://127.0.0.1:8041
python personal/tests/locations-live.py http://127.0.0.1:8041
python personal/tests/offline.py
```

JSON-отчёты и снимки создаются в ignored verification/. При обновлении ресурсов увеличивать CACHE в sw.js.

## Границы

Физический iPhone/Safari/Android, экранная клавиатура, установка и реальное разрешение системных уведомлений ожидают приёмки пользователем. Фоновой гарантированной доставки нет. Без Web Locks остаётся проверка снимка, но строгая атомарность нескольких вкладок не обещается. Многомесячная эксплуатация не заменяется этими сценариями.

Собственный набор модели присланной версии запущен отдельно —35/35; дополнительные доказанные отличия перечислены в COMPARE-LG110.md. Полная сквозная проверка чужого приложения здесь не повторялась.
