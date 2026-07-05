import json

INPUT_FILE = "data.json"
OUTPUT_FILE = "cleaneddata.json"

# Rankings to keep for the MU
MU_RANKINGS = [
    "muWeeklyDamages",
    "muBounty",
    "muReputation",
    "muDamages"
]

# Rankings to keep for members
MEMBER_RANKINGS = [
    "userDamages",
    "weeklyUserDamages",
    "userWealth",
    "userBounty"
]


def clean_data(data):
    cleaned = {
        "mu": {
            "name": data.get("mu", {}).get("name"),
            "avatarUrl": data.get("mu", {}).get("avatarUrl"),
            "rankings": {}
        },
        "members": []
    }

    # Keep only selected MU rankings
    mu_rankings = data.get("mu", {}).get("rankings", {})
    for ranking in MU_RANKINGS:
        if ranking in mu_rankings:
            cleaned["mu"]["rankings"][ranking] = mu_rankings[ranking]

    # Keep only selected member data
    for member in data.get("members", []):
        member_clean = {
            "username": member.get("username"),
            "avatarUrl": member.get("avatarUrl"),
            "level": member.get("leveling", {}).get("level"),
            "rankings": {}
        }
        
        member_rankings = member.get("rankings", {})
        for ranking in MEMBER_RANKINGS:
            if ranking in member_rankings:
                member_clean["rankings"][ranking] = member_rankings[ranking]

        cleaned["members"].append(member_clean)

    return cleaned


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    cleaned_data = clean_data(data)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

    print(f"Cleaned data saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
