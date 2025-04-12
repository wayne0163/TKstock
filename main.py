from src.config_manager import ConfigManager
from src.gui import StockSystemGUI

def main():
    config = ConfigManager()
    gui = StockSystemGUI(config)
    gui.run()

if __name__ == "__main__":
    main()