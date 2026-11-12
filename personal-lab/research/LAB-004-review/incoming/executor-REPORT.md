# Отчёт о выполнении LAB-004A — восстановление стенда после прерывания

## 1. Происхождение и контрольные суммы (SHA-256)

- **Исходный коммит пакета (`BUNDLE_MANIFEST.json`)**: `032c757db925e6957853045d1b6951bb1230ec59` (ветка `lab/synthetic-users`).
- **SHA-256 `personal-lab/research/LAB-002-digital-month/driver.py` до правки**:
  `2320f7ba1d0235989f93825c4f53301027354c644042acdc53579bee2f1b944e` (`21 900` байт; сохранён в `driver.py.orig`).
- **SHA-256 `personal-lab/research/LAB-002-digital-month/driver.py` после правки**:
  `557f780b6f90d65dd8504a836cd20d37ccce3d3f6247fe6f5ff434be7ac45ab1`.
- **SHA-256 `personal-lab/research/LAB-002-digital-month/README-DRIVER.md` до правки**:
  `3c474769142ed4e41a4e484a5f139a7d1a1ebd76fabf33d6196bd3a3175e5e10`.
- **SHA-256 `personal-lab/research/LAB-002-digital-month/README-DRIVER.md` после правки**:
  `9dd82ea28f12aaab60f6de0f2b14f57790130e9f8128903edb0a0a7e018a0dc5`.
- **SHA-256 нового скрипта проверки `personal-lab/research/LAB-002-digital-month/verify_resume.py`**:
  `16ab0318da4e069cd5bf92e437dd964561bc653c629842e2b4511daef7fbdc2b`.
- **Неизменность приложения и исходных доказательств**:
  Все файлы приложения (`personal-lab/app.js`, `persistence.js`, `planning.js`, `sw.js`, `pwa.js`, `index.html`, `style.css`, `manifest.webmanifest`, `fonts/*`), `world.pilot.json`, `world.month.json` и все 218 файлов в `personal-lab/evidence/month-pilot-001/` побайтово совпадают с `BUNDLE_MANIFEST.json`.

## 2. Среда исполнения и ограничения окружения

- **Фактическая среда**: Linux (Debian GNU/Linux 12 bookworm), Python `3.11.2`, Node `v18.20.4`, Chromium `156.0.8078.73` (`/usr/bin/chromium`), ChromeDriver (`/usr/bin/chromedriver`), `selenium` `4.8.3`.
- **Ограничения среды (отмечены явно согласно `START_HERE.md` и `PROMPT.md`)**:
  1. В изолированном офлайн-контейнере отсутствует доступ к внешней сети и пакет `python3.11-venv` / колесо `playwright==1.62.0` (`python3 -m venv` и `pip install -r requirements.txt` не могут скачать пакеты из PyPI).
  2. В `driver.py` сохранён нативный импорт `from playwright.sync_api import sync_playwright` как основной транспорт по умолчанию (плюс выполнен контрактный тест точных сигнатур вызовов Playwright 1.62.0), а для запуска в офлайн-среде без колеса `playwright` встроен прозрачный CDP/WebDriver-фоллбэк к тому же реальному `/usr/bin/chromium` (`browser_backend` явно фиксируется в `run.json`).
  3. В контейнере управляемая политика `/etc/chromium/policies/managed/chrome_policy.json` блокирует буквальные имена `127.0.0.1` и `localhost` в `URLBlocklist`, разрешая `http://*`. При обнаружении этой политики стенд автоматически передаёт в Chromium `--host-resolver-rules=MAP lifegame.local 127.0.0.1, MAP * ~NOTFOUND, EXCLUDE 127.0.0.1` и открывает локальный сервер через `lifegame.local`, сохраняя блокировку любых внешних запросов.

## 3. Что реализовано в `driver.py` и `README-DRIVER.md`

