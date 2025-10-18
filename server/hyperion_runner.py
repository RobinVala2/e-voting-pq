import subprocess
import re

def run_hyperion(voters=50, tellers=3, max_votes=2):
    """
    Run Hyperion main.py as subprocess and capture its console output.
    Returns: dict { 'raw_output': str, 'timings': dict, 'bulletin_board': list }
    """
    cmd = ["python3", "hyperion/main.py", str(voters), str(tellers), str(max_votes)]
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
    match = re.search(r"Setup\s*\|.*?\n([^\n]+)", text)
    if not match:
        return {}
    row = [x.strip() for x in re.split(r"\s*\|\s*", match.group(1))]
    try:
        values = [float(x) for x in row if re.match(r"^[0-9.]+$", x)]
    except ValueError:
        values = row
    headings = re.findall(r"\|\s*([^|]+)", text.splitlines()[-3])  # last table heading line
    return dict(zip(headings, values))

def parse_bulletin_board(text):
    """
    Parse the multi-line ASCII Texttable printed by Hyperion main.py.
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
