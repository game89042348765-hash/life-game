# LifeGame — фактические проверки исправлений аудита

4 ноября 2026 года, Москва. Chromium 155 / Playwright 1.62; отдельные временные профили с искусственными данными. Личные данные, настоящие ключи и платные API не использовались.

## Основная регрессия

- PASS: existing save opens unchanged; eight blocks and ten starter treats
- PASS: all main navigation destinations open
- PASS: goal link, three planned tasks, 45 coins + 100 day bonus, five diamonds, reload
- PASS: calendar event creation and completion without a monetary reward
- PASS: quest steps, final reward and undo use the actual accounting history
- PASS: purchases in both currencies, balances and purchase history
- PASS: focus timer: start, pause, reload, resume, stop; no invented minutes or coins
- PASS: key action, manual minutes and a single reward for the daily target
- PASS: day graph editing, independent templates, day placement; first-step countdown without data changes
- PASS: happiness: JSON library, own moment, two timed virtual replies, likes, collection, reload
- PASS: AI settings, model selection, send and formatted reply with local mocks; key absent from storage
- PASS: full JSON export/import, settings, happiness data and original-version compatibility
- PASS: 320/390/480/1440 px: content and dialogs have no horizontal overflow
- PASS: no uncaught JavaScript errors in completed scenarios

## Новые сценарии

- PASS: catalogue batch-add stays open; target widget is visible and focused; data survives removal
- PASS: widget placement and reorder preserve the keyboard control
- PASS: return to long collection restores its scroll position
- PASS: calendar remembers the selected month; Today resets it explicitly
- PASS: Escape protects a changed form and allows explicit discard
- PASS: saved task is addressed and focused; weekday hint and singular reward are correct
- PASS: browser Back and Forward follow internal page transitions
- PASS: browser Back closes a modal before leaving its page
- PASS: named motivation dialog returns to Settings; direct collection and nested modal Back work
- PASS: stage quest creation, two completions and history-safe undo still work
- PASS: JSON download round-trip and invalid file selection leave progress intact
- PASS: quota error is visible in the editor; the last valid save can still be downloaded exactly
- PASS: no uncaught JavaScript errors in the new scenarios

## Дополнительные сценарии

- PASS: catalogue reset is available immediately; removing the last favourite leaves focus on filters
- PASS: bulk selection and block ordering remain accessible through list management
- PASS: required fields remain validated; browser Back can keep or discard an edited form
- PASS: browser Back follows route steps, protects exit, and repeated active-tab taps do not add history
- PASS: file preview and replacement confirmation work; a subsequent download cannot replace the selected restore file
- PASS: corrupt saved JSON is kept untouched and is never exported as a valid backup
- PASS: synthetic 100/500/1000-task lists load and save without data loss; timings recorded as environment-specific
- PASS: no uncaught JavaScript errors in the additional scenarios

## Размер и задержки искусственных списков

| Заданий | JSON, байт | Открыть блок, мс | Выполнить, мс |
| ---: | ---: | ---: | ---: |
| 100 | 26853 | 421 | 314 |
| 500 | 112053 | 704 | 587 |
| 1000 | 218553 | 1569 | 848 |

Это единичные сквозные измерения Playwright, включая ожидания интерфейса, а не гарантия скорости телефона. 1000 видимых заданий уже дают заметную задержку. Большие коллекции/чаты отдельно не измерены.

16 пар финальных снимков: одинаковое сохранение в каждой паре. WebP декодируются в те же RGBA-пиксели, что PNG. Проверка кода: node --check и git diff --check; результат записан в FINAL_MANIFEST.json.

Реальные Safari/iOS/Android, клавиатура, таймер заблокированного телефона, платные API и CORS GitHub Pages не проверены. Все 16 пар пересняты по финальному HTML, включая резервное копирование. Публикация выполняется через GitHub Pages; развёртывание и скачивание проверяются отдельно от локальной функциональной регрессии.
