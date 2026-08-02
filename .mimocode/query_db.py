import sqlite3, json, datetime

DB = r"C:\Users\Administrator\.local\share\mimocode\mimocode.db"
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Find all edit/write tool calls to config.py and sim_core.pyx across sessions
print("=== Tool calls modifying config.py / sim_core.pyx ===")
cur.execute("""
    SELECT DISTINCT m.session_id, m.time_created, 
           p.data as pdata
    FROM part p
    JOIN message m ON p.message_id = m.id
    WHERE p.session_id IN (
        SELECT id FROM session 
        WHERE project_id = 'a270d463-9b10-47b4-a96e-eeb0ce12f43c'
    )
    AND json_extract(p.data, '$.type') = 'tool'
    AND (
        json_extract(p.data, '$.tool') = 'edit' OR 
        json_extract(p.data, '$.tool') = 'write'
    )
    AND (
        json_extract(p.data, '$.state.input.file_path') LIKE '%config.py' OR
        json_extract(p.data, '$.state.input.file_path') LIKE '%sim_core.pyx'
    )
    ORDER BY m.time_created
""")
for r in cur.fetchall():
    dt = datetime.datetime.fromtimestamp(r["time_created"] / 1000, tz=datetime.timezone.utc)
    pdata = json.loads(r["pdata"])
    tool = pdata.get("tool", "")
    input_data = pdata.get("state", {}).get("input", {})
    fp = input_data.get("file_path", "unknown")
    old_s = input_data.get("old_string", "")
    new_s = input_data.get("new_string", "")
    # Find which session
    sid = r["session_id"]
    if old_s and new_s:
        print(f"\n  [{dt.strftime('%Y-%m-%d %H:%M')}] {sid}")
        print(f"  Tool: {tool} file: {fp}")
        print(f"  OLD: {str(old_s)[:300]}")
        print(f"  NEW: {str(new_s)[:300]}")

conn.close()