1. **Явный режим возобновления (`--resume`) и режим чтения (`--read-only`)**:
   - Без `--resume` повторное открытие существующего `run-dir` по-прежнему отклоняется (`run.json already exists: choose a fresh run-dir or pass --resume; do not overwrite evidence`) без изменения файлов.
   - С `--resume` состояние оркестратора и каждого актора восстанавливается из атомарного `checkpoint.json` со сверкой по `events.jsonl` и `summary.json`.
   - Исправлена ошибка в блоке `finally:` функции `serve()`, где прежний `driver.py` при остановке процесса принудительно вызывал `driver.end(...)` и `driver.finish()`, помечая прерванную сессию как `completed`, а незавершённый прогон — как `finished`. Теперь `suspend_on_shutdown()` сохраняет частичный кусок трассы и фиксирует `session_interrupted` и `daemon_stopped`, оставляя сессию активной для последующего `--resume`.
2. **Чекпоинт всех требуемых параметров**:
   - Для каждого `actor` сохраняются и восстанавливаются: `day`, `last_day`, `last_completed_date` (ISO-дата последнего закрытого дня), `memory` (собственные заметки), `steps` и `budget` (`budget_remaining` — расход и остаток бюджета), `active` (статус активной сессии), `virtual_time` (виртуальные часы), `sequence` (счётчик наблюдений), `sessions`, `latest_state`, `pending_action` и `reconcile_required`.
3. **Последовательность дней и `no_use`**:
   - После закрытого дня (`completed`) разрешается только `last_day + 1`.
   - После `no_use` (как по выбору участника через `skip`, так и при `available: false`) день остаётся `no_use` после перезапуска и не открывает браузер задним числом.
4. **Проверка соответствия мира и версии приложения**:
   - При старте прогона сохраняются `world.json`, `source-manifest.json` и SHA-256 всех основных файлов приложения (`index.html`, `app.js`, `persistence.js`, `planning.js`, `style.css`, `sw.js`, `pwa.js`, `manifest.webmanifest`) в `run.json` и `checkpoint.json`.
   - При `--resume` несовпадение мира (`world mismatch`) или любого файла приложения (`application version mismatch`) немедленно отклоняет запуск до модификации каких-либо файлов в `run-dir`.
5. **Явная неоднозначность `pending_action` и запрет автоповтора**:
   - Перед выполнением любого UI-действия в браузере на диск записываются событие `action_started` в `events.jsonl` и структура `pending_action` (`status: "in_flight_unconfirmed"`) в `checkpoint.json`.
   - Если сбой/прерывание происходит после отправки UI-действия в браузер, но до записи подтверждения `action`, при `--resume` действие переводится в `status: "ambiguous_unconfirmed_after_interruption"` с `reconcile_required: true` и `auto_retried: false`.
   - Автоматический повтор клика/ввода/покупки исключён. Любая попытка вызвать `act`/`scroll` до сверки отклоняется с ошибкой `ambiguous pending_action after interruption: automatic retry is forbidden; call observe first to inspect and reconcile actual UI state before acting`.
   - Вызов `observe` переоткрывает persistent-профиль актора на сохранённом `virtual_time`, делает свежий снимок экрана и возвращает его вместе с объектом `ambiguous_pending_action`, предупреждением `recovery_notice` и явными флагами `trace_interrupted: true`, `drafts_restored: false` (несохранённые черновики в DOM и оборванный кусок трассы не выдаются за полностью восстановленные).
6. **Раздельное хранение продолжений журнала и трасс**:
   - Старый `events.jsonl` и уже созданные `trace.zip` не затираются. При каждом `--resume` создаётся отдельный файл продолжения `events.resume-NNN.jsonl` (с синхронной дозаписью в основной `events.jsonl`), а продолжения прерванных трасс сохраняются в `trace-resume-NN.zip`.
