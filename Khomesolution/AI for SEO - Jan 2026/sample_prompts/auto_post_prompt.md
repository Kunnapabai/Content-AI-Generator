# WordPress Auto‑Post — Multi‑List Keyword Analyzer & Executor (ONE category per keyword)

Classify each keyword from `data/keywords/keywords.txt` into **exactly one (1) closest category** and the correct author, then execute `scripts/wp_auto_post.py` with the proper flags.
The keywords file has **one keyword per line** (Thai and/or English). Your output must **always** pick a single best category.

---

## 0) Fixed Setup (must use)
- **Prototype post**: `1`
- **Base content dir**: `output/research`
- **Reviewer (always)**: **ID 1**
- **Post status**: **`draft`** (always)


---

## 1) Categories & Authors (ground truth)

| Category | ID  | Scope | Author |
|---|---:|---|---:|
| **ระแนง** | **4** | ระแนงไม้, ระแนงเหล็ก, ระแนงอลูมิเนียม, ระแนงบังตา, ระแนงกันแดด, ระแนงตกแต่ง | **1** |
| **หลังคา** | **3** | หลังคาบ้าน, หลังคาเมทัลชีท, หลังคากระเบื้อง, หลังคาโพลีคาร์บอเนต, หลังคาจั่ว, หลังคาปั้นหยา | **1** |
| **ประตูหน้าต่าง** | **2** | ประตูไม้, ประตูอลูมิเนียม, ประตูกระจก, หน้าต่างบานเลื่อน, หน้าต่างบานกระทุ้ง, ประตูหน้าต่าง UPVC | **1** |

> **Author mapping:** All categories → **1**.


---

## 2) Signal Lists (multi‑hit allowed during analysis)

Normalize to lowercase for matching; keep the original keyword text for CLI flags and slug.

**ระแนง (4)** — core: `ระแนง, ระแนงไม้, ระแนงเหล็ก, ระแนงอลูมิเนียม, ระแนงบังตา, ระแนงกันแดด`
types: `ระแนงตกแต่ง, ระแนงบังแดด, ระแนงซี่, ระแนงไม้เทียม, ระแนงไม้ระบาย`
context: `บังตา, กันแดด, ตกแต่งผนัง, ฉากกั้น`

**หลังคา (3)** — core: `หลังคา, roof, roofing, หลังคาบ้าน, มุงหลังคา`
types: `เมทัลชีท, metal sheet, กระเบื้อง, โพลีคาร์บอเนต, polycarbonate, ซีแพค, cpac, scg`
styles: `หลังคาจั่ว, หลังคาปั้นหยา, หลังคาแบน, หลังคาโค้ง, หลังคาเพิงหมาแหงน`
context: `โครงหลังคา, แป, จันทัน, ฝ้าหลังคา, รางน้ำฝน`

**ประตูหน้าต่าง (2)** — core: `ประตู, หน้าต่าง, door, window, ประตูหน้าต่าง`
materials: `ประตูไม้, ประตูอลูมิเนียม, ประตูกระจก, ประตู upvc, ประตูเหล็ก`
types: `บานเลื่อน, บานกระทุ้ง, บานเปิด, บานพับ, บานสวิง, บานเฟี้ยม`
context: `กรอบประตู, วงกบ, มุ้งลวด, กระจกนิรภัย, ประตูกันเสียง`

**Negations (reduce/ban a modality)**: `ไม่ใช่ระแนง, ไม่ใช่หลังคา, ไม่ใช่ประตู, ไม่ใช่หน้าต่าง`

---

## 3) Decision Algorithm (deterministic, returns **one** category)

1) **Preprocess**: trim, lowercase for matching (keep original for CLI).
2) **Score** each category:
   - Primary/core term = **+3**
   - Type/material or explicit concern tied to that category = **+2**
   - Context cue (implicit intent) = **+1**
   - Negation targeting a category = **−3** to that category
3) **Select exactly one category**:
   - Pick the **highest score**.
   - If tie → apply precedence: **ระแนง > หลังคา > ประตูหน้าต่าง**.
   - If still tied → choose the class with the **longest exact-match token**; if still tied → choose **ระแนง**.
4) **Unknown/unlisted terms (semantic fallback)** if all scores ≤ 0:
   - Slat/screen/partition → **ระแนง (4)**
   - Roof/covering/overhead → **หลังคา (3)**
   - Otherwise → **ประตูหน้าต่าง (2)**
5) **Assign author**: All → **1**. Reviewer → **7**.
6) **Record a short rationale**: top signals (+/−), negations, final score, chosen category.

> **Important:** You must output **one and only one** category per keyword.

---

## 4) CLI Command (PER keyword, status always `draft`)

WordPress auto-generates slugs from post titles.

```bash
python scripts/wp_auto_post.py post \
  --keywords-file data/keywords/keywords.txt \
  --base-dir output/research \
  --prototype-id 1 \
  --category {CATEGORY_ID} \
  --author-id {AUTHOR_ID} \
  --reviewer-id 1 \
  --status draft \
  --only-keyword "{ACTUAL_KEYWORD_TEXT}"
```

- Keep double quotes around Thai/whitespace strings.

---

## 5) Examples (ONE category)

**Keyword:** `ระแนงไม้เทียม ราคา` → ระแนง (4), Author 1

```bash
python scripts/wp_auto_post.py post \
  --keywords-file data/keywords/keywords.txt \
  --base-dir output/research \
  --prototype-id 1 \
  --category 4 \
  --author-id 1 \
  --reviewer-id 1 \
  --status draft \
  --only-keyword "ระแนงไม้เทียม ราคา"
```

**Keyword:** `หลังคาเมทัลชีท ข้อดีข้อเสีย` → หลังคา (3), Author 1

```bash
python scripts/wp_auto_post.py post \
  --keywords-file data/keywords/keywords.txt \
  --base-dir output/research \
  --prototype-id 1 \
  --category 3 \
  --author-id 1 \
  --reviewer-id 1 \
  --status draft \
  --only-keyword "หลังคาเมทัลชีท ข้อดีข้อเสีย"
```

**Keyword:** `ประตูอลูมิเนียม บานเลื่อน` → ประตูหน้าต่าง (2), Author 1

```bash
python scripts/wp_auto_post.py post \
  --keywords-file data/keywords/keywords.txt \
  --base-dir output/research \
  --prototype-id 1 \
  --category 2 \
  --author-id 1 \
  --reviewer-id 1 \
  --status draft \
  --only-keyword "ประตูอลูมิเนียม บานเลื่อน"
```

---

## 6) Execution Loop (all keywords)

For each non‑empty, non‑comment line in `keywords.txt`:

1. Classify with scoring + precedence → **return exactly one category**.
2. Map Author → **1**; Reviewer **7**.
3. Run the CLI (status **draft**; `--only-keyword` = actual keyword).
4. Log a brief rationale and confidence (score gap).

---

## 7) Quick Checklist (per keyword)

- [ ]  Scored all categories; applied negations.
- [ ]  Tie resolved by precedence; **one** category chosen.
- [ ]  Author set → **1** + Reviewer **7**.
- [ ]  CLI executed with `--status draft`.
- [ ]  `--only-keyword` uses the **actual keyword**.
- [ ]  Rationale + confidence recorded.
