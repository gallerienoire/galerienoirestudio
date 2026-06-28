#!/usr/bin/env python3
"""Retro-process existing projects: generate styling & shopping guides."""
import json, subprocess, uuid, tempfile

VENV = '/home/team/shared/ai-pipeline/venv/bin/python'
SCRIPT = '/home/team/shared/ai-pipeline/styling_shopping_guide.py'

def team_db(sql):
    r = subprocess.run(['team-db', sql], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"team-db error: {r.stderr[:200]}")
    return json.loads(r.stdout) if r.stdout.strip() else []

def process_project(pid):
    print(f"  Fetching profile for {pid[:8]}...")
    rows = team_db(f"SELECT content FROM deliverables WHERE type='room_profile' AND project_id='{pid}' LIMIT 1")
    if not rows:
        print(f"  ⚠️ No room_profile found for {pid[:8]}")
        return False
    
    inner = json.loads(rows[0]['content'])
    wrapped = {'room_profile': inner}
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(wrapped, f)
        tmp = f.name
    
    r = subprocess.run([VENV, SCRIPT, tmp, '--json'], capture_output=True, text=True)
    
    import os
    os.unlink(tmp)
    
    if r.returncode != 0:
        print(f"  ❌ Script error: {r.stderr[:100]}")
        return False
    
    result = json.loads(r.stdout)
    sg, sh = result['styling_guide'], result['shopping_guide']
    
    sid, shid = str(uuid.uuid4()), str(uuid.uuid4())
    sg_str = json.dumps(sg).replace("'", "''")
    sh_str = json.dumps(sh).replace("'", "''")
    
    team_db(f"INSERT INTO deliverables (id, project_id, type, content) VALUES ('{sid}', '{pid}', 'styling_guide', '{sg_str}')")
    team_db(f"INSERT INTO deliverables (id, project_id, type, content) VALUES ('{shid}', '{pid}', 'shopping_guide', '{sh_str}')")
    team_db(f"UPDATE projects SET status='guides_generated' WHERE id='{pid}'")
    
    room = sg.get('room_summary', {})
    print(f"  ✅ {room.get('room_type','?')} ({room.get('architecture_style','?')}) — {len(sg.get('layout_changes',[]))} changes, {len(sh.get('product_summary',[]))} products")
    return True

if __name__ == '__main__':
    rows = team_db("SELECT DISTINCT d.project_id FROM deliverables d WHERE d.type='room_profile' AND d.project_id NOT IN (SELECT project_id FROM deliverables WHERE type='styling_guide')")
    pids = [r['project_id'] for r in rows]
    print(f"Found {len(pids)} projects needing retro-processing")
    for pid in pids:
        process_project(pid)
    print("\nDone!")