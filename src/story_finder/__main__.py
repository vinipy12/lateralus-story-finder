import logging

from story_finder.bot import build_application
from story_finder.config import Settings


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # Configuration is validated first: a bad .env fails here, not on first command.
    settings = Settings()

    application = build_application(settings)
    logging.getLogger(__name__).info("starting long-polling")
    application.run_polling()


if __name__ == "__main__":
    main()
