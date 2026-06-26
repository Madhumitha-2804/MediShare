def match_ngo(medicine_name, donor_location, ngo_data):
    """
    Match a verified medicine directly with dynamic NGO data stored in the database.
    """
    matches = []
    medicine_name = medicine_name.strip().upper()
    donor_location = donor_location.strip().lower()

    # Query all active NGOs from database
    all_ngos = NGO.query.all()

    for ngo in all_ngos:
        ngo_location = ngo.location.strip().lower()
        # Fetch requirements array dynamically
        required_medicines = [req.medicine_name.upper() for req in ngo.requirements]

        score = 0
        reasons = []

        # Rule 1: medicine name match
        if medicine_name in required_medicines:
            score += 70
            reasons.append("Medicine required by NGO")

        # Rule 2: location compatibility match
        if donor_location == ngo_location:
            score += 30
            reasons.append("Same donor and NGO location")

        if score > 0:
            matches.append({
                "ngo_name": ngo.name,
                "location": ngo.location,
                "score": score,
                "match_reason": ", ".join(reasons)
            })

    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches