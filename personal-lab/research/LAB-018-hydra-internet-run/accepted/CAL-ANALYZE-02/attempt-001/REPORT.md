# REPORT — CAL-ANALYZE-02 / attempt-001

Результат: все 26 назначенных карточек проанализированы. Blocked IDs: `[]`. Пакет submitted для приёмки оркестратором; accepted в полях карточек означает завершённый аналитический разбор, а не окончательную приёмку всего снимка.

Выход: TASK.json, elements.jsonl, relations.jsonl, ANALYSIS.md, REPORT.md и RESULT_MANIFEST.json. Манифест записывается последним и содержит SHA-256/bytes остальных пяти файлов. После сдачи attempt неизменяем.

## Объём и границы

- 26 полных карточек: 13 mechanism, 10 quality_capability, 2 interaction_pattern, 1 technique.
- 23 main и 3 reference; reference: E-HI-CAL-031, E-HI-CAL-034, E-HI-CAL-037. Это треки каталога, а не ранги или готовый отбор.
- Все 26: existence=verified, review_status=accepted, risk_status=reviewed, evidence_effect=unknown. reviewed не означает безопасность для всех.
- 5 новых связей: 3 documented, 2 hypothesis, префикс REL-HI-A02-.
- 93 отдельных строки конкретных рисков; одинаковые строки риска не повторяются. Само число не измеряет качество разбора.
- 10 инфраструктурных quality_capability имеют psychological_loop=null; у остальных петли явно аналитические. Необоснованные дополнительные оси оставлены null/пустыми.
- Не выставлены баллы, не создан локальный топ и не выполнено сопоставление с LifeGame.

Механизмы и исходные различия сохранены: выдача/перенос значка, разные репутационные правила, инвестиция/bounty/upkeep/trash, нативные файлы/экспорт/шифрованный перенос, конфликтная копия/условная запись, документ/оболочка offline, атомарность/undo/история/корзина, чтение backup/пробное восстановление. Условия коррекции и возвращения, прямо не заданные источником, отмечены как аналитические.

## Фактически прочитанный вход

Полностью прочитаны 26 normalized skeletons, 24 finding-записи со всеми 49 claims и 30 source-записей. Полностью прочитан глобальный INDEX: 52 element rows и 24 family rows. Для E-HI-CAL-001–026 прочитан только индекс, не чужие анализы. Итого 130 уникальных record IDs с учётом пересечения skeletons и индекса.

Аналитик прочитал полные записи источников в переданном пакете. Новых HTTP GET и повторного чтения сетевых страниц не было; accessed/retrieved_at и отметки чтения исходных страниц принадлежат поисковому исполнителю. Сведения оркестратора о независимой проверке источников не считаются самостоятельным доказательством эффекта.

Применимые ограничения прочитаны в /workspace/life-game/AGENTS.md и personal-lab/AGENTS.md. В read-only release прочитаны DATA_CONTRACT.md, TAXONOMY.md, taxonomy.json, SCORING.md и PROMPTS/02-ANALYZE.md. Полностью прочитаны tasks/CAL-ANALYZE-02.json и tasks/ANALYSIS-INSTRUCTIONS.md. Первый общий вывод с обрезанной частью индекса/таксономии перечитан меньшими частями; анализ не опирался на обрезанный текст.

Полные skeletons и analyzed_ids:

`E-HI-CAL-027`, `E-HI-CAL-028`, `E-HI-CAL-029`, `E-HI-CAL-030`, `E-HI-CAL-031`, `E-HI-CAL-032`, `E-HI-CAL-033`, `E-HI-CAL-034`, `E-HI-CAL-035`, `E-HI-CAL-036`, `E-HI-CAL-037`, `E-HI-CAL-038`, `E-HI-CAL-039`, `E-HI-CAL-040`, `E-HI-CAL-041`, `E-HI-CAL-042`, `E-HI-CAL-043`, `E-HI-CAL-044`, `E-HI-CAL-045`, `E-HI-CAL-046`, `E-HI-CAL-047`, `E-HI-CAL-048`, `E-HI-CAL-049`, `E-HI-CAL-050`, `E-HI-CAL-051`, `E-HI-CAL-052`

