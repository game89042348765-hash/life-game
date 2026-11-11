# Проверки личной версии

11 ноября 2026. Проверки проводились в отдельных чистых Chromium-контекстах Playwright на localhost, только с вымышленными данными. Внешние запросы тестового браузера блокировались. Реальный браузер/сохранения пользователя не использовались.

**48/48 групп модели/интерфейса и 5/5 групп PWA прошли.** Это направленные проверки личной версии, а не обещание отсутствия всех ошибок.

## Модель и пользовательские сценарии

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
- UI: create strategy → stage → goal → key task → day → reload — PASS.
- UI: bonus catalog creation preserves parent task draft — PASS.
- Seven actual dates: schedules, rest, pause, remove, rollover and reviews — PASS.
- Two tabs: stale draft retained/refused and no duplicate payout — PASS.
- UI: real JSON download and file import roundtrip — PASS.
- Corrupt primary is preserved, raw download and recovery import work — PASS.
- Demo and test date remain separate from personal data — PASS.
- Mobile/desktop screens and editors: 320/375/390/768/1100px — PASS.
- No uncaught JavaScript exceptions — PASS.

## Настоящая автономная оболочка

- Install service worker scoped to personal and create task — PASS.
- Offline reload, completion, persistent reward and second reload — PASS.
- PWA update defers reload for open draft and preserves committed data — PASS.
- Foreground calendar reminder fires once and remains acknowledged on reload — PASS.
- No uncaught browser errors — PASS.

## Неделя

11–17 ноября 2026 (Europe/Moscow), семь настоящих дат в управляемых часах браузера. Без инструмента тестовой даты демо. Задание daily, weekly в среду, разовое без даты, привычка с порогом, квест на три шага и календарное обязательство. Проверены отдых, творческий режим, удаление только из плана, возвращение, завершение и перезагрузка.

Итог: **177 монет / 177 XP, 16 активных фактов, два пропуска**: календарь 12 ноября и регулярное задание 16 ноября. Скрытое отдыхом/паузой и убранное только на сегодня пропусков не создало. Сохранены ответы дневной, недельной и месячной сессий.

## Интерфейс и границы

Экраны и редакторы проверены при ширине 320/375/390/768/1100 px, горизонтального переполнения нет. Просмотрены снимки мобильного редактора и главной в тёмной теме. Проверен обычный UI-путь создания собственного блока → этапа → цели → ключевого задания → Конструктора → выполнения → reload. Нет ошибок JavaScript.

Модельные вызовы доступны только через диагностическую вставку в перехваченный HTTP-ответ тестового браузера. В поставляемом app.js тестового API и обхода защиты tx нет. PWA проверяется отдельно без вставки: регистрация/кэш/офлайн/обновление/напоминание.

Физический iPhone/Safari, клавиатура, меню установки, сохранение файла из мобильного Safari и разрешение системных уведомлений ожидают пользовательской приёмки. Фоновые уведомления при закрытом браузере не реализованы. Без Web Locks резервная защита использует сравнение снимка, но не обещает строгую атомарность между вкладками. Заполненный localStorage не лечится автоматически: запись отклоняется, доступен экспорт.

## Повторить

Нужны Python, Playwright и Chromium. Из корня репозитория запустить локальный сервер на 8041, затем:

```sh
node --check personal/app.js
node --check personal/persistence.js
node --check personal/pwa.js
node --check personal/sw.js
python personal/tests/browser.py http://127.0.0.1:8041
python personal/tests/offline.py
```

Второй сценарий сам поднимает временный HTTP-сервер на отдельном порту, подменяет версию SW только в ответе этого тестового сервера и не меняет рабочий sw.js. Результаты/скриншоты создаются в ignored verification/. Они не входят в публикацию.

Корневой index.html, assets/ и next/ побайтово не изменялись. SHA исходного Claude и проверенной копии совпадает с SOURCE.json.
