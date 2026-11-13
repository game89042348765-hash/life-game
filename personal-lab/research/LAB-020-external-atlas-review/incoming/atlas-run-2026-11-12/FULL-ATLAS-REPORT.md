# Итоговый отчёт полного прогона исследования LifeGame Atlas (`FULL-ATLAS-REPORT.md`)

- **Прогон**: `atlas-run-2026-11-12` (Калибровка + Волна 1 + Волна 2 — полный цикл)
- **Версия конвейера**: `LifeGame-Atlas-Hybrid-v2.1.1+lab.1` (`protocol_version: 2.1`, `taxonomy_version: 2.1`, `rubric_version: 2.1`)
- **Статус целевого отбора (`target = 200`)**: **`target_reached: true`** (`eligible = 204`, `above_floor = 204`, `selected = 200`)
- **Покрытие таксономии**: **32 из 32 категорий (`missing_categories: []`)** и **12 из 12 задач пользователя (`missing_jobs: []`)**

## 1. Сводная воронка полного прогона (13 поисковых пакетов -> 200 отобранных единиц атласа)

Внутри одного непрерывного рабочего прогона сохранены **три полных исторических среза** (калибровочный срез на 50 находок, срез Волны 1 на 75 находок и финальный полный срез на 211 находок), что позволяет координатору проверить как промежуточную калибровку, так и готовый полный атлас:

| Этап / Срез | Папка в архиве | Источники (`sources`) | Находки (`findings`) | Канонические элементы (`elements`) | Слепые оценки (`ratings`) | Отобрано в атлас (`selected`) | `target_reached` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Срез 1: Калибровка (`CAL-SEARCH-01..04`)** | `datasets/calibration-complete-v1/` → `releases/calibration-pilot-v1/` | **36** | **50** | **49** (`45` ранжируемых) | **90** (`45 × 2`) | **45** | `false` (калибровочный проход) |
| **Срез 2: Волна 1 — закрытие 32 категорий (`+WAVE1-SEARCH-01..04`)** | `datasets/wave1-complete-all32cats/` → `releases/wave1-all32cats-v1/` | **67** | **75** | **74** (`69` ранжируемых) | **138** (`69 × 2`) | **69** | `false` (`32/32` категорий закрыты) |
| **Срез 3: Полный релиз (`+WAVE2-SEARCH-01..05`)** | `datasets/full-atlas-complete-v1/` → `releases/full-atlas-release-v1/` | **107** | **211** | **210** (`204` ранжируемых + `5` анти-паттернов + `1` составная система) | **408** (`204 × 2`) | **200** (`100` core + `6` rare_lateral_gem + `94` extension) | **`true` (`200/200`)** |

## 2. Распределение 13 поисковых пакетов по категориям `C01–C32`

