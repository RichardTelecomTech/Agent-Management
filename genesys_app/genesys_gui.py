# genesys_gui.py
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QTextEdit
from genesys_client import get_api_client, get_users, get_user_queues, get_user_skills

class GenesysApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.api_instance = get_api_client()
        
    def initUI(self):
        self.layout = QVBoxLayout()

        self.searchBox = QLineEdit(self)
        self.searchBox.setPlaceholderText('Enter User Name')
        self.layout.addWidget(self.searchBox)

        self.searchButton = QPushButton('Search', self)
        self.searchButton.clicked.connect(self.search_users)
        self.layout.addWidget(self.searchButton)

        self.resultBox = QTextEdit(self)
        self.resultBox.setReadOnly(True)
        self.layout.addWidget(self.resultBox)

        self.setLayout(self.layout)
        self.setWindowTitle('Genesys Cloud User Search')
        self.show()
        
    def search_users(self):
        search_text = self.searchBox.text()
        users = get_users(self.api_instance)
        results = []
        for user in users:
            if search_text.lower() in user.name.lower():
                queues = get_user_queues(self.api_instance, user.id)
                skills = get_user_skills(self.api_instance, user.id)
                results.append(f"User: {user.name}\nQueues: {', '.join([q.name for q in queues])}\nSkills: {', '.join([s.name for s in skills])}\n")
        self.resultBox.setText('\n\n'.join(results))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = GenesysApp()
    sys.exit(app.exec_())
