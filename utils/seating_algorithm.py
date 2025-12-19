from typing import List, Dict, Any
import pandas as pd
import numpy as np
import random
import re
from pulp import (
    LpProblem, LpVariable, LpBinary, lpSum, LpMaximize, LpStatus,
    PULP_CBC_CMD
)

def _safe_id(x: str) -> str:
    """Sanitize id strings to be safe as variable/constraint names in PuLP."""
    if not isinstance(x, str):
        x = str(x)
    return re.sub(r'[^0-9a-zA-Z_]', '_', x)

def get_student_attribute(student_id: str, attribute: str, students: Dict[str, Dict[str, Any]]):
    """Return attribute or None from student info dict."""
    return students.get(student_id, {}).get(attribute)

def generate_adjacency_matrix(seats: List[Any]) -> Dict[str, List[str]]:
    """
    Generate adjacency matrix based on row_number and col_number.
    seats: List of SQLAlchemy RoomSeat objects or dicts with 'id', 'row_number', 'col_number'.
    Returns: Dict {seat_id_str: [adjacent_seat_id_strs]}
    """
    matrix = {}
    
    # helper to normalize seat usage
    # We will use seat.id (integer) as the key, but cast to str for consistency with algorithm
    seat_map = {} # (row, col) -> seat_id_str
    
    seat_list = []
    
    for seat in seats:
        # Handle both dict and object
        if isinstance(seat, dict):
            s_id = str(seat['id'])
            row = seat.get('row_number')
            col = seat.get('col_number')
        else:
            s_id = str(seat.id)
            row = seat.row_number
            col = seat.col_number
            
        if row is not None and col is not None:
            seat_map[(row, col)] = s_id
        
        seat_list.append(s_id)
        matrix[s_id] = [] # Initialize

    # Build adjacency (checking for neighbors)
    # We consider neighbors: Left, Right, Front, Back.
    # Adjust based on requirements. Usually Left/Right is most critical for cheating.
    # But let's include all 4 for robustness if they are close.
    
    for (r, c), s_id in seat_map.items():
        neighbors = []
        # Check neighbors
        candidates = [
            (r, c+1), (r, c-1), # Left/Right
            (r+1, c), (r-1, c)  # Front/Back
        ]
        
        for nr, nc in candidates:
            if (nr, nc) in seat_map:
                neighbors.append(seat_map[(nr, nc)])
        
        matrix[s_id] = neighbors
        
    return matrix

