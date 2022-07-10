from dl_bot.bot import DlBot

import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if __name__ == "__main__":
    bot = DlBot()
    bot.build_and_run()
