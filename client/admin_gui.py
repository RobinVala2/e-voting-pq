import sys
import asyncio
import re
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTabWidget, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit,
    QSpinBox, QFormLayout, QGroupBox, QMessageBox
)
import httpx

SERVER = "http://127.0.0.1:8000"


# --- Helper functions ---
def format_vote_display(vote_str):
    """
    Format vote string to display x and y on separate lines.
    Input: "{'x': 123, 'y': 456, 'curve': 'P-256'}"
    Output: "x: 123\ny: 456\ncurve: P-256"
    """
    if not vote_str or not isinstance(vote_str, str):
        return vote_str
    
    x_match = re.search(r"'x':\s*(\d+)", vote_str)
    y_match = re.search(r"'y':\s*(\d+)", vote_str)
    curve_match = re.search(r"'curve':\s*'([^']+)'", vote_str)
    
    if x_match and y_match:
        x_val = x_match.group(1)
        y_val = y_match.group(1)
        curve_val = curve_match.group(1) if curve_match else "P-256"
        
        return f"x: {x_val}\ny: {y_val}\ncurve: {curve_val}"
    
    # fallback
    return vote_str


# --- API helpers ---
async def run_hyperion(voters=50, tellers=3, threshold=2, max_votes=2):
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{SERVER}/hyperion",
            json={
                "voters": voters,
                "tellers": tellers,
                "threshold": threshold,
                "max_votes": max_votes
            }
        )
        return r.json()

async def get_bb():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{SERVER}/bb")
        return r.json()