def allocate_seating(room_data: Dict[str, Any], students: Dict[str, Dict[str, Any]], exam_id: str, exam_type: str = 'SEMESTER') -> Dict[str, Any]:
    """
    Core allocation function.
    
    room_data: {
        "room_id": str,
        "seats": [seat_id_str, ...],
        "adjacency_matrix": {seat_id: [neighbor_ids]}
    }
    students: {
        student_id_str: { 'subject': ..., 'section': ..., 'roll': int, ... }
    }
    """
    
    room_id = room_data.get("room_id", "ROOM")
    seats = list(room_data.get("seats", []))
    adjacency = room_data.get("adjacency_matrix", {})

    S = list(students.keys())
    L = seats

    # Capacity check
    if len(S) > len(L):
        return {"status": "ERROR", "message": f"Capacity Error: {len(S)} students > {len(L)} seats", "assignments": []}

    # Create mapping for sanitized variable names
    s_safe = {s: _safe_id(s) for s in S}
    l_safe = {l: _safe_id(l) for l in L}

    # Create PuLP problem
    prob = LpProblem(f"Exam_Seating_{_safe_id(exam_id)}_{_safe_id(room_id)}", LpMaximize)

    # Decision variables X_s_l
    X = {}
    for s in S:
        X[s] = {}
        for l in L:
            var_name = f"X_{s_safe[s]}_{l_safe[l]}"
            X[s][l] = LpVariable(var_name, cat=LpBinary)

    # --- CONDITIONAL OBJECTIVE FUNCTION ---
    if exam_type.upper() == 'MID':
        # OBJECTIVE: Maximize Roll Number Sorting
        # seat_order based on simple sort of ID (or row/col if we had it here, but ID is proxy)
        seat_order = {seat: i for i, seat in enumerate(sorted(L))}
        
        # Parse roll numbers (handling non-ints safely)
        student_rolls = {}
        for s in S:
            r = get_student_attribute(s, 'roll', students)
            try:
                # Extract numbers from string if needed, or assume it's int-like
                if isinstance(r, str):
                   nums = re.findall(r'\d+', r)
                   val = int(nums[-1]) if nums else 999999
                else:
                   val = int(r)
            except:
                val = 999999
            student_rolls[s] = val

        max_roll = max(student_rolls.values()) if student_rolls else 0
        
        deterministic_weights = {}
        for s in S:
            roll = student_rolls.get(s, max_roll + 1)
            # Higher weight for (Low Roll assigned to Low Seat Index)
            # roll_factor: smaller roll -> bigger number
            roll_weight = (max_roll + 10) - roll  
            
            deterministic_weights[s] = {}
            for l in L:
                seat_index = seat_order[l]
                # seat_factor: smaller index -> bigger number
                seat_weight = (len(L) + 10) - seat_index
                
                # Weight = interaction
                deterministic_weights[s][l] = roll_weight * 1000 + seat_weight 
                
        prob += lpSum(X[s][l] * deterministic_weights[s][l] for s in S for l in L), "MaximizeRollOrder"

    else: 
        # OBJECTIVE: Maximize Randomization
        random_weights = {s: {l: random.random() for l in L} for s in S}
        prob += lpSum(X[s][l] * random_weights[s][l] for s in S for l in L), "MaximizeRandomization"

    # Constraint 1: Seat Limit (<= 1 student)
    for l in L:
        prob += lpSum(X[s][l] for s in S) <= 1, f"Seat_Limit_{l_safe[l]}"

    # Constraint 2: Student Assignment (== 1 seat)
    for s in S:
        prob += lpSum(X[s][l] for l in L) == 1, f"Student_Assignment_{s_safe[s]}"

    # Constraint 3: Separation (Anti-Cheating)
    # Precompute L_adj
    L_adj = {l: adjacency.get(l, []) for l in L}
    
    S_sorted = S
    nS = len(S_sorted)
    
    for i in range(nS):
        s1 = S_sorted[i]
        subj1 = get_student_attribute(s1, 'subject', students)
        sec1 = get_student_attribute(s1, 'section', students)
        roll1 = get_student_attribute(s1, 'roll', students)

        for j in range(i + 1, nS):
            s2 = S_sorted[j]
            subj2 = get_student_attribute(s2, 'subject', students)
            sec2 = get_student_attribute(s2, 'section', students)
            roll2 = get_student_attribute(s2, 'roll', students)

            is_subject_conflict = (subj1 and subj2 and subj1 == subj2)
            is_section_conflict = (sec1 and sec2 and sec1 == sec2)
            
            # Roll conflict: adjacent rolls (e.g., 101 and 102)
            is_roll_conflict = False
            try:
                r1_val = int(re.findall(r'\d+', str(roll1))[-1]) if isinstance(roll1, str) else int(roll1)
                r2_val = int(re.findall(r'\d+', str(roll2))[-1]) if isinstance(roll2, str) else int(roll2)
                if abs(r1_val - r2_val) == 1:
                    is_roll_conflict = True
            except:
                pass

            if is_subject_conflict or is_section_conflict or is_roll_conflict:
                
                name_prefix = "Conflict_"
                if is_subject_conflict: name_prefix += "S"
                if is_section_conflict: name_prefix += "C"
                if is_roll_conflict: name_prefix += "R"
                
                # Enforce separation for adjacent seats
                for l1 in L:
                    neighbors = L_adj.get(l1, [])
                    for l2 in neighbors:
                        # Avoid duplicate constraints (a,b) same as (b,a)
                        # We use simple string comparison or ID comparison to only add once
                        if str(l1) < str(l2):
                           # X[s1][l1] + X[s2][l2] <= 1
                           c_name = f"{name_prefix}_{s_safe[s1]}_{s_safe[s2]}_{l_safe[l1]}_{l_safe[l2]}"
                           prob += X[s1][l1] + X[s2][l2] <= 1, c_name

    # Optional: Preferred seats (omitted for brevity unless requested, data usually not avail yet)

    # Solve
    try:
        solver = PULP_CBC_CMD(msg=0, timeLimit=30)
        prob.solve(solver)
    except Exception as e:
        return {"status": "ERROR", "message": f"Solver exception: {e}", "assignments": []}

    status_str = str(LpStatus[prob.status])
    
    if status_str.lower() in ("optimal", "feasible"):
        assignment_list = []
        for s in S:
            for l in L:
                val = X[s][l].varValue
                if val is not None and float(val) > 0.5:
                    assignment_list.append({
                        "student_id": s,  # This maps back to our student DB ID 
                        "seat_id": l,     # This maps back to our room_seat DB ID
                    })
        return {"status": "SUCCESS", "message": "Seating allocation complete.", "assignments": assignment_list}
    else:
        return {"status": "ERROR", "message": f"Optimization failed: {status_str}", "assignments": []}
