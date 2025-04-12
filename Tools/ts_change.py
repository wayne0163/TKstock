import os
import pandas as pd
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QPushButton, QFileDialog, QMessageBox)

class StockCodeConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setWindowTitle('股票代码转换工具')
        self.setGeometry(300, 300, 400, 250)

    def initUI(self):
        central_widget = QWidget()
        layout = QVBoxLayout()

        btn_remove = QPushButton('去掉后缀', self)
        btn_remove.clicked.connect(self.remove_suffix)
        layout.addWidget(btn_remove)

        btn_add = QPushButton('加入交易所后缀', self)
        btn_add.clicked.connect(self.add_suffix)
        layout.addWidget(btn_add)

        btn_exit = QPushButton('退出', self)
        btn_exit.clicked.connect(self.close)
        layout.addWidget(btn_exit)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def remove_suffix(self):
        file_path, _ = QFileDialog.getOpenFileName(self, '选择CSV文件', filter='CSV Files (*.csv)')
        if not file_path:
            return

        try:
            df = pd.read_csv(file_path)
            if 'ts_code' not in df.columns:
                QMessageBox.critical(self, '错误', 'CSV文件中缺少ts_code字段')
                return
            
            df['ts_code'] = df['ts_code'].apply(
                lambda x: re.sub(r'\..*', '', x))
            
            txt_path = os.path.splitext(file_path)[0] + '.txt'
            df['ts_code'].to_csv(txt_path, index=False, header=False)
            
            QMessageBox.information(self, '完成', '后缀移除完成！')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'处理失败: {str(e)}')

    def add_suffix(self):
        file_path, _ = QFileDialog.getOpenFileName(self, '选择文件', 
                                                  filter='CSV Files (*.csv)')
        if not file_path:
            return

        try:
            df = pd.read_csv(file_path)
            def format_code(code):
                code_str = str(int(code)).zfill(6)
                if code_str[0] == '6':
                    return f'{code_str}.SH'
                elif code_str[0] == '8':
                    return f'{code_str}.BJ'
                elif code_str[0] in ['0', '3']:
                    return f'{code_str}.SZ'
                return code_str
            
            df['ts_code'] = df['ts_code'].apply(format_code)
            df.to_csv(file_path, index=False)
            QMessageBox.information(self, '完成', '交易所后缀添加完成！')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'处理失败: {str(e)}')

if __name__ == '__main__':
    app = QApplication([])
    window = StockCodeConverter()
    window.show()
    app.exec_()