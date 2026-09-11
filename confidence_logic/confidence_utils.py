def calculate_eob_confidence(results: list) -> float:
    """
    Calculate EOB confidence by averaging the model confidence
    of all extracted patients.

    Returns percentage, e.g. 99.0
    """

    if not results:
        return 0.0

    confidences = []

    for patient in results:

        confidence = patient.get("_model_confidence")

        if confidence is None:
            continue

        try:
            confidence = float(confidence)

            confidence = max(
                0.0,
                min(1.0, confidence)
            )

            confidences.append(confidence)

        except (ValueError, TypeError):
            continue

    if not confidences:
        return 0.0

    average_confidence = (
        sum(confidences) / len(confidences)
    )

    return round(
        average_confidence * 100,
        2
    )

def calculate_model_confidence(parsed: dict) -> float:
    """
    Calculate model confidence from all non-zero VLM field confidences.

    Confidence values of 0.0 are excluded from the average.
    Returns a score between 0 and 1.
    """

    confidences = []

    def collect_confidence(obj):

        if isinstance(obj, dict):

            if "confidence" in obj:
                try:
                    confidence = float(obj["confidence"])

                    # Keep confidence safely between 0 and 1
                    confidence = max(
                        0.0,
                        min(1.0, confidence)
                    )

                    # Ignore 0 confidence values
                    if confidence > 0:
                        confidences.append(confidence)

                except (ValueError, TypeError):
                    pass

            # Continue recursively
            for value in obj.values():
                collect_confidence(value)

        elif isinstance(obj, list):

            for item in obj:
                collect_confidence(item)

    collect_confidence(parsed)

    if not confidences:
        return 0.0

    return round(
        sum(confidences) / len(confidences),
        2
    )

def _unwrap_vlm_output(obj):

    if isinstance(obj, dict):

        if (
            "value" in obj
            and "confidence" in obj
        ):
            return obj["value"]

        return {
            key: _unwrap_vlm_output(value)
            for key, value in obj.items()
        }

    elif isinstance(obj, list):

        return [
            _unwrap_vlm_output(item)
            for item in obj
        ]

    return obj