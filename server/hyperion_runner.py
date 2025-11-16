import subprocess
import re

def run_hyperion(voters=50, tellers=3, threshold=2, max_votes=2):
    """
    Run Hyperion main.py as subprocess and capture its console output.
    """
    cmd = ["python3", "hyperion/main.py", str(voters), str(tellers), str(threshold), "-maxv", str(max_votes)]
    proc = subprocess.run(cmd, capture_output=True, text=True)

    output = proc.stdout
    timings = parse_timings(output)
    bb = parse_bulletin_board(output)
    return {
        "raw_output": output,
        "timings": timings,
        "bulletin_board": bb,
    }

def parse_timings(text):
    """
    Extract timing table from Texttable output.
    """
    timings = {}
    
    lines = text.split('\n')
    
    header_start = None
    for i, line in enumerate(lines):
        if '| Setup' in line and '| Voting' in line:
            header_start = i
            break
    
    if header_start is None:
        return timings
    
    header_end = None
    for i in range(header_start + 1, min(header_start + 10, len(lines))):
        if lines[i].startswith('+---'):
            header_end = i
            break
    
    if header_end is None:
        return timings
    
    data_line = None
    for i in range(header_end + 1, min(header_end + 5, len(lines))):
        if '|' in lines[i] and re.search(r'\|\s*[0-9]+\.[0-9]+', lines[i]):
            data_line = lines[i]
            break
    
    if data_line is None:
        return timings
    
    header_lines = lines[header_start:header_end]
    
    header_columns = []
    for line in header_lines:
        parts = [p.strip() for p in line.split('|')]
        if parts and not parts[0]:
            parts = parts[1:]
        if not header_columns:
            header_columns = ['' for _ in parts]
        for i, part in enumerate(parts):
            if i < len(header_columns):
                if part:
                    header_columns[i] = (header_columns[i] + ' ' + part).strip()
    
    data_parts = [d.strip() for d in data_line.split('|')]
    if data_parts and not data_parts[0]:
        data_parts = data_parts[1:]
    
    expected_headers = [
        'Setup',
        'Voting (avg.)',
        'Tallying (Mixing)',
        'Tallying (Decryption)',
        'Notification',
        'Verification (avg.)',
        'Coercion Mitigation',
        'Individual Views',
    ]
    
    for i in range(min(len(data_parts), len(expected_headers))):
        if i < len(data_parts):
            value_str = data_parts[i]
            expected_header = expected_headers[i]
            try:
                timings[expected_header] = float(value_str)
            except (ValueError, TypeError):
                pass
    
    return timings

def parse_bulletin_board(text):
    """
    Parse the ASCII Texttable printed by Hyperion main.py.
    """
    bb_data = []
    lines = text.split('\n')
    
    current_vote = []
    current_commitment = []
    in_data_row = False
    
    for line in lines:
        if line.startswith('+---') or line.startswith('| Vote') or not line.strip():
            if current_vote and current_commitment:
                vote_str = ' '.join(current_vote).strip()
                commitment_str = ''.join(current_commitment).strip()
                if "{'x':" in vote_str and "'curve':" in vote_str:
                    bb_data.append({
                        "vote": vote_str,
                        "commitment": commitment_str,
                    })
                
                current_vote = []
                current_commitment = []
                in_data_row = False
            continue
        
        # Parse data rows (lines starting with |)
        if line.startswith('|'):
            in_data_row = True
            # Split by pipe and extract the two columns
            parts = line.split('|')
            if len(parts) >= 3:  # | vote_part | commitment_part |
                vote_part = parts[1].strip()
                commitment_part = parts[2].strip()
                
                if vote_part:
                    current_vote.append(vote_part)
                if commitment_part:
                    current_commitment.append(commitment_part)
    
    if current_vote and current_commitment:
        vote_str = ' '.join(current_vote).strip()
        commitment_str = ''.join(current_commitment).strip()
        if "{'x':" in vote_str and "'curve':" in vote_str:
            bb_data.append({
                "vote": vote_str,
                "commitment": commitment_str,
            })
    
    return bb_data
