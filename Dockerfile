FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

# State lives on a mounted volume, never in the image, so moving hosts later
# is copying one file.
ENV DATABASE_PATH=/data/story_finder.db
VOLUME ["/data"]

# Long-polling, not webhooks: no port is exposed and none is needed.
CMD ["python", "-m", "story_finder"]
