# CAL-SOURCE-AUDIT-01 — результат первой фазы

**SOURCE PREFLIGHT: pass** в пределах всех 48 raw findings. Проверены 61 источник и 120 claims, включая 75 existence и все benefit/risk/failure/origin. 62 реальных GET (61 входной URL + уточнение arXiv v1) дали 200; релевантное содержимое прочитано. Непроверенных existence-ID — 0. Source blockers/major — 0.

Два открытых minor не меняют существование: Joplin origin alias между пакетами и конец диапазона restic `482–565`, тогда как файл заканчивается на 557. Initial/final CAL02 SHA разведены; расхождение закрыто отдельным input amendment, final совпадают с sealed manifests. PLOS p discrepancy и Wesnoth income inconsistency подтверждены как внутренние особенности источников, уже ограниченные во входных findings.

Это не финальный аудит рейтинга/отбора. Оценки не открывались. Нормализация, два blind review и расчёт ожидают второй фазы; массовая волна этим отчётом не разрешена. Функции/код приложения и общие статусы не читались.

Фактический контекст `/root/cal_audit`, backend `model_id=null`; инструменты curl GET, Python stdlib/lxml, pdftotext. В checkout записана только собственная папка проверки. Длинные чужие тексты — только /tmp. Выполнена статическая сверка JSONL, ID/refs, счётчиков, excerpts, final hashes и manifest-entries; конкретная квитанция в STATIC_CHECKS.json.

Основной документ — [AUDIT.md](AUDIT.md); замечания — [issues.jsonl](issues.jsonl); HTTP provenance и краткие excerpts — [http_log.jsonl](http_log.jsonl), [source_checks.jsonl](source_checks.jsonl); точные ID — [checked_ids.json](checked_ids.json).
