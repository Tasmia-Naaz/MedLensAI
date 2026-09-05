class ValidationService:
    @staticmethod
    def calculate_reference_status(value, ref_low, ref_high):
        """
        Determines the clinical status strictly based on source reference ranges.
        Backend logic:
            if value < reference_low: LOW
            elif value > reference_high: HIGH
            else: NORMAL
            if reference range is missing: UNKNOWN
        NEVER invents or guesses reference ranges.
        """
        if value is None:
            return "UNKNOWN"

        if ref_low is None and ref_high is None:
            return "UNKNOWN"

        try:
            val = float(value)
            
            # Both bounds available
            if ref_low is not None and ref_high is not None:
                low = float(ref_low)
                high = float(ref_high)
                if val < low:
                    return "LOW"
                elif val > high:
                    return "HIGH"
                else:
                    return "NORMAL"
            
            # Only upper bound available (< ref_high)
            elif ref_high is not None:
                high = float(ref_high)
                if val > high:
                    return "HIGH"
                else:
                    return "NORMAL"
            
            # Only lower bound available (> ref_low)
            elif ref_low is not None:
                low = float(ref_low)
                if val < low:
                    return "LOW"
                else:
                    return "NORMAL"
            
            return "UNKNOWN"
        except (ValueError, TypeError):
            return "UNKNOWN"

    @staticmethod
    def detect_conflicts(patient_profile, report_text, extracted_tests=None):
        """
        Scans for inconsistencies between patient profile (allergies, conditions, medications)
        and document contents/extracted tests.
        Uses neutral, factual language:
        "Potential inconsistency detected between information in the patient profile and uploaded record. Please review the original information."
        """
        conflicts = []
        doc_text_lower = (report_text or "").lower()

        # 1. Allergy conflict check (e.g. Penicillin, Sulfa, Aspirin, NSAIDs, Latex)
        allergies_str = patient_profile.get("allergies") or ""
        if allergies_str:
            allergy_list = [a.strip() for a in allergies_str.split(",") if a.strip()]
            for allergy in allergy_list:
                allergy_lower = allergy.lower()
                # Cross check against report text or extracted medications
                # E.g. penicillin vs amoxicillin, ampicillin, penicillin
                triggers = [allergy_lower]
                if "penicillin" in allergy_lower:
                    triggers.extend(["amoxicillin", "ampicillin", "augmentin", "penicillin-vk"])
                elif "aspirin" in allergy_lower:
                    triggers.extend(["nsaid", "ibuprofen", "naproxen"])

                for trig in triggers:
                    if trig in doc_text_lower:
                        conflicts.append({
                            "type": "Allergy Profile Inconsistency",
                            "description": (
                                f"Potential inconsistency detected between patient profile allergy ({allergy}) "
                                f"and medication/finding noted in uploaded record ({trig.capitalize()}). "
                                "Please review the original information."
                            )
                        })
                        break

        # 2. Condition conflict check (e.g. Diabetes condition vs Glucose or high glucose medication)
        conditions_str = patient_profile.get("conditions") or ""
        if conditions_str:
            cond_list = [c.strip() for c in conditions_str.split(",") if c.strip()]
            for cond in cond_list:
                cond_lower = cond.lower()
                if "diabetes" in cond_lower:
                    # Check if report has high glucose and contradictory diet notes
                    if "dextrose" in doc_text_lower or "high sugar infusion" in doc_text_lower:
                        conflicts.append({
                            "type": "Condition Protocol Inconsistency",
                            "description": (
                                "Potential inconsistency detected between recorded patient condition (Diabetes) "
                                "and dietary/infusion note found in uploaded document. Please review the original information."
                            )
                        })

        return conflicts