Полные findings:

`F-HI-C03-001`, `F-HI-C03-002`, `F-HI-C03-003`, `F-HI-C03-004`, `F-HI-C03-005`, `F-HI-C03-006`, `F-HI-C03-007`, `F-HI-C03-008`, `F-HI-C03-009`, `F-HI-C03-010`, `F-HI-C03-011`, `F-HI-C03-012`, `F-HI-C04-001`, `F-HI-C04-002`, `F-HI-C04-003`, `F-HI-C04-004`, `F-HI-C04-005`, `F-HI-C04-006`, `F-HI-C04-007`, `F-HI-C04-008`, `F-HI-C04-009`, `F-HI-C04-010`, `F-HI-C04-011`, `F-HI-C04-012`

Полные sources:

`S-HI-C03-001`, `S-HI-C03-002`, `S-HI-C03-003`, `S-HI-C03-004`, `S-HI-C03-005`, `S-HI-C03-006`, `S-HI-C03-007`, `S-HI-C03-008`, `S-HI-C03-009`, `S-HI-C03-010`, `S-HI-C03-011`, `S-HI-C03-012`, `S-HI-C03-013`, `S-HI-C03-014`, `S-HI-C03-015`, `S-HI-C03-016`, `S-HI-C04-001`, `S-HI-C04-002`, `S-HI-C04-003`, `S-HI-C04-004`, `S-HI-C04-005`, `S-HI-C04-006`, `S-HI-C04-007`, `S-HI-C04-008`, `S-HI-C04-009`, `S-HI-C04-010`, `S-HI-C04-011`, `S-HI-C04-012`, `S-HI-C04-013`, `S-HI-C04-014`

Глобальный индекс — все element IDs:

`E-HI-CAL-001`, `E-HI-CAL-002`, `E-HI-CAL-003`, `E-HI-CAL-004`, `E-HI-CAL-005`, `E-HI-CAL-006`, `E-HI-CAL-007`, `E-HI-CAL-008`, `E-HI-CAL-009`, `E-HI-CAL-010`, `E-HI-CAL-011`, `E-HI-CAL-012`, `E-HI-CAL-013`, `E-HI-CAL-014`, `E-HI-CAL-015`, `E-HI-CAL-016`, `E-HI-CAL-017`, `E-HI-CAL-018`, `E-HI-CAL-019`, `E-HI-CAL-020`, `E-HI-CAL-021`, `E-HI-CAL-022`, `E-HI-CAL-023`, `E-HI-CAL-024`, `E-HI-CAL-025`, `E-HI-CAL-026`, `E-HI-CAL-027`, `E-HI-CAL-028`, `E-HI-CAL-029`, `E-HI-CAL-030`, `E-HI-CAL-031`, `E-HI-CAL-032`, `E-HI-CAL-033`, `E-HI-CAL-034`, `E-HI-CAL-035`, `E-HI-CAL-036`, `E-HI-CAL-037`, `E-HI-CAL-038`, `E-HI-CAL-039`, `E-HI-CAL-040`, `E-HI-CAL-041`, `E-HI-CAL-042`, `E-HI-CAL-043`, `E-HI-CAL-044`, `E-HI-CAL-045`, `E-HI-CAL-046`, `E-HI-CAL-047`, `E-HI-CAL-048`, `E-HI-CAL-049`, `E-HI-CAL-050`, `E-HI-CAL-051`, `E-HI-CAL-052`

Глобальный индекс — все family IDs:

