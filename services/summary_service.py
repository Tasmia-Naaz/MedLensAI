class SummaryService:
    SAFETY_NOTICE = (
        "MedLens organizes and explains information from available medical records. "
        "It does not provide medical diagnosis or treatment recommendations. "
        "Please consult a qualified healthcare professional for medical decisions."
    )

    @staticmethod
    def generate_summary(report_filename, tests):
        """
        Generates a clear, neutral, patient-friendly explanation of laboratory results.
        Strictly observes non-diagnostic boundaries and links observations to report sources.
        """
        total_tests = len(tests)
        if total_tests == 0:
            return {
                "overview": "No test results were extracted for this document.",
                "total_tests": 0,
                "within_range_count": 0,
                "outside_range_count": 0,
                "unknown_count": 0,
                "observations": [],
                "safety_notice": SummaryService.SAFETY_NOTICE
            }

        within_range = [t for t in tests if t.get("status") == "NORMAL"]
        low_results = [t for t in tests if t.get("status") == "LOW"]
        high_results = [t for t in tests if t.get("status") == "HIGH"]
        unknown_results = [t for t in tests if t.get("status") == "UNKNOWN"]
        outside_range_count = len(low_results) + len(high_results)

        overview = (
            f"Your uploaded report contains {total_tests} laboratory results. "
            f"{len(within_range)} results fall within the reference ranges provided in the report, "
            f"while {outside_range_count} results are outside those ranges"
            f"{f', and {len(unknown_results)} results have no specified reference range' if unknown_results else ''}."
        )

        observations = []

        # Highlight outside range items first
        for t in low_results:
            name = t.get("test_name", "Test")
            val = t.get("value")
            unit = t.get("unit", "")
            page = t.get("source_page", 1)
            observations.append({
                "type": "below_range",
                "badge": "LOW",
                "badge_class": "danger",
                "text": f"{name} ({val} {unit}) is below the reference range stated in the report.",
                "source": f"{report_filename} — Page {page}"
            })

        for t in high_results:
            name = t.get("test_name", "Test")
            val = t.get("value")
            unit = t.get("unit", "")
            page = t.get("source_page", 1)
            observations.append({
                "type": "above_range",
                "badge": "HIGH",
                "badge_class": "warning",
                "text": f"{name} ({val} {unit}) is above the reference range stated in the report.",
                "source": f"{report_filename} — Page {page}"
            })

        for t in within_range:
            name = t.get("test_name", "Test")
            val = t.get("value")
            unit = t.get("unit", "")
            page = t.get("source_page", 1)
            observations.append({
                "type": "within_range",
                "badge": "NORMAL",
                "badge_class": "success",
                "text": f"{name} ({val} {unit}) is within the reference range stated in the report.",
                "source": f"{report_filename} — Page {page}"
            })

        for t in unknown_results:
            name = t.get("test_name", "Test")
            page = t.get("source_page", 1)
            observations.append({
                "type": "unknown_range",
                "badge": "UNKNOWN",
                "badge_class": "secondary",
                "text": f"Reference range not provided in source report for {name}.",
                "source": f"{report_filename} — Page {page}"
            })

        return {
            "overview": overview,
            "total_tests": total_tests,
            "within_range_count": len(within_range),
            "outside_range_count": outside_range_count,
            "unknown_count": len(unknown_results),
            "observations": observations,
            "safety_notice": SummaryService.SAFETY_NOTICE
        }
