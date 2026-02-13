import pandas as pd
import json
import glob
import os
import re

# --- Configuration ---
RESEARCH_DIR  = "output/research"
EXPORTS_DIR   = "data/exports"
GLOBAL_OUTPUT = "data/kw-semantic/master_queries.csv"
GLOBAL_REPORT = "data/kw-semantic/merge_report.json"

SRC_AHREFS       = "🅰️"
SRC_AUTOCOMPLETE = "🔍"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def clean_keyword(text):
    """Normalize keyword: strip whitespace, lowercase."""
    if not isinstance(text, str):
        return ""
    return text.strip().lower()


def strip_thai_combining(text):
    """Remove Thai combining characters (vowels, tone marks) to produce a consonant skeleton.

    Stripped ranges:
      U+0E31          Mai Han Akat
      U+0E34 - U+0E3A Sara I .. Sara Ai Maimuan
      U+0E47 - U+0E4E Maitaikhu .. Yamakkan
    """
    return re.sub(r'[\u0e31\u0e34-\u0e3a\u0e47-\u0e4e]', '', text)


def normalize_for_match(text):
    """Collapse all whitespace for Thai keyword comparison.

    Autocomplete suggestions have spaces between syllables
    (e.g. "ประตู รั้ว หน้า บ้าน") while Ahrefs keywords are
    concatenated (e.g. "ประตูรั้วหน้าบ้าน").  Removing spaces
    makes both forms comparable.
    """
    if not isinstance(text, str):
        return ""
    return re.sub(r"\s+", "", text).strip().lower()


def keyword_matches_topic(kw_norm, base_norm, autocomplete_norms):
    """Return True if a normalised Ahrefs keyword belongs to a topic.

    Matching rules (applied in order):
      1. Exact match against the normalised autocomplete suggestion set.
      2. The base keyword is a substring of the Ahrefs keyword (catches
         longer variants like "ประตูหน้าบ้านสวยๆราคา").
      3. The Ahrefs keyword is a substring of the base keyword (catches
         shorter core forms like "ประตูหน้าบ้าน").
    """
    if kw_norm in autocomplete_norms:
        return True
    if base_norm in kw_norm or kw_norm in base_norm:
        return True
    return False


def merge_sources(sources):
    """Merge source icons from multiple rows into a single string."""
    combined = set()
    for s in sources:
        for icon in [SRC_AHREFS, SRC_AUTOCOMPLETE]:
            if icon in str(s):
                combined.add(icon)
    result = ""
    if SRC_AHREFS in combined:
        result += SRC_AHREFS
    if SRC_AUTOCOMPLETE in combined:
        result += SRC_AUTOCOMPLETE
    return result if result else str(sources.iloc[0])


def find_column(columns, patterns):
    """Find a column matching patterns, checking most-specific pattern first.

    Patterns are tried in order against all columns, so placing
    'organic traffic' before 'traffic' prevents 'Traffic cost'
    from matching before 'Current organic traffic'.
    """
    for p in patterns:
        for col in columns:
            if p in col.lower():
                return col
    return None


def clean_numeric(value):
    """Convert a possibly formatted value (commas, K/M, dash) to int.

    Handles every variant seen in Ahrefs exports:
      '1,200' -> 1200, '3.5K' -> 3500, '-' -> 0, NaN -> 0
    """
    if pd.isna(value):
        return 0
    s = str(value).strip().replace(',', '')
    if s in ('', '-', 'nan', 'None'):
        return 0
    s_upper = s.upper()
    try:
        if 'K' in s_upper:
            return int(float(s_upper.replace('K', '')) * 1_000)
        if 'M' in s_upper:
            return int(float(s_upper.replace('M', '')) * 1_000_000)
        return int(float(s))
    except (ValueError, OverflowError):
        return 0