# --- Admin GUI ---
class AdminApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hyperion Admin")
        self.resize(1100, 700)

        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        # Tab 1: Tally
        self.tab_tally = QWidget()
        self.tab_tally.setLayout(self.build_tally_tab())
        self.tabs.addTab(self.tab_tally, "Hyperion Protocol")

        # Tab 2: Bulletin Board
        self.tab_bb = QWidget()
        self.tab_bb.setLayout(self.build_bb_tab())
        self.tabs.addTab(self.tab_bb, "Bulletin Board")

        # Tab 3: PQC Mapping --> TBD: DELETE
        self.tab_pqc_map = QWidget()
        self.tab_pqc_map.setLayout(self.build_pqc_tab())
        self.tabs.addTab(self.tab_pqc_map, "PQC Mapping")

        layout.addWidget(self.tabs)
        self.setLayout(layout)
    
    # ==================
    #   TABS
    # ==================

    def build_tally_tab(self):
        layout = QVBoxLayout()
        
        # Settings group
        settings_group = QGroupBox("Hyperion Protocol Settings")
        settings_layout = QFormLayout()
        
        # Number of Voters
        self.spin_voters = QSpinBox()
        self.spin_voters.setMinimum(1)
        self.spin_voters.setMaximum(1000)
        self.spin_voters.setValue(50)
        settings_layout.addRow("Number of Voters:", self.spin_voters)
        
        # Number of Tellers
        self.spin_tellers = QSpinBox()
        self.spin_tellers.setMinimum(1)
        self.spin_tellers.setMaximum(100)
        self.spin_tellers.setValue(3)
        settings_layout.addRow("Number of Tellers:", self.spin_tellers)
        
        # Threshold
        self.spin_threshold = QSpinBox()
        self.spin_threshold.setMinimum(1)
        self.spin_threshold.setMaximum(100)
        self.spin_threshold.setValue(2)
        self.spin_tellers.valueChanged.connect(
            lambda v: self.spin_threshold.setMaximum(v)
        )
        settings_layout.addRow("Threshold (K):", self.spin_threshold)
        
        # Max Votes
        self.spin_max_votes = QSpinBox()
        self.spin_max_votes.setMinimum(2)
        self.spin_max_votes.setMaximum(100)
        self.spin_max_votes.setValue(2)
        settings_layout.addRow("Max Vote Value:", self.spin_max_votes)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        btn_tally = QPushButton("Run Hyperion Protocol")
        btn_tally.clicked.connect(self.do_tally)

        btn_tally.setToolTip(
            "Runs full Hyperion protocol.\n\n"
            "Classical: EC-ElGamal encryption, ECDSA signatures.\n\n"
            "PQC alternative: ML-KEM (encryption) + ML-DSA (signatures)."
        )

        self.table_tally = QTableWidget()
        self.table_tally.setColumnCount(3)
        self.table_tally.setHorizontalHeaderLabels(["Voter ID", "Vote", "Commitment"])
        self.table_tally.verticalHeader().setVisible(False)
        self.table_tally.horizontalHeader().setStretchLastSection(True)
        self.table_tally.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_tally.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_tally.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        layout.addWidget(btn_tally)
        layout.addWidget(self.table_tally)
        
        # Timing Statistics Table
        self.stats_label = QLabel("Performance Statistics (seconds)")
        self.stats_label.hide()
        layout.addWidget(self.stats_label)
        
        self.table_stats = QTableWidget()
        self.table_stats.setRowCount(1)
        self.table_stats.setVerticalHeaderLabels(["Time (seconds)"])
        self.table_stats.verticalHeader().setVisible(True)
        self.table_stats.horizontalHeader().setStretchLastSection(True)
        self.table_stats.setFixedHeight(60) 
        self.table_stats.setRowHeight(0, 30) 
        self.table_stats.hide()
        layout.addWidget(self.table_stats)

        return layout

    def build_bb_tab(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Bulletin Board"))

        btn_refresh = QPushButton("Refresh BB")
        btn_refresh.clicked.connect(self.do_show_bb)

        btn_refresh.setToolTip(
            "Displays the final bulletin board.\n\n"
            "Classical: EC-ElGamal commitments.\n"
            "PQC alternative: ML-KEM or lattice-based commitments."
        )

        self.table_bb = QTableWidget()
        self.table_bb.setColumnCount(3)
        self.table_bb.setHorizontalHeaderLabels(
            ["Voter ID", "Vote", "Commitment"]
        )
        self.table_bb.verticalHeader().setVisible(False)  
        self.table_bb.horizontalHeader().setStretchLastSection(True)
        self.table_bb.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_bb.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_bb.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        layout.addWidget(btn_refresh)
        layout.addWidget(self.table_bb)

        return layout

    
    def build_pqc_tab(self): # TBD: DELETE
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Mapping of Classical → Post-Quantum Components"))

        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Component / Function", "Non-PQC", "PQC Alternative"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)

        pqc_data = [
            ("Key Generation (poc_setup)", "ECDSA", "ML-DSA"),
            ("Threshold Setup (setup)", "EC-ElGamal + Shamir", "Threshold ML-KEM (experimental)"),
            ("Vote Encryption (voting)", "EC-ElGamal", "ML-KEM"),
            ("Vote Signature (voting)", "ECDSA", "ML-DSA"),
            ("Zero-Knowledge Proofs (voting)", "NIZK + Chaum-Pedersen + Fiat-Shamir", "Lattice-based FS with aborts / Picnic / zk-STARKs"),
            ("Tallying (encryption/decryption)", "EC-ElGamal threshold decryption", "Threshold ML-KEM (research)"),
            ("Re-encryption Mixnet (tallying)", "ElGamal-compatible mixnet", "Lattice-based shuffle (Ring-LWE)"),
            ("Partial Decryption Proofs (tallying)", "Sigma protocols (EC-based)", "Fiat-Shamir with aborts (lattice-based)"),
            ("Commitments / Hash Functions", "SHA-256", "SHA-3 / SHAKE-256"),
            ("Notification (voter term computation)", "EC-ElGamal", "ML-KEM"),
            ("Verification (ballot checking)", "EC-ElGamal commitments", "Fiat-Shamir with aborts"),
            ("Individual Views", "EC-ElGamal re-encryption", "Fiat-Shamir with aborts"),
            ("Coercion Mitigation", "EC-ElGamal commitments", "Fiat-Shamir with aborts"),
        ]

        table.setRowCount(len(pqc_data))
        for i, (comp, classical, pqc) in enumerate(pqc_data):
            table.setItem(i, 0, QTableWidgetItem(comp))
            table.setItem(i, 1, QTableWidgetItem(classical))
            table.setItem(i, 2, QTableWidgetItem(pqc))

        layout.addWidget(table)
        return layout

    # =========================
    #   ACTIONS
    # =========================
    def do_tally(self):
        # Get settings from spin boxes
        voters = self.spin_voters.value()
        tellers = self.spin_tellers.value()
        threshold = self.spin_threshold.value()
        max_votes = self.spin_max_votes.value()

        # Validate threshold <= tellers
        if threshold > tellers:
            QMessageBox.warning(self, "Invalid Settings", 
                              f"Threshold ({threshold}) cannot be greater than number of tellers ({tellers})")
            return

        try:
            res = asyncio.run(run_hyperion(voters, tellers, threshold, max_votes))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error running Hyperion protocol: {e}")
            return
        
        if res.get("status") != "ok":
            QMessageBox.critical(self, "Error", f"Error running Hyperion protocol:\n{res}")
            return

        # Populate tally table
        tally_rows = res.get("tally", [])
        self.table_tally.setRowCount(len(tally_rows))
        for row_idx, row in enumerate(tally_rows):
            self.table_tally.setItem(row_idx, 0, QTableWidgetItem(str(row_idx + 1)))
            vote_str = format_vote_display(row.get("vote", ""))
            vote_item = QTableWidgetItem(vote_str)
            self.table_tally.setRowHeight(row_idx, 80)
            self.table_tally.setItem(row_idx, 1, vote_item)
            self.table_tally.setItem(row_idx, 2, QTableWidgetItem(row.get("commitment", "")))

        # Populate Bulletin Board
        self.table_bb.setRowCount(len(tally_rows))
        for row_idx, row in enumerate(tally_rows):
            self.table_bb.setItem(row_idx, 0, QTableWidgetItem(str(row_idx + 1)))
            vote_str = format_vote_display(row.get("vote", ""))
            vote_item = QTableWidgetItem(vote_str)
            self.table_bb.setRowHeight(row_idx, 80)
            self.table_bb.setItem(row_idx, 1, vote_item)
            self.table_bb.setItem(row_idx, 2, QTableWidgetItem(row.get("commitment", "")))

        # Populate Timing Statistics table
        timings = res.get("timings", {})
        if timings:
            timing_phases = [
                ("Setup", "Setup"),
                ("Voting (avg.)", "Voting (avg.)"),
                ("Tallying (Mixing)", "Tallying (Mixing)"),
                ("Tallying (Decryption)", "Tallying (Decryption)"),
                ("Notification", "Notification"),
                ("Verification (avg.)", "Verification (avg.)"),
                ("Coercion Mitigation", "Coercion Mitigation"),
                ("Individual Views", "Individual Views"),
            ]
            
            available_phases = [(key, name) for key, name in timing_phases if key in timings]
            
            if available_phases:
                self.table_stats.setColumnCount(len(available_phases))
                self.table_stats.setHorizontalHeaderLabels([name for _, name in available_phases])
                
                for col_idx in range(len(available_phases)):
                    self.table_stats.horizontalHeader().setSectionResizeMode(col_idx, QHeaderView.ResizeToContents)
                
                for col_idx, (key, name) in enumerate(available_phases):
                    value = timings[key]
                    try:
                        formatted_value = f"{float(value):.3f}"
                    except (ValueError, TypeError):
                        formatted_value = str(value)
                    
                    self.table_stats.setItem(0, col_idx, QTableWidgetItem(formatted_value))
                
                self.table_stats.setRowHeight(0, 30)
                self.table_stats.setFixedHeight(60) 
                
                self.stats_label.show()
                self.table_stats.show()
            else:
                self.stats_label.hide()
                self.table_stats.hide()
        else:
            self.stats_label.hide()
            self.table_stats.hide()

    def do_show_bb(self):
        """
        Trigger GET /bb -> refresh Bulletin Board table
        """
        try:
            res = asyncio.run(get_bb())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error fetching bulletin board: {e}")
            return
        
        if res.get("status") != "ok":
            QMessageBox.critical(self, "Error", f"Error fetching bulletin board:\n{res}")
            return

        bb = res.get("bb", [])
        self.table_bb.setRowCount(len(bb))
        for row_idx, row in enumerate(bb):
            self.table_bb.setItem(row_idx, 0, QTableWidgetItem(str(row_idx + 1)))
            vote_str = format_vote_display(row.get("vote", ""))
            vote_item = QTableWidgetItem(vote_str)
            self.table_bb.setRowHeight(row_idx, 80)
            self.table_bb.setItem(row_idx, 1, vote_item)
            self.table_bb.setItem(row_idx, 2, QTableWidgetItem(row.get("commitment", "")))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AdminApp()
    win.show()
    sys.exit(app.exec_())
