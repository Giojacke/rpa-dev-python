"""Bootstrap: load settings, configure logging, create the engine, run the process.

Exit code 0 = success, 1 = the process failed (see logs/ and evidence/).
"""

from __future__ import annotations

import logging
import sys

from config.settings import load_settings
from core.engines.engine_factory import create_engine
from core.exceptions import RpaException
from core.logger import setup_logging
from process import Process


def main() -> int:
    settings = load_settings()
    setup_logging(settings.process_name, settings.logs_dir)
    logger = logging.getLogger("main")
    logger.info("Using engine '%s' (headless=%s)", settings.engine, settings.headless)

    engine = create_engine(settings.engine, headless=settings.headless, timeout_seconds=settings.timeout_seconds)
    try:
        engine.open()
        Process(engine, settings).run()
        return 0
    except RpaException as error:
        logger.error("Bot finished with errors: %s", error)
        return 1
    except Exception:
        logger.exception("Bot crashed with an unexpected error")
        return 1
    finally:
        engine.close()


if __name__ == "__main__":
    sys.exit(main())
