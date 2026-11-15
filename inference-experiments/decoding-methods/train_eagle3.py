"""Speculators의 실행 이력 저장을 제외하고 EAGLE-3를 학습한다."""

from unittest.mock import patch

from speculators.train.cli import main
from speculators.train.config import TrainConfig


if __name__ == "__main__":
    config = TrainConfig.resolve()
    with patch.object(TrainConfig, "save"):
        main(config)
