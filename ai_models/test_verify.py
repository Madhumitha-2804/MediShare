from ai_models.verify_medicine import MedicineVerifier
from ai_models.match_ngo import match_ngo


if __name__ == "__main__":
    verifier = MedicineVerifier()

    image_paths = [
        r"C:\Users\varss\OneDrive\Desktop\Medishare\uploads\medicine1_front.png",
        r"C:\Users\varss\OneDrive\Desktop\Medishare\uploads\medicine1_back.png"
    ]

    result = verifier.verify_medicine(image_paths)

    print("=== MEDICINE VERIFICATION RESULT ===")
    print(result)

    if result["status"] == "VERIFIED":
        ngo_data = [
            {
                "ngo_name": "Helping Hands NGO",
                "location": "chennai",
                "required_medicines": ["PARACETAMOL", "DOLO", "AMOXICILLIN"]
            },
            {
                "ngo_name": "Care Foundation",
                "location": "coimbatore",
                "required_medicines": ["AZITHROMYCIN", "CETIRIZINE"]
            },
            {
                "ngo_name": "Hope Medical Trust",
                "location": "madurai",
                "required_medicines": ["PARACETAMOL", "IBUPROFEN"]
            }
        ]

        donor_location = "chennai"
        matches = match_ngo(result["medicine_name"], donor_location, ngo_data)

        print("\n=== NGO MATCH RESULTS ===")
        for ngo in matches:
            print(ngo)