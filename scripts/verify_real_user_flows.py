"""Verify Real User Flows A, B, C, D through live HTTP requests against running FastAPI backend.
Inspects actual question IDs, stems, and options across multiple iterations.
"""
import urllib.request
import json
import uuid

BASE_URL = "http://127.0.0.1:8000"

def post(url, data, token=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {token}"} if token else {})
        }
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get(url, token=None):
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"} if token else {}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def run():
    print("=================== SAT MASTER LIVE USER FLOW VERIFICATION ===================")
    
    # 0. Auth: Dev login
    auth_resp = post(f"{BASE_URL}/api/v1/auth/dev", {
        "telegram_id": 77889901,
        "first_name": "E2ETester"
    })
    token = auth_resp["access_token"]
    user_id = auth_resp["user"]["id"]
    print(f"Logged in as test user: {user_id}")

    # ================= FLOW A: MATH PRACTICE (5 CYCLES) =================
    print("\n-------------------- FLOW A: MATH PRACTICE (5 CYCLES) --------------------")
    # Start Math Practice session
    math_session = post(
        f"{BASE_URL}/api/v1/math/practice",
        {"question_count": 6, "domain": "ALL", "difficulty": "MIXED"},
        token
    )
    session_id = math_session["id"]
    print(f"Started Math Practice Session {session_id}")
    
    prev_q = None
    for step in range(1, 6):
        current_sess = get(f"{BASE_URL}/api/v1/math/practice/{session_id}", token)
        curr_q = current_sess["current_question"]
        assert curr_q is not None, f"Expected current_question at step {step}"
        
        qid = curr_q["question_id"]
        pq_id = curr_q["practice_question_id"]
        stem = curr_q["question_text"]
        opts = curr_q["options"]
        opt_ids = [o["id"] for o in opts]
        
        print(f"\n[Math Step {step}]")
        print(f"  Q ID: {qid}")
        print(f"  Stem: {stem[:70]}...")
        print(f"  Options ({len(opts)}): {[(o['label'], o['text'][:25]) for o in opts]}")
        
        if prev_q:
            assert qid != prev_q["qid"], f"Question ID did not change: {qid} == {prev_q['qid']}"
            assert stem != prev_q["stem"], f"Question Stem did not change between questions!"
            assert set(opt_ids).isdisjoint(set(prev_q["opt_ids"])), "Options leaked across questions!"
            print("  [OK] VERIFIED: qid != prev_qid, stem != prev_stem, options belong uniquely to current question")
            
        # Submit answer
        ans_res = post(
            f"{BASE_URL}/api/v1/math/practice/{session_id}/questions/{pq_id}/answer",
            {"selected_option_id": opt_ids[0], "time_spent_seconds": 25},
            token
        )
        print(f"  Answer submitted -> is_correct: {ans_res['is_correct']}, next available: {not ans_res['session_completed']}")
        
        prev_q = {"qid": qid, "stem": stem, "opt_ids": opt_ids}

    # ================= FLOW B: READING & WRITING (5 CYCLES) =================
    print("\n---------------- FLOW B: READING & WRITING (5 CYCLES) ----------------")
    prev_rw = None
    for step in range(1, 6):
        # Fetch R&W question via Question Engine 2.0
        q = get(f"{BASE_URL}/api/v1/questions/random?subject=READING_WRITING", token)
        qid = q["id"]
        stem = q["question_text"]
        opts = q["options"]
        opt_ids = [o["id"] for o in opts]
        
        print(f"\n[R&W Step {step}]")
        print(f"  Q ID: {qid}")
        print(f"  Domain: {q['domain']} | Skill: {q['skill']}")
        print(f"  Stem: {stem[:70]}...")
        print(f"  Options ({len(opts)}): {[(o['label'], o['text'][:25]) for o in opts]}")
        print(f"  Desmos allowed: {q['desmos_allowed']} (Correctly False for R&W)")
        
        assert q["subject"] == "READING_WRITING"
        assert q["desmos_allowed"] is False
        assert len(opts) == 4
        
        if prev_rw:
            assert qid != prev_rw["qid"], f"R&W question ID repeated: {qid}"
            assert stem != prev_rw["stem"], "R&W stem repeated!"
            assert set(opt_ids).isdisjoint(set(prev_rw["opt_ids"])), "Options leaked across R&W questions!"
            print("  [OK] VERIFIED: qid != prev_qid, stem != prev_stem, options strictly belong to current R&W question")
            
        # Submit attempt
        att_res = post(
            f"{BASE_URL}/api/v1/questions/{qid}/attempt",
            {"selected_option_id": opt_ids[0], "time_spent_seconds": 35},
            token
        )
        print(f"  Attempt submitted -> is_correct: {att_res['is_correct']}, explanation length: {len(att_res['explanation'])}")
        
        prev_rw = {"qid": qid, "stem": stem, "opt_ids": opt_ids}

    # ================= FLOW C: ADAPTIVE SESSION =================
    print("\n-------------------- FLOW C: ADAPTIVE SESSION --------------------")
    adapt_sess = post(
        f"{BASE_URL}/api/v1/adaptive/session",
        {"total_questions": 5, "subject": "MATH"},
        token
    )
    asess_id = adapt_sess["id"]
    apq1 = adapt_sess["current_question"]
    q1 = apq1["question"]
    print(f"Adaptive Question 1: [{q1['id'][:8]}] {q1['question_text'][:60]}...")
    
    # Submit answer for Question 1
    post(
        f"{BASE_URL}/api/v1/adaptive/session/{asess_id}/questions/{q1['id']}/answer",
        {"selected_option_id": q1["options"][0]["id"], "time_spent_seconds": 30},
        token
    )
    
    # Fetch updated adaptive session
    updated_asess = get(f"{BASE_URL}/api/v1/adaptive/session/{asess_id}", token)
    apq2 = updated_asess["current_question"]
    q2 = apq2["question"]
    print(f"Adaptive Question 2: [{q2['id'][:8]}] {q2['question_text'][:60]}...")
    
    assert q2["id"] != q1["id"], "Adaptive did not advance question!"
    assert q2["question_text"] != q1["question_text"], "Adaptive stem did not change!"
    assert set(o["id"] for o in q2["options"]).isdisjoint(set(o["id"] for o in q1["options"])), "Adaptive options leaked!"
    print("  [OK] VERIFIED: Adaptive Session advances atomically with new ID, new stem, and new options.")

    # ================= FLOW D: DESMOS LAB =================
    print("\n---------------------- FLOW D: DESMOS LAB ----------------------")
    desmos_sess = post(
        f"{BASE_URL}/api/v1/desmos/session",
        {"target_count": 5, "recommended_only": True},
        token
    )
    dsess_id = desmos_sess["id"]
    dq1 = desmos_sess["questions"][0]
    print(f"Desmos Question 1: [{dq1['question_id'][:8]}] {dq1['question_text'][:60]}...")
    assert dq1["desmos_allowed"] is True
    
    post(
        f"{BASE_URL}/api/v1/desmos/session/{dsess_id}/questions/{dq1['question_id']}/answer",
        {"selected_option_id": dq1["options"][0]["id"], "time_spent_seconds": 20, "desmos_used": True},
        token
    )
    
    updated_dsess = get(f"{BASE_URL}/api/v1/desmos/session/{dsess_id}", token)
    dq2 = next(q for q in updated_dsess["questions"] if not q["is_answered"])
    print(f"Desmos Question 2: [{dq2['question_id'][:8]}] {dq2['question_text'][:60]}...")
    
    assert dq2["question_id"] != dq1["question_id"], "Desmos question did not advance!"
    assert dq2["question_text"] != dq1["question_text"], "Desmos stem did not change!"
    assert set(o["id"] for o in dq2["options"]).isdisjoint(set(o["id"] for o in dq1["options"])), "Desmos options leaked!"
    print("  [OK] VERIFIED: Desmos session advances with distinct stem and options.")

    print("\n=================== ALL 4 USER FLOWS VERIFIED SUCCESSFULLY ===================")

if __name__ == "__main__":
    run()
