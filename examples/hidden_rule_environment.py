from __future__ import annotations

import argparse
import json
import time

from essa.hidden_lab import ESSAHiddenRuleLearner


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycles", type=int, default=6)
    parser.add_argument("--forever", action="store_true")
    parser.add_argument("--delay", type=float, default=0.0)
    args = parser.parse_args()

    learner = ESSAHiddenRuleLearner()
    reports = []
    while args.forever or len(reports) < args.cycles:
        report = learner.run_cycle()
        reports.append(report)
        if args.forever:
            print(json.dumps(report.__dict__, sort_keys=True), flush=True)
            if args.delay:
                time.sleep(args.delay)

    if args.forever:
        return

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


if __name__ == "__main__":
    main()
