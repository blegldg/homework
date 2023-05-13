from dataclasses import dataclass


@dataclass()
class Experiment:
    name: str
    experimentName: str
    version: str
    timestamp: int


@dataclass
class ExperimentTableEntry:
    type: str
    experimentsJson: str
    timestamp: int
