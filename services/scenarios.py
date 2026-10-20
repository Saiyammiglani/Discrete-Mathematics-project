"""Presentation metadata for the illustrative MPSTME case study.

Facility furniture is illustrative, not an inventory or an actual floor plan.
The graph still contains one switch per location; equipment drawings are not
additional vertices. Costs are illustrative installation estimates in INR 1,000.
"""

MPSTME_SAMPLE = "MPSTME Mumbai (6 facilities)"

MPSTME_FACILITIES = {
    "LIB": {"name": "Library", "kind": "library", "subtitle": "Reading & study"},
    "ARVR": {"name": "AR VR Lab", "kind": "arvr", "subtitle": "Immersive learning"},
    "ROB": {"name": "Robotics Lab", "kind": "robotics", "subtitle": "Robotics & control"},
    "TELE": {"name": "Telecommunication Lab", "kind": "telecom", "subtitle": "Lucas Nuelle lab"},
    "PRINT": {"name": "3-D Printing Lab", "kind": "printing", "subtitle": "Design & fabrication"},
    "RES": {"name": "Research Lab", "kind": "research", "subtitle": "Research workstations"},
}

MPSTME_POS = {
    "LIB": (-4.2, 4.2), "ARVR": (0.0, 4.2), "ROB": (4.2, 4.2),
    "TELE": (0.0, 0.0), "RES": (4.2, 0.0), "PRINT": (8.4, 0.0),
}


def location_name(vertex: str, facilities: dict | None = None) -> str:
    """Display metadata never changes IDs in the algorithm or CSV."""
    return (facilities or {}).get(vertex, {}).get("name", vertex)


def rupees(weight: float) -> str:
    """Scenario weights are thousands of rupees, not raw rupees."""
    return f"₹{weight * 1000:,.0f}"