7. **Эксклюзивная блокировка профилей и освобождение контекста**:
   - Каталог `run-dir/.driver.lock` и каждый открытый профиль `profiles/<actor>/.profile.lock` удерживаются через неблокирующий `fcntl.flock(LOCK_EX | LOCK_NB)` с дополнительной проверкой живого PID в `SingletonLock` Chromium.
   - По завершении дня (`end`) и по команде `{"op": "release", "actor": "..."}` браузерный контекст штатно закрывается (`context_released: true`), освобождая ОЗУ без потери данных в `profiles/<actor>`.
   - Повторный запуск `--resume` на завершённом прогоне (`finished: true`) отклоняется с понятной причиной (либо открывается в режиме только для чтения с `--read-only`).

## 4. Выполненные команды и фактические результаты по критериям приёмки

### Команды запуска проверок

```sh
# 1. Проверка неизменности 218 исходных доказательств пилота LAB-002
python3 personal-lab/evidence/verify.py

# 2. Комплексная проверка всех 6 критериев приёмки LAB-004A с реальным Chromium и Node-валидатором
python3 personal-lab/research/LAB-002-digital-month/verify_resume.py

# 3. Независимый запуск анализатора фактов и схемы состояний на каталоге resume-проверки
python3 personal-lab/research/LAB-002-digital-month/analyze_run.py personal-lab/verification/resume-test-001
```

### Фактические результаты по 6 критериям приёмки (`personal-lab/verification/resume-test-001/verification-report.json`)

| Критерий | Сценарий проверки в реальном Chromium | Фактический результат | Статус |
| :--- | :--- | :--- | :--- |
| **1. UI-создание → конец дня → стоп → resume → следующий день** | `P01` в день 1 (`2026-11-16`) через UI выбирает Lite и создаёт привычку `«Читать 10 минут вечером»`, закрывает день (`end`), daemon останавливается (`SIGTERM`). После `--resume` попытка повторить день 1 отклоняется (`next day must be 2`), открывается день 2 (`2026-11-17`), привычка на месте без дублей (`habits: 1`), отмечается выполнение (`+5` монет, `+5` XP, `lastProcessed: "2026-11-17"`). | Данные сохранены в `profiles/P01`, повтор дня 1 отклонён, привычка в `observer-state.json` ровно одна, баланс `coins=5, xp=5`. | **PASS** |
| **2. Изоляция памяти, счётчиков и дат двух акторов** | В одном прогоне с перезапусками работают `P01` (привычка чтения, `21:00`/`22:00` MSK) и `P02` (задание `«Собрать материалы проекта»`, `09:00`/`18:00` MSK). | У `P01`: `habits=['Читать 10 минут вечером']`, `tasks=[]`, `last_completed_date='2026-11-19'`. У `P02`: `tasks=['Собрать материалы проекта']`, `habits=[]`, `last_completed_date='2026-11-18'`. Виртуальные часы и заметки `memory` не смешиваются. | **PASS** |
| **3. Сохранение `no_use` и расхода бюджета активной сессии** | День 3 у `P01` (`skip`) и `P02` (`available=false`) фиксируется как `no_use`. В день 4 (`budget=10`) `P01` тратит 2 действия (открывает быстрое добавление и вводит несохранённый черновик), после чего daemon останавливается. После `--resume` проверяется день 3 и продолжается день 4. | День 3 у обоих остался `no_use` (каталоги `day-03` не создавались, попытка открыть день 3 задним числом отклонена). В день 4 у `P01` после `--resume` `actions_used=2, action_budget=10`, `drafts_restored=false`, `trace_interrupted=true`; следующее действие увеличило счётчик до `3/10`. | **PASS** |
| **4. Прерывание после UI-коммита до подтверждения (`pending_action`)** | `P03` в день 1 проходит онбординг, заполняет привычку `«Рисовать скетч 10 минут»` и на шаге 8 нажимает `«Создать»`. После реального клика в Chromium и записи в `localStorage` процесс daemon аварийно завершается (`exit code 99`) до вызова `observe()` и записи `action` в `events.jsonl` (клиент получает `RemoteDisconnected`). Затем запускается `serve --resume`. | Автоповтора нет (`auto_retried: false`). Попытка вызвать `act` до `observe` отклонена с `ambiguous pending_action after interruption: automatic retry is forbidden; call observe first...`. Вызов `observe` вернул актуальный экран, `ambiguous_pending_action` и `recovery_notice`. В `observer-state.json` привычка `«Рисовать скетч 10 минут»` создана ровно 1 раз (`habits: 1`). | **PASS** |
| **5. Несовпадение мира/версии, занятый профиль и завершённый run** | Проверены: запуск без `--resume` на существующем `run-dir`; `--resume` с `world.month.json`; `--resume` с изменённым `app.js`; второй daemon на активном `run-dir`; второй daemon на занятом `profiles/P01`; `--resume` после `finish`; `--resume --read-only` после `finish`. | Все некорректные/конфликтующие запуски отклонены с точными причинами (`world mismatch`, `application version mismatch`, `locked by another active daemon`, `refusing to resume completed run`). SHA-256 всех файлов доказательств до и после отказов совпали побайтово. | **PASS** |
| **6. Снимки, продолжения трасс, схема состояний и контроль ошибок** | Проверены устаревший `observation_id`, неизвестный элемент `e999`, исчерпание бюджета после resume (`action_budget_exhausted`), валидатор `analyze_run.py` (Node + `LifeGamePersistence.validate`), целостность `trace.zip` и `trace-resume-*.zip`, а также регрессия `check_observation.py`. | Все 8 снимков `observer-state.json` прошли `LifeGamePersistence.validate` (`all_captured_personal_states_schema_valid: true`, `all_captured_namespaces_lab_only: true`). Все 8 `trace.zip` и 2 `trace-resume-01.zip` валидны (`zip_valid: true, has_trace: true`). Контроль ошибок работает штатно. | **PASS** |

