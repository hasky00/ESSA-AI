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
    parser.add_argument("--json", action="store_true")
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
        run_stream(learner, args.delay, end_at, as_json=args.json)
        return

    reports = []
    while len(reports) < args.cycles:
        report = learner.run_cycle()
        reports.append(report)

    if args.json:
        print(
            json.dumps(
                {
                    "cycles": [report.__dict__ for report in reports],
                    "forward_rules": learner.output_forward_rules(),
                    "world_model": learner.output_world_model(),
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print("\n\n".join(learner.cycle_text(report) for report in reports))


def run_stream(
    learner: ESSAHiddenRuleLearner,
    delay: float,
    end_at: float | None,
    *,
    as_json: bool,
) -> None:
    while end_at is None or time.monotonic() < end_at:
        report = learner.run_cycle()
        if as_json:
            print(json.dumps(report.__dict__, sort_keys=True), flush=True)
        else:
            print(learner.cycle_text(report), flush=True)
            print("-" * 72, flush=True)
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
