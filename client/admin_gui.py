import sys
import asyncio
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTabWidget,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit
)
import httpx

SERVER = "http://127.0.0.1:8000"


# --- API helpers ---
async def tally():
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{SERVER}/tally")
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
        self.tabs.addTab(self.tab_tally, "Tally Results")

        # Tab 2: Bulletin Board
        self.tab_bb = QWidget()
        self.tab_bb.setLayout(self.build_bb_tab())
        self.tabs.addTab(self.tab_bb, "Bulletin Board")

        # Tab 3: Logs
        self.tab_logs = QWidget()
        self.tab_logs.setLayout(self.build_logs_tab())
        self.tabs.addTab(self.tab_logs, "Logs")

        # Tab 4: PQC Mapping
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
        layout.addWidget(QLabel("Run Full Hyperion Protocol"))

        btn_tally = QPushButton("Run Tally")
        btn_tally.clicked.connect(self.do_tally)

        btn_tally.setToolTip(
            "Runs full Hyperion protocol.\n\n"
            "Classical: EC-ElGamal encryption, ECDSA signatures.\n\n"
            "PQC alternative: ML-KEM (encryption) + ML-DSA (signatures)."
        )

        self.table_tally = QTableWidget()
        self.table_tally.setColumnCount(2)
        self.table_tally.setHorizontalHeaderLabels(["Vote", "Commitment"])
        self.table_tally.horizontalHeader().setStretchLastSection(True)
        self.table_tally.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(btn_tally)
        layout.addWidget(self.table_tally)

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
        self.table_bb.setColumnCount(2)
        self.table_bb.setHorizontalHeaderLabels(
            ["Vote", "Commitment"]
        )
        self.table_bb.horizontalHeader().setStretchLastSection(True)
        self.table_bb.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(btn_refresh)
        layout.addWidget(self.table_bb)

        return layout

    def build_logs_tab(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Hyperion Console Output"))

        self.logs_box = QTextEdit()
        self.logs_box.setReadOnly(True)
        self.logs_box.setPlaceholderText("Run the tally to view protocol logs...")
        layout.addWidget(self.logs_box)

        return layout
    
    def build_pqc_tab(self):
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
        """
        Trigger /tally -> update all three tabs (tally, bb, logs)
        """
        self.logs_box.setPlainText("Running Hyperion... please wait.")
        QApplication.processEvents()

        try:
            res = asyncio.run(tally())
        except Exception as e:
            self.logs_box.setPlainText(f"Error: {e}")
            return
        
        if res.get("status") != "ok":
            self.logs_box.setPlainText(f"Error running tally:\n{res}")
            return

        # Populate tally table
        tally_rows = res.get("tally", [])
        self.table_tally.setRowCount(len(tally_rows))
        for row_idx, row in enumerate(tally_rows):
            self.table_tally.setItem(row_idx, 0, QTableWidgetItem(row.get("vote", "")))
            self.table_tally.setItem(row_idx, 1, QTableWidgetItem(row.get("commitment", "")))

        # Populate Bulletin Board
        self.table_bb.setRowCount(len(tally_rows))
        for row_idx, row in enumerate(tally_rows):
            self.table_bb.setItem(row_idx, 0, QTableWidgetItem(row.get("vote", "")))
            self.table_bb.setItem(row_idx, 1, QTableWidgetItem(row.get("commitment", "")))

        # Populate Logs tab
        raw_output = res.get("raw_output", "")
        self.logs_box.setPlainText(raw_output or "No log output captured.")

        self.tabs.setCurrentWidget(self.tab_logs)

    def do_show_bb(self):
        """
        Trigger GET /bb -> refresh Bulletin Board table
        """
        try:
            res = asyncio.run(get_bb())
        except Exception as e:
            self.logs_box.setPlainText(f"Error fetching bulletin board: {e}")
            return
        
        if res.get("status") != "ok":
            self.logs_box.setPlainText(f"Error fetching bulletin board:\n{res}")
            return

        bb = res.get("bb", [])
        self.table_bb.setRowCount(len(bb))
        for row_idx, row in enumerate(bb):
            self.table_bb.setItem(row_idx, 0, QTableWidgetItem(row.get("vote", "")))
            self.table_bb.setItem(row_idx, 1, QTableWidgetItem(row.get("commitment", "")))

        self.logs_box.setPlainText(f"Bulletin board refreshed. {len(bb)} entries loaded.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AdminApp()
    win.show()
    sys.exit(app.exec_())
