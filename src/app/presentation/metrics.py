"""Display metrics shared by FastAPI and Streamlit."""


def match_percentage(rank: int, total: int) -> int:
    """Display match % decreasing by rank (aligns with design: 100, 94, 88…)."""
    if total <= 1:
        return 100
    step = 6
    return max(70, 100 - (rank - 1) * step)
