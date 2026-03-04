def is_profile_complete(profile) -> bool:
    # Define “complete” however you want
    required = [
        profile.postcode,
        profile.address_line,
    ]
    return all(bool(v and str(v).strip()) for v in required)