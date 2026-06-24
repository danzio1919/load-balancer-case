from simulation_engine.strategies import (
    SchedulingStrategy,
    LeastLoadedMemoryStrategy,
    RoundRobinStrategy,
    BestFitStrategy,
)

STRATEGY_MAP = {
    "least_loaded_memory": (LeastLoadedMemoryStrategy, "Least Loaded Memory"),
    "round_robin": (RoundRobinStrategy, "Round Robin"),
    "best_fit": (BestFitStrategy, "Best Fit"),
}

def get_strategy_names() -> list[str]:
    return list(STRATEGY_MAP.keys())

def get_strategy(name: str) -> SchedulingStrategy:
    """
    Instantiates and returns the scheduling strategy.
    Defaults to LeastLoadedMemoryStrategy if name is unknown.
    """
    strategy_cls, _ = STRATEGY_MAP.get(name, (LeastLoadedMemoryStrategy, None))
    return strategy_cls()

def get_display_name(name: str) -> str:
    _, display_name = STRATEGY_MAP.get(name, (None, "Least Loaded Memory"))
    return display_name
