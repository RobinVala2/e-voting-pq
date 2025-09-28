import sys
import asyncio
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTabWidget,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
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
        self.setWindowTitle("Hyperion Admin (PyQt5)")
        self.resize(1000, 600)

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

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def build_tally_tab(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Admin Panel – Run Tally"))

        btn_tally = QPushButton("Run Tally")
        btn_tally.clicked.connect(self.do_tally)

        self.table_tally = QTableWidget()
        self.table_tally.setColumnCount(3)
        self.table_tally.setHorizontalHeaderLabels(["Row ID", "Vote", "h_r"])
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

        self.table_bb = QTableWidget()
        self.table_bb.setColumnCount(5)
        self.table_bb.setHorizontalHeaderLabels(
            ["Row ID", "Voter ID", "h", "Encrypted Vote", "Signed Ballot"]
        )
        self.table_bb.horizontalHeader().setStretchLastSection(True)
        self.table_bb.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(btn_refresh)
        layout.addWidget(self.table_bb)

        return layout

    # --- Actions ---
    def do_tally(self):
        res = asyncio.run(tally())
        tally_rows = res.get("tally", [])

        self.table_tally.setRowCount(len(tally_rows))
        for row_idx, row in enumerate(tally_rows):
            self.table_tally.setItem(row_idx, 0, QTableWidgetItem(row.get("row_id", "")))
            self.table_tally.setItem(row_idx, 1, QTableWidgetItem(row.get("vote", "")))
            self.table_tally.setItem(row_idx, 2, QTableWidgetItem(row.get("h_r", "")))

    def do_show_bb(self):
        res = asyncio.run(get_bb())
        bb = res.get("bb", [])

        self.table_bb.setRowCount(len(bb))
        for row_idx, row in enumerate(bb):
            self.table_bb.setItem(row_idx, 0, QTableWidgetItem(row.get("row_id", "")))
            self.table_bb.setItem(row_idx, 1, QTableWidgetItem(row.get("voter_id", "")))
            self.table_bb.setItem(row_idx, 2, QTableWidgetItem(row.get("h", "")))
            self.table_bb.setItem(row_idx, 3, QTableWidgetItem(row.get("enc_vote", "")))
            self.table_bb.setItem(row_idx, 4, QTableWidgetItem(row.get("signed_ballot", "")))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AdminApp()
    win.show()
    sys.exit(app.exec_())
