from __future__ import annotations

import argparse
import json
import sys
import time

from essa.hidden_lab import ESSAHiddenRuleLearner


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycles", type=int, default=6)
    parser.add_argument("--forever", action="store_true")
    parser.add_argument("--week", action="store_true")
    parser.add_argument("--delay", type=float, default=0.0)
    args = parser.parse_args()

    learner = ESSAHiddenRuleLearner()
    if args.week:
        args.forever = True
        args.delay = args.delay or 60.0
        end_at = time.monotonic() + 7 * 24 * 60 * 60
    else:
        end_at = None

    if args.forever:
        args.delay = args.delay or 1.0
        run_stream(learner, args.delay, end_at)
        return

    reports = []
    while len(reports) < args.cycles:
        report = learner.run_cycle()
        reports.append(report)

    print(
        json.dumps(
            {
                "cycles": [report.__dict__ for report in reports],
                "forward_rules": learner.output_forward_rules(),
            },
            indent=2,
            sort_keys=True,
        )
    )


def run_stream(
    learner: ESSAHiddenRuleLearner,
    delay: float,
    end_at: float | None,
) -> None:
    while end_at is None or time.monotonic() < end_at:
        report = learner.run_cycle()
        print(json.dumps(report.__dict__, sort_keys=True), flush=True)
        if delay:
            time.sleep(delay)
    print(
        json.dumps(
            {
                "finished": True,
                "reason": "duration_complete",
                "forward_rules": learner.output_forward_rules(),
            },
            sort_keys=True,
        ),
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