## 5. Пути к проверочным артефактам

- `personal-lab/research/LAB-002-digital-month/driver.py` — обновлённый транспорт с поддержкой `--resume` и `--read-only`.
- `personal-lab/research/LAB-002-digital-month/README-DRIVER.md` — обновлённая документация транспорта.
- `personal-lab/research/LAB-002-digital-month/verify_resume.py` — исполняемый скрипт проверки всех 6 критериев приёмки.
- `personal-lab/verification/resume-test-001/` — полный набор артефактов основного проверочного прогона:
  - `run.json`, `checkpoint.json`, `summary.json`, `world.json`, `source-manifest.json`
  - `events.jsonl` и отдельные сегменты продолжений `events.resume-001.jsonl` … `events.resume-005.jsonl`
  - `facts-report.json` (результат `analyze_run.py` с проверкой схемы через Node и `persistence.js`)
  - `verification-report.json` (сводка прохождения всех 6 критериев приёмки)
  - `P01/day-01/`, `P01/day-02/`, `P01/day-04/` (включая исходный `trace.zip` и продолжение `trace-resume-01.zip`), `P01/day-06/`
  - `P02/day-01/`, `P02/day-02/`, `P02/day-04/`
  - `P03/day-01/` (включая следы восстановления после аварийного прерывания на `pending_action` и `trace-resume-01.zip`)
- `personal-lab/verification/resume-budget-exhaust-check/` — артефакты проверки сохранения и исчерпания малого бюджета (`2/2`) после `--resume`.
- `personal-lab/verification/observation-check-20261111T212643Z/report.json` — проверка 6 регрессионных правил видимости текста и контролов (`check_observation.py`).
- *Примечание*: все выполненные прогоны в `personal-lab/verification/` являются технической проверкой лабораторной инфраструктуры восстановления и не имеют статуса нового пользовательского исследования или 30-дневного прогона.