def deduplicate(df):
    """Aggregate duplicates: merge sources, keep max vol and traf."""
    if df.empty:
        return df

    df = df.copy()
    df["_key"] = df["query"].apply(clean_keyword)

    agg = df.groupby("_key", sort=False).agg(
        query=("query", "first"),
        src=("src", merge_sources),
        vol=("vol", "max"),
        traf=("traf", "max"),
    ).reset_index(drop=True)

    agg = agg.sort_values(by=["vol", "traf"], ascending=[False, False])
    return agg


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def load_autocomplete_json(filepath):
    """Load a single autocomplete JSON.

    Returns (base_keyword, suggestions, DataFrame with query/src/vol/traf).
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    base_kw = data.get("base_keyword", "")
    suggestions = data.get("suggestions", [])

    rows = []
    if base_kw:
        rows.append({
            "query": base_kw, "src": SRC_AUTOCOMPLETE,
            "vol": 0, "traf": 0,
        })
    for s in suggestions:
        if isinstance(s, str) and s.strip():
            rows.append({
                "query": s.strip(), "src": SRC_AUTOCOMPLETE,
                "vol": 0, "traf": 0,
            })

    return base_kw, suggestions, pd.DataFrame(rows)


def resolve_exports_dir(keyword):
    """Resolve the keyword-level exports directory, with skeleton fallback.

    Returns the keyword folder inside EXPORTS_DIR (not the all_urls/ sub-dir)
    so that the caller can glob recursively and pick up both
    ``all_urls/{domain}/page.csv`` and the pre-merged ``{keyword}.csv``.

    Tries the exact folder name first.  If it doesn't exist (e.g. rename was
    blocked by PermissionError), falls back to scanning EXPORTS_DIR for a
    folder whose consonant skeleton matches.
    """
    exact = os.path.join(EXPORTS_DIR, keyword)
    if os.path.isdir(exact):
        return exact

    if not os.path.isdir(EXPORTS_DIR):
        return None

    target_skeleton = strip_thai_combining(keyword)
    for folder in os.listdir(EXPORTS_DIR):
        folder_path = os.path.join(EXPORTS_DIR, folder)
        if not os.path.isdir(folder_path):
            continue
        if strip_thai_combining(folder) == target_skeleton:
            print(f"    Fallback: reading from '{folder}' for keyword '{keyword}'")
            return folder_path

    return None


def load_ahrefs_for_keyword(keyword):
    """Load Ahrefs CSVs recursively from the resolved exports directory.

    Searches ``data/exports/{keyword}/**/*.csv`` (including both the raw
    per-domain files under ``all_urls/`` and the pre-merged keyword CSV).
    Falls back to a skeleton-matched folder when the exact name is missing.
    """
    keyword_dir = resolve_exports_dir(keyword)
    rows = []

    if not keyword_dir:
        print(f"    No exports directory for {keyword}")
        return pd.DataFrame(rows)

    csv_files = sorted(glob.glob(os.path.join(keyword_dir, "**", "*.csv"), recursive=True))
    rel_dir = os.path.relpath(keyword_dir, EXPORTS_DIR)
    print(f"    Found {len(csv_files)} Ahrefs CSV(s) in {rel_dir}/")

    for fp in csv_files:
        rel = os.path.relpath(fp, keyword_dir)
        if os.path.getsize(fp) < 10:
            print(f"      {rel}: too small, skipped")
            continue

        try:
            try:
                df = pd.read_csv(fp, sep="\t", encoding="utf-16")
            except (UnicodeError, UnicodeDecodeError, pd.errors.EmptyDataError):
                try:
                    df = pd.read_csv(fp, encoding="utf-8-sig")
                except (pd.errors.EmptyDataError, pd.errors.ParserError):
                    print(f"      {rel}: unreadable, skipped")
                    continue

            if df.empty:
                print(f"      {rel}: empty, skipped")
                continue

            df.columns = df.columns.str.strip()

            # Dynamic column discovery (most-specific patterns first)
            kw_col = find_column(df.columns, ["keyword"])
            vol_col = find_column(df.columns, ["volume"])
            traf_col = find_column(df.columns, ["organic traffic", "traffic"])

            if not kw_col:
                print(f"      {rel}: no Keyword column found, skipped")
                print(f"        Columns: {list(df.columns)}")
                continue
            if not vol_col:
                print(f"      {rel}: WARNING no Volume column (defaulting to 0)")
                print(f"        Columns: {list(df.columns)}")
            if not traf_col:
                print(f"      {rel}: WARNING no Traffic column (defaulting to 0)")
                print(f"        Columns: {list(df.columns)}")

            loaded = 0
            for _, row in df.iterrows():
                kw = str(row.get(kw_col, "")).strip()
                if not kw:
                    continue

                rows.append({
                    "query": kw,
                    "vol": clean_numeric(row.get(vol_col)) if vol_col else 0,
                    "traf": clean_numeric(row.get(traf_col)) if traf_col else 0,
                    "src": SRC_AHREFS,
                })
                loaded += 1

            print(f"      {rel}: {loaded} rows loaded "
                  f"(vol='{vol_col}', traf='{traf_col}')")
        except Exception as e:
            print(f"      ERROR {rel}: {e}")

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Per-folder processing
# ---------------------------------------------------------------------------
def process_keyword_folder(folder_name, folder_path):
    """Process one keyword folder and write its master-queries CSV.

    Uses full concatenation (outer-join) so that every Ahrefs keyword is
    included regardless of whether it appears in the autocomplete list.
    Autocomplete suggestions are still merged in; deduplicate() combines
    the source icons and keeps the maximum vol/traf when a keyword exists
    in both sources.

    1. Load autocomplete JSON (optional -- missing file is not fatal)
    2. Load ALL Ahrefs CSVs from data/exports/{folder_name}/
    3. Concatenate both sources without filtering
    4. Deduplicate (max vol/traf, merged src icons), export
    """
    parts = []

    # Autocomplete (optional)
    ac_files = glob.glob(os.path.join(folder_path, "*-autocomplete.json"))
    if ac_files:
        base_kw, suggestions, ac_df = load_autocomplete_json(ac_files[0])
        print(f"    Autocomplete: base + {len(suggestions)} suggestions")
        if not ac_df.empty:
            parts.append(ac_df)
    else:
        print(f"    No autocomplete JSON in {folder_name} (continuing with Ahrefs only)")

    # Ahrefs -- include ALL rows, no topic filtering
    ahrefs_df = load_ahrefs_for_keyword(folder_name)
    if not ahrefs_df.empty:
        print(f"    Ahrefs: {len(ahrefs_df)} rows (all included)")
        parts.append(ahrefs_df)

    if not parts:
        print(f"    No data for {folder_name}, skipped")
        return pd.DataFrame()

    merged = deduplicate(pd.concat(parts, ignore_index=True))

    # Clean
    merged["query"] = merged["query"].apply(clean_keyword)
    merged = merged[merged["query"] != ""]

    # Export per-folder CSV
    out_path = os.path.join(folder_path, f"{folder_name}-master-queries.csv")
    merged.to_csv(out_path, index=False, encoding="utf-8-sig")

    ahrefs_count = len(merged[merged["src"].str.contains(SRC_AHREFS, na=False)])
    ac_count = len(merged[merged["src"].str.contains(SRC_AUTOCOMPLETE, na=False)])
    print(f"    Output: {len(merged)} rows (ahrefs={ahrefs_count}, autocomplete={ac_count})")
    print(f"    Saved: {out_path}")

    return merged


# ---------------------------------------------------------------------------
# Folder reconciliation
# ---------------------------------------------------------------------------
def reconcile_thai_folder_names():
    """Rename mangled folders in EXPORTS_DIR to match correct names in RESEARCH_DIR.

    The old sanitize_filename stripped Thai combining characters (vowels / tone
    marks), producing folder names like 'ประตหนาบานสวยๆ' instead of
    'ประตูหน้าบ้านสวยๆ'.  This function detects the mismatch by comparing
    consonant skeletons and renames the exports folder so that
    load_ahrefs_for_keyword() can find the data.
    """
    if not os.path.isdir(RESEARCH_DIR) or not os.path.isdir(EXPORTS_DIR):
        return 0

    research_folders = {
        d for d in os.listdir(RESEARCH_DIR)
        if os.path.isdir(os.path.join(RESEARCH_DIR, d))
    }

    # skeleton -> correct (research) name
    skeleton_to_correct = {}
    for name in research_folders:
        skeleton_to_correct[strip_thai_combining(name)] = name

    exports_folders = [
        d for d in os.listdir(EXPORTS_DIR)
        if os.path.isdir(os.path.join(EXPORTS_DIR, d))
    ]

    renamed = 0
    for exp_name in exports_folders:
        if exp_name in research_folders:
            continue  # already matches

        skeleton = strip_thai_combining(exp_name)
        correct_name = skeleton_to_correct.get(skeleton)
        if not correct_name or correct_name == exp_name:
            continue

        old_path = os.path.join(EXPORTS_DIR, exp_name)
        new_path = os.path.join(EXPORTS_DIR, correct_name)

        if os.path.exists(new_path):
            print(f"    CONFLICT: '{exp_name}' -> '{correct_name}' "
                  f"already exists, skipped")
            continue

        try:
            os.rename(old_path, new_path)
            print(f"    Renamed: '{exp_name}' -> '{correct_name}'")
            renamed += 1
        except PermissionError:
            print(f"    WARNING: Cannot rename '{exp_name}' -> '{correct_name}': "
                  f"permission denied. Close any open files in that folder and retry.")


    return renamed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("Starting Master Query Merge (per-keyword)")
    print("=" * 60)

    # 0. Fix mangled Thai folder names in data/exports/
    print("\n[0] Reconciling Thai folder names")
    fixed = reconcile_thai_folder_names()
    if fixed:
        print(f"    Fixed {fixed} folder(s)")
    else:
        print("    All folder names OK")

    # 1. Discover keyword folders
    keyword_folders = sorted([
        d for d in os.listdir(RESEARCH_DIR)
        if os.path.isdir(os.path.join(RESEARCH_DIR, d))
    ])
    print(f"\n[1] Found {len(keyword_folders)} keyword folder(s)")

    # 2. Process each folder (loads Ahrefs per-keyword from data/exports/)
    all_folder_dfs = []
    for folder_name in keyword_folders:
        folder_path = os.path.join(RESEARCH_DIR, folder_name)
        print(f"\n--- {folder_name} ---")
        folder_df = process_keyword_folder(folder_name, folder_path)
        if not folder_df.empty:
            all_folder_dfs.append(folder_df)

    if not all_folder_dfs:
        print("\nNo data produced. Check input directories.")
        return

    # 3. Global merged output (union of all per-folder results)
    print("\n" + "=" * 60)
    print("[2] Building global master_queries.csv")

    global_df = deduplicate(pd.concat(all_folder_dfs, ignore_index=True))
    global_df["query"] = global_df["query"].apply(clean_keyword)
    global_df = global_df[global_df["query"] != ""]

    os.makedirs(os.path.dirname(GLOBAL_OUTPUT), exist_ok=True)
    global_df.to_csv(GLOBAL_OUTPUT, index=False, encoding="utf-8-sig")

    # 4. Report
    report = {
        "keyword_folders": len(keyword_folders),
        "total_rows": int(len(global_df)),
        "unique_queries": int(global_df["query"].nunique()),
        "per_folder": {},
    }
    for folder_name in keyword_folders:
        fp = os.path.join(RESEARCH_DIR, folder_name,
                          f"{folder_name}-master-queries.csv")
        if os.path.exists(fp):
            fdf = pd.read_csv(fp, encoding="utf-8-sig")
            report["per_folder"][folder_name] = {
                "rows": int(len(fdf)),
                "unique_queries": int(fdf["query"].nunique()),
            }

    with open(GLOBAL_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 5. Summary
    print(f"\n  Global total rows: {report['total_rows']:,}")
    print(f"  Global unique queries: {report['unique_queries']:,}")
    print(f"  Global output: {GLOBAL_OUTPUT}")
    print(f"  Report: {GLOBAL_REPORT}")

    for name, stats in report["per_folder"].items():
        print(f"  [{name}] {stats['rows']} rows, {stats['unique_queries']} queries")


if __name__ == "__main__":
    main()