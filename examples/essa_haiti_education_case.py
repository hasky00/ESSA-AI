from __future__ import annotations

import argparse
import json
import time

from essa.haiti_education_case import ESSAHaitiEducationLearner


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--forever", action="store_true")
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    learner = ESSAHaitiEducationLearner()
    if args.forever:
        while True:
            report = learner.run_cycle()
            print_report(learner, report, as_json=args.json)
            if args.delay:
                time.sleep(args.delay)
        return

    reports = [learner.run_cycle() for _ in range(args.days)]
    if args.json:
        print(
            json.dumps(
                {
                    "days": [report.__dict__ for report in reports],
                    "summary": learner.summarize_run(reports),
                    "forward_rules": learner.output_forward_rules(),
                    "world_model": learner.output_world_model(),
                    "source": learner.source_url,
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print("\n\n".join(learner.cycle_text(report) for report in reports))
        print("\n\n" + learner.summary_text(reports))


def print_report(
    learner: ESSAHaitiEducationLearner,
    report,
    *,
    as_json: bool,
) -> None:
    if as_json:
        print(json.dumps(report.__dict__, sort_keys=True), flush=True)
    else:
        print(learner.cycle_text(report), flush=True)
        print("-" * 72, flush=True)


if __name__ == "__main__":
    main()
