import json

# Step 4: Restriction priority
ACTION_PRIORITY = {
    "block": 4,
    "escalate": 3,
    "sanitize": 2,
    "allow": 1
}

def load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None

def match_policies(policies, risk):
    return [p for p in policies if p.get("risk") == risk]

def decide_action(input_item, policies, default_action):
    matched_policies = match_policies(policies, input_item.get("risk"))

    if not matched_policies:
        return default_action, [], "no matching policy"

    actions = []
    reasons = []

    for policy in matched_policies:
        if input_item.get("confidence", 0) < policy.get("min_confidence", 1):
            # Confidence not met → choose most restrictive allowed action
            action = max(
                policy["allowed_actions"],
                key=lambda a: ACTION_PRIORITY[a]
            )
            reasons.append(
                f'{policy["risk"]} risk; confidence {input_item["confidence"]} < required {policy["min_confidence"]}'
            )
        else:
            # Confidence met → choose least restrictive allowed action
            action = min(
                policy["allowed_actions"],
                key=lambda a: ACTION_PRIORITY[a]
            )
            reasons.append("confidence threshold met")

        actions.append(action)

    # If multiple policies matched, choose the most restrictive final action
    final_action = max(actions, key=lambda a: ACTION_PRIORITY[a])
    return final_action, [p["id"] for p in matched_policies], "; ".join(reasons)

def generate_output(action, original_output):
    if action == "allow":
        return original_output
    if action == "sanitize":
        return "This response cannot be shown. Please consult a qualified professional."
    if action == "escalate":
        return "Sent for human review"
    return "Blocked"

def main():
    policies_data = load_json("policies.json")
    inputs_data = load_json("inputs.json")

    policies = policies_data.get("policies", [])
    default_action = policies_data.get("default_action", "block")

    results = []

    for item in inputs_data:
        decision, applied_policies, reason = decide_action(
            item, policies, default_action
        )

        results.append({
            "id": item.get("id"),
            "decision": decision,
            "applied_policies": applied_policies,
            "final_output": generate_output(decision, item.get("output")),
            "reason": reason
        })

    with open("output.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