1. **`CAL-SEARCH-01` (`C05, C08`)**: 5 источников, 12 находок (Mark Forster Final Version, SuperMemo Incremental Reading, Reclaim/SkedPal Time Maps, Goblin Tools, Amazing Marvin).
2. **`CAL-SEARCH-02` (`C09, C12`)**: 15 источников, 15 находок (CDC ME/CFS Energy Envelope & Push-and-Crash, Christine Miserandino Spoon Theory, Kanban University WIP Limits, Duolingo Streak Freeze & BRB, Humanizing Work & Keypup Backlog Bankruptcy, PMC9432722 Micro-Breaks Meta-Analysis, PubMed 22645164 Self-Compassion, EnvisionADHD Gold/Silver/Bronze Routines, IncitefulMed Heart-Rate Pacing).
3. **`CAL-SEARCH-03` (`C21, C22`)**: 11 источников, 12 находок (Hades God Mode & Mirror of Night, Gamescrye Horizontal Progression, AppScale Sink-First Economy, Heroic Labs Cohort Source-to-Sink Ratio, The Decision Lab Streak Creep, Yu-kai Chou Overjustification Effect & Decoupling Extrinsic Triggers, G2A/DotGG Pity Timers, ACNH Nook Miles+).
4. **`CAL-SEARCH-04` (`C28, C29`)**: 5 источников, 11 находок (Obsidian Sync Conflict Copy Isolation & Double-Sync Detector, Anki Safe Mode & Check Database, Logseq/CRDT JSONL Op-Log, Cycle-Safe Tree CRDT Move, Gap-Detecting Vector Watermark).
5. **`WAVE1-SEARCH-01` (`C01, C02, C04`)**: 5 источников, 4 находки (Wilkinson/Munger Anti-Goals by Inversion, Stanford Life Design Odyssey Plans, Gary Klein Project Premortem, Annie Duke Kill Criteria).
6. **`WAVE1-SEARCH-02` (`C17, C18, C32`)**: 7 источников, 5 находок (Goodhart's Law Paired Counter-Metrics, FranklinCovey 4DX Lead vs. Lag Measures, Focusmate/CHADD Body Doubling, StickK Ulysses Pact, Ness Labs Tiny Experiments Pact).
7. **`WAVE1-SEARCH-03` (`C19, C20, C27`)**: 6 источников, 4 находки (YNAB Give Every Dollar a Job & True Expenses, Arda Two-Bin Kanban Inventory, PNAS Choice Architecture Defaults & Point-of-Choice Cues, Amazing Marvin Modular Strategy Toggles & NN/g Progressive Disclosure).
8. **`WAVE1-SEARCH-04` (`C23, C24, C25, C26`)**: 13 источников, 12 находок (Hades Pact of Punishment Per-Weapon Bounties, Macrobian Safe Failure Loops, SuperBetter Secret Identity & Narrative Triad, Disco Elysium Thought Cabinet, Civilization Two-Layer Fog of War, Kraina GPS Loop Closure Reveal & Rolling Fog Maintenance, GamineAI Skill Tree Anti-Patterns, Death Stranding Social Strand System, Habitica Party Bosses & World Bosses).
9. **`WAVE2-SEARCH-01` (`C01–C06`)**: 8 источников, 27 находок (Reinertsen WSJF & CD3 Matrix, Kahneman/Flyvbjerg Reference Class Forecasting, Taleb Barbell Strategy & Via Negativa, David Allen GTD Two-Minute Rule & Next Physical Action, Atul Gawande Read-Do vs. Do-Confirm Checklists, Gollwitzer If-Then Implementation Intentions, Oettingen WOOP Mental Contrasting, Luhmann/Ahrens Zettelkasten Atomic Notes & Folgezettel).
10. **`WAVE2-SEARCH-02` (`C07–C12`)**: 8 источников, 27 находок (Sophie Leroy Attention Residue Parking Note, Baumeister/Masicampo Zeigarnik Loop Closure via Concrete Plan, Katy Milkman Temptation Bundling, Zoe Read-Bivens Flowtime Stopwatch, Kleitman 90-Minute Ultradian BRAC Pacing, James Clear Never Miss Twice Rule, John Sweller Cognitive Load Theory — Worked Examples, Split-Attention & Expertise Reversal, Marc Zao-Sanders Calendar Timeboxing).
11. **`WAVE2-SEARCH-03` (`C13–C18`)**: 8 источников, 27 находок (Open-Source FSRS DSR Memory Model & Desired Retention Slider, Roediger & Karpicke Testing Effect / Active Recall, Tiago Forte 5-Layer Progressive Summarization, US Army 4-Question After-Action Review & Hot Wash, Nicole Forsgren SPACE 5-Dimensional Productivity Framework, Eve Rodsky Fair Play CPE Ownership & Minimum Standard of Care, Google SRE Blameless Postmortem & Error Budget, FAA/NASA Sterile Cockpit Rule).
12. **`WAVE2-SEARCH-04` (`C19–C24`)**: 8 источников, 27 находок (US EPA Lean 5S Red-Tag Quarantine, Shadow Board & Shine-as-Inspection, Shigeo Shingo Poka-Yoke Control & Kitting Tray, Maddy Thorson Celeste Coyote Time, Jump Buffering, Corner Correction & Assist Mode, Resident Evil 4 Dynamic Difficulty Rank & 1-HP Mercy Gate, Slay the Spire Branching Risk/Reward Map & Campfire Rest vs. Smith, Persona 5 Calendar Slot Allocation & Confidant Synergies, Dark Souls Bloodstain Second-Chance Recovery, Shadow of Mordor Nemesis Obstacle Memory & Bodyguard Sabotage).
13. **`WAVE2-SEARCH-05` (`C25–C32`)**: 8 источников, 28 находок (Outer Wilds Rumor-Mode Mystery Graph & Knowledge-Gated Progression, Journey Anonymous Non-Verbal Chirp Co-op, Ink & Switch 7 Ideals of Local-First Software & The Long Now Test, SQLite Write-Ahead Logging WAL & Passive Checkpointing, Microsoft Research CHI 2019 Guidelines for Human-AI Interaction G1/G2/G3/G8/G9/G11/G14, W3C COGA Cognitive Accessibility Single-Step View & Zero-Timeout Persistence, Single-Case Experimental Design ABAB Reversal & Multiple-Baseline N=1 Trials, Fractional Half-Kelly Capacity Sizing & Maximum Drawdown Circuit Breaker).

## 3. Ключевые показатели финального отбора (`releases/full-atlas-release-v1/audit.json`)

- **Всего источников**: `107` (`100%` с реальными проверенными HTTP/HTTPS URL, `0` синтетических заглушек)
- **Всего находок**: `211` (сгруппированы в **47 бюджетированных шардов** при `--prompt-reserve-bytes 93896` и `--max-bytes 120000`, `0` потерь ID, `0` сверхкрупных одиночных связок)
- **Всего канонических элементов**: `210`
  - Ранжируемые единицы (`main` track): `204`
  - Предупреждения об анти-паттернах (`anti_pattern_warning`): `5` (`F-CAL02-003/015`, `F-CAL03-009`, `F-CAL03-010`, `F-W1S04-009`, `F-W2S03-017`)
  - Составные системы (`reference` / `composite` `method_system`): `1` (`E-ATLAS-021` с привязанными связями `contains`)
- **Слепая оценка**: `408` полных слепых оценок (`204 × 2` от `atlas-rater-A` и `atlas-rater-B`), `4` спорных расхождения (`spread = 2`) закрыты мотивированными записями `rating_resolution` в `decisions.jsonl`
- **Итоговый отбор (`selected = 200`)**:
  - `core`: **100** элементов (по абсолютному индексу качества `Q`)
  - `rare_lateral_gem`: **6** элементов (защищённая квота междисциплинарных находок с `paradigm_novelty = 3`)
  - `extension`: **94** элемента (жадная максимизация покрытия категорий, задач и семейств `U = 0.70*Q + 30*G`)
- **Анализ чувствительности (`sensitivity`)**: рассчитан по 6 профилям весов (`baseline`, `equal`, `long_use`, `low_effort`, `opinions_low`, `opinions_high`), результаты сохранены в `releases/full-atlas-release-v1/audit.json` и `quality-ranked.csv`.