`FM-HI-CAPTURE`, `FM-HI-RESURFACING`, `FM-HI-RECURRENCE`, `FM-HI-TIME-COORDINATION`, `FM-HI-CALENDAR-ALLOCATION`, `FM-HI-CLINICAL-LOAD`, `FM-HI-WORK-BREAKS`, `FM-HI-TRAINING-PACING`, `FM-HI-STOCHASTIC-STRESS-RECOVERY`, `FM-HI-CAPACITY-REPRESENTATION`, `FM-HI-COMMITMENT-PAUSE`, `FM-HI-RETURN-QUEUE`, `FM-HI-RECOVERY-HISTORY`, `FM-HI-ACHIEVEMENT-VALIDATION`, `FM-HI-ECONOMIC-SINKS`, `FM-HI-REPUTATION-ACCESS`, `FM-HI-PORTABILITY`, `FM-HI-XP-ADVANCEMENT`, `FM-HI-EXCHANGEABLE-REINFORCEMENT`, `FM-HI-RESOURCE-GATE`, `FM-HI-CONFLICT-CONTROL`, `FM-HI-OFFLINE-PERSISTENCE`, `FM-HI-ATOMIC-PERSISTENCE`, `FM-HI-BACKUP-VERIFICATION`

Blocked IDs: `[]`. Не прочитанные полные карточки за пределами назначения не объявлены проанализированными.

## Выполненные проверки

Локальная статическая проверка прошла без ошибок:

- Все 5/5 входных SHA-256 совпали с TASK до и после анализа.
- Выход содержит ровно все 26 назначенных IDs, без дублей и посторонних элементов.
- Обязательные поля, типы непустых списков и taxonomy codes проверены; все name/description и исходные семантические метки сохранены.
- raw_ids/source_ids, family_id, original_names, existence_claim_refs, normalization_role и контрастные normalization_variants сохранены точно.
- Каждая existence-ссылка указывает на existence claim verified-находки и accessed-источник из карточки; risk/failure refs ссылаются на правильные claims.
- Цели пяти relations существуют в глобальном индексе, статусы и уникальные префиксы корректны.
- scores/ratings отсутствуют; гипотетическая польза и психологические петли помечены; infrastructure null не заменён выдуманной психологией.
- Отдельно перечитаны evidence_summary всех 26 карточек и уточнена граница найденных правил и аналитического пути исправления/возврата.

Это проверка структуры и ограниченного содержания входа, а не верификация эффективности парсингом JSON. Приёмка полного снимка, глобальная дедупликация связей и два отдельных слепых обзора остаются у оркестратора.

## Ограничения и следующие проверки

В данном контексте не повторялись первичные исследования, не запускались приложения, игровые клиенты, реальный экспорт/импорт, конфликт синхронизации, crash tests, чтение backup или восстановление. Полные веб-страницы не сохранялись. Платные API, логины, реальные секреты, сообщения и изменения среды не использовались.

Вопросы текущих версий сохранены явно: Khan Academy Brazil/Peru, MoodleDocs 5.3 и внешние backpacks, расхождение дохода деревни Wesnoth 1.18.5, ограниченный Duolingo test 2025, сторонний Rested XP guide без Blizzard, документация restic 0.19.1/код v0.17.3 и upcoming Nextcloud 36. Исправленный restic locator 482–557 используется без перезаписи источника.

Неизвестные денежные и временные затраты не подменены числами. Смешанные сообщения о badges, школьные санкции и предварительный отчёт GitLab 2017 ограничены их исходными контекстами. Все игровые жизненные переносы и новые сочетания остаются аналитическими гипотезами.

Запись выполнялась только в incoming/CAL-ANALYZE-02/attempt-001/. Приложение, release, принятые данные, общие журналы, Git и ветка не изменялись; другие анализы, ratings, scout и независимая модель не читались. Временный генератор внутри attempt удалён до финального манифеста.

Существенные вопросы и affected IDs перечислены в ANALYSIS.md; незавершённых карточек и unresolved-major/blocker IDs нет. Результат ожидает приёмки оркестратором; публикация и внедрение не выполнялись.
