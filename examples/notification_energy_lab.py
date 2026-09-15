from __future__ import annotations

import argparse
import json
import time

from essa.notification_lab import NotificationEnergyLearner


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycles", type=int, default=6)
    parser.add_argument("--forever", action="store_true")
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    learner = NotificationEnergyLearner()
    if args.forever:
        while True:
            report = learner.run_cycle()
            print_report(learner, report, as_json=args.json)
            if args.delay:
                time.sleep(args.delay)
        return

    reports = [learner.run_cycle() for _ in range(args.cycles)]
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


def print_report(
    learner: NotificationEnergyLearner,
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
