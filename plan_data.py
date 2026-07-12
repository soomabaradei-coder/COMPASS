"""Block and reference-section data — extracted from the official department forms.

Sources:
- Blocks for Second Semester Schedules 2026 (block definitions per level)
- First Semester 2026 - Course Registration Challenges form (sections with CRNs)
"""

# Ready-made blocks per level (fixed set of courses in each block)
BLOCKS = {
    "Level 4": [
        {"name": "Level 4 Block", "courses": ["CPCS 203", "CPCS 222", "MATH 202"]},
    ],
    "Level 5 / 6": [
        {"name": "Block 1 (L5)", "courses": ["CPCS 211", "CPCS 212", "CPCS 203", "CHEM 202"]},
        {"name": "Block 1", "courses": ["CPCS 214", "CPCS 223", "CPCS 241", "CPCS 301", "STAT 352"]},
        {"name": "Block 2", "courses": ["CPCS 214", "CPCS 223", "CPCS 241", "CPCS 301", "STAT 352"]},
        {"name": "Block 3", "courses": ["CPCS 214", "CPCS 223", "CPCS 241", "CPCS 301", "STAT 352"]},
        {"name": "Block 4", "courses": ["CPCS 214", "CPCS 223", "CPCS 241", "CPCS 301", "STAT 352"]},
        {"name": "Block 1 (Scholarship)", "courses": ["CPCS 214", "CPCS 301", "CPCS 241", "CPCS 381", "CPCS 391"]},
    ],
    "Level 7 / 8": [
        {"name": "Block 1 (L7)", "courses": ["CPCS 324", "CPCS 331", "CPCS 351", "CPCS 361", "CPIS 334"]},
        {"name": "Block 1", "courses": ["CPCS 302", "CPCS 381", "CPCS 391", "CPIS 334", "CPIS 393"]},
        {"name": "Block 2", "courses": ["CPCS 301", "CPCS 302", "CPCS 381", "CPCS 391", "CPIS 334", "CPIS 393"]},
        {"name": "Block 3", "courses": ["CPCS 212", "CPCS 302", "CPCS 381", "CPCS 391", "CPIS 334", "CPIS 393"]},
        {"name": "Block 4", "courses": ["CPCS 222", "CPCS 302", "CPCS 381", "CPCS 391", "CPIS 334", "CPIS 393"]},
    ],
    "Level 9 / 10": [
        {"name": "Block 1 - Advanced Programming Track", "courses": ["CPCS 403", "CPIS 428"]},
        {"name": "Block 2 - Software Engineering Track", "courses": ["CPCS 353", "CPCS 454", "CPCS 457", "CPIS 428"]},
    ],
}

# Sections with reference numbers (CRN) per block — for the schedule-challenges form
CHALLENGE_BLOCKS = {
    "Level 5 - Block 1": ["CPCS 212 AAR (65780)", "CPCS 204 BCS (65681)", "CPCS 211 GAR (65772)"],
    "Level 5 - Block 2": ["CPCS 212 CAR (65786)", "CPCS 211 BAR (65763)", "CPCS 204 DCS (65747)"],
    "Level 5 - Block 3": ["CPCS 211 DAR (65769)", "CPCS 204 GCS (65723)", "CPCS 212 HAR (65787)"],
    "Level 5.5 - Block 1 (Scholarship/Transfer)": ["CPCS 223 EAR (66218)", "CPCS 212 VAR (68373)",
                                                    "CPCS 351 DAR (66388)", "CPCS 211 IAR (68372)"],
    "Level 7 - Block 1": ["CPCS 371 CAR (66404)", "CPCS 331 EAR (66377)", "CPCS 324 DAR (66263)",
                          "CPCS 361 GAR (66356)", "CPCS 351 IAR (66392)"],
    "Level 7 - Block 2": ["CPCS 371 AAR (66398)", "CPCS 331 CAR (66379)", "CPCS 351 BAR (66383)",
                          "CPCS 324 GAR (66265)", "CPCS 361 IAR (66365)"],
    "Level 7 - Block 3": ["CPCS 331 AAR (66373)", "CPCS 371 EAR (66406)", "CPCS 324 BAR (66267)",
                          "CPCS 361 DAR (66362)", "CPCS 351 GAR (66391)"],
    "Level 7.5 - Block 1 (Transfer)": ["CPCS 324 DAR (66263)", "CPCS 302 BAR (66413)",
                                        "CPIS 334 ICS (63006)", "CPCS 391 (66422)", "CPCS 981"],
    "Level 9 - General Block (Graduates)": ["CPCS 425 (66633)", "CPCS 463 (66640)", "CPCS 432 (66622)",
                                            "CPCS 433 (66626)", "CPCS 302 BAR (66413)", "CPCS 391 (66422)",
                                            "CPCS 371 EAR (66406)", "CPCS 361 DAR (66362)", "CPCS 331 AAR (66373)"],
}

# Registration problem types (from the form)
CHALLENGE_TYPES = [
    "I could not add any course",
    "I added only one course (must be dropped and a full new block chosen)",
    "I added two or more courses from the same block but could not add the rest",
    "Other",
]


def blocks_group_for_level(level):
    """Return the block group matching the student's level."""
    if level is None:
        return "Level 5 / 6"
    if level <= 4:
        return "Level 4"
    if level <= 6:
        return "Level 5 / 6"
    if level <= 8:
        return "Level 7 / 8"
    return "Level 9 / 10"
