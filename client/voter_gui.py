import sys
import asyncio
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit, QLabel, QComboBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from . import voter 
import httpx

SERVER = "http://127.0.0.1:8000"

class VoterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hyperion Voter (PyQt5)")
        self.resize(900, 600)

        self.voter_id = "alice"
        self.pk_voter = "pk_alice"
        self.x, self.h = voter.gen_trapdoor()

        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        # Tab 1: Voter
        self.tab_voter = QWidget()
        self.tab_voter.setLayout(self.build_voter_tab())
        self.tabs.addTab(self.tab_voter, "Voter")

        # Tab 2: Bulletin Board
        self.tab_bb = QWidget()
        self.tab_bb.setLayout(self.build_bb_tab())
        self.tabs.addTab(self.tab_bb, "Bulletin Board")

        # Tab 3: Tally Results (read-only)
        self.tab_tally = QWidget()
        self.tab_tally.setLayout(self.build_tally_tab())
        self.tabs.addTab(self.tab_tally, "Tally Results")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    # --- Voter tab ---
    def build_voter_tab(self):
        layout = QVBoxLayout()

        # Voter ID input
        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel("Voter ID:"))
        self.input_voter_id = QLineEdit(self.voter_id)
        hlayout.addWidget(self.input_voter_id)
        layout.addLayout(hlayout)

        # Vote choice dropdown
        hlayout_vote = QHBoxLayout()
        hlayout_vote.addWidget(QLabel("Vote:"))
        self.vote_choice = QComboBox()
        self.vote_choice.addItems(["YES", "NO"])
        hlayout_vote.addWidget(self.vote_choice)
        layout.addLayout(hlayout_vote)

        # Buttons
        btn_register = QPushButton("Register")
        btn_cast = QPushButton("Cast Vote")
        btn_notify = QPushButton("Fetch Notification")

        btn_register.clicked.connect(self.do_register)
        btn_cast.clicked.connect(self.do_cast)
        btn_notify.clicked.connect(self.do_notify)

        layout.addWidget(btn_register)
        layout.addWidget(btn_cast)
        layout.addWidget(btn_notify)

        # Output log
        self.output_voter = QTextEdit()
        self.output_voter.setReadOnly(True)
        layout.addWidget(self.output_voter)

        return layout

    # --- Bulletin Board tab ---
    def build_bb_tab(self):
        layout = QVBoxLayout()

        btn_refresh = QPushButton("Refresh Bulletin Board")
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

    # --- Tally Results tab (read-only) ---
    def build_tally_tab(self):
        layout = QVBoxLayout()

        btn_refresh = QPushButton("Refresh Tally Results")
        btn_refresh.clicked.connect(self.do_show_tally)

        self.table_tally = QTableWidget()
        self.table_tally.setColumnCount(3)
        self.table_tally.setHorizontalHeaderLabels(["Row ID", "Vote", "h_r"])
        self.table_tally.horizontalHeader().setStretchLastSection(True)
        self.table_tally.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(btn_refresh)
        layout.addWidget(self.table_tally)

        return layout

    # --- Logs ---
    def log_voter(self, text):
        self.output_voter.append(text)

    # --- Actions ---
    def do_register(self):
        voter_id = self.input_voter_id.text()
        res = asyncio.run(voter.register(voter_id, self.pk_voter, self.h))
        self.log_voter(f"[REGISTER] {res}")

    def do_cast(self):
        voter_id = self.input_voter_id.text()
        choice = self.vote_choice.currentText()
        res = asyncio.run(voter.cast(voter_id, choice, self.h))
        self.log_voter(f"[CAST {choice}] {res}")

    def do_notify(self):
        voter_id = self.input_voter_id.text()
        res = asyncio.run(voter.notify(voter_id))
        self.log_voter(f"[NOTIFY] {res}")

    def do_show_bb(self):
        res = asyncio.run(voter.show_bb())
        bb = res.get("bb", [])

        self.table_bb.setRowCount(len(bb))
        for row_idx, row in enumerate(bb):
            self.table_bb.setItem(row_idx, 0, QTableWidgetItem(row.get("row_id", "")))
            self.table_bb.setItem(row_idx, 1, QTableWidgetItem(row.get("voter_id", "")))
            self.table_bb.setItem(row_idx, 2, QTableWidgetItem(row.get("h", "")))
            self.table_bb.setItem(row_idx, 3, QTableWidgetItem(row.get("enc_vote", "")))
            self.table_bb.setItem(row_idx, 4, QTableWidgetItem(row.get("signed_ballot", "")))

    def do_show_tally(self):
        res = asyncio.run(voter.get_tally())
        tally = res.get("tally", [])

        self.table_tally.setRowCount(len(tally))
        for row_idx, row in enumerate(tally):
            self.table_tally.setItem(row_idx, 0, QTableWidgetItem(row.get("row_id", "")))
            self.table_tally.setItem(row_idx, 1, QTableWidgetItem(row.get("vote", "")))
            self.table_tally.setItem(row_idx, 2, QTableWidgetItem(row.get("h_r", "")))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = VoterApp()
    win.show()
    sys.exit(app.exec_())
