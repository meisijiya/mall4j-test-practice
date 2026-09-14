# mall4j-test-practice

> Test design and artifacts for gz-yami/mall4j (⭐5.2k · AGPL-3.0).

## What's here

Functional test cases, predicted defects, and a 9-chapter test report for the B2C e-commerce platform mall4j. Plus the lesson materials I wrote while doing the work.

| Path | Contents |
|---|---|
| `testcases/M1-D2-001/` | 90 functional cases (login / register / product / cart) — CSV + Markdown + generator script |
| `testcases/M1-D3-001/` | 60 functional cases + 18 predicted defects + 9-chapter report |
| `lessons/` | 17 HTML lesson pages on mall4j business + test design |
| `reference/` | 15 one-page cheat sheets |
| `learning-records/` | 17 post-mortem write-ups |
| `.github/ISSUE_TEMPLATE/bug-report.md` | Standard bug-report form |

## How it's organized

```
testcases/
├── M1-D2-001/
│   ├── M1-D2-001-testcases.csv     # 90 rows, 11 columns
│   ├── M1-D2-001-testcases.md
│   └── generate-cases.py           # regenerable
└── M1-D3-001/
    ├── M1-D3-001-testcases.csv     # 60 rows
    ├── M1-D3-001-testcases.md
    ├── bug-list.csv                # 18 defects + header
    ├── bug-list.md                 # 491 lines, one section per defect
    ├── functional-test-report.md   # 9 chapters, 384 lines
    ├── generate-cases.py
    └── generate-bugs.py
```

## Defect distribution

Predicted from static reading of the source (Controller annotations + Param constraints + Service implementations + Security config) plus walking through the state machine for failure paths.

| Severity | Count | Examples |
|---|---|---|
| Critical | 3 | Auth bypass, order-state inconsistency, payment idempotency |
| Major | 6 | Missing validation, wrong error code, race condition |
| Minor | 6 | UI edge cases, message wording, redundant checks |
| Trivial | 3 | Logging gaps, formatting |

Total: **18 defects** across login (4), product (3), cart (3), order/payment (5), member/permission (3).

## Test report

`functional-test-report.md` has 9 chapters:

1. Overview (project background + scope)
2. Methodology (equivalence partitioning, boundary value, scenario testing, decision tables)
3. Environment (JDK17 + MySQL 8 + Redis 5 + mall4j dev profile)
4. Case summary (150 cases by module)
5. Defect summary (18 defects by severity)
6. Risk assessment
7. Conclusion
8. Improvement suggestions
9. Appendix (case index + defect list)

## How to use

### Browse cases

```bash
# D2: login / register / product / cart
column -t -s, testcases/M1-D2-001/M1-D2-001-testcases.csv | less

# D3: order / member / exception
column -t -s, testcases/M1-D3-001/M1-D3-001-testcases.csv | less

# 18 defects
column -t -s, testcases/M1-D3-001/bug-list.csv | less
```

### Regenerate cases

```bash
cd testcases/M1-D2-001 && python3 generate-cases.py
cd testcases/M1-D3-001 && python3 generate-cases.py
cd testcases/M1-D3-001 && python3 generate-bugs.py
```

### Read the report

```bash
# Markdown renders nicely on GitHub; or use a local viewer
glow testcases/M1-D3-001/functional-test-report.md
```

## Lessons

The `lessons/` directory has 17 HTML files written while working through the project. Topics range from "what mall4j does" (business overview) to "how I designed the cases" (methodology) to "how the 18 defects were predicted". They're standalone — open any in a browser.

## AGPLv3 note

mall4j is AGPL-3.0. This repo doesn't modify mall4j source — all cases, defects, and reports come from reading the public source + Swagger + the demo site. The companion automation repo ([mall4j-auto-test](../mall4j-auto-test)) has the pytest / Playwright / Locust code that runs against a local mall4j instance.

## Related

- [mall4j-auto-test](../mall4j-auto-test) — pytest + Playwright + CI + Locust scripts
- [agent-eval-practice](../agent-eval-practice) — Agent testing methodology (separate project)
- Source: [gz-yami/mall4j](https://github.com/gz-yami/mall4j)

## License

AGPL-3.0 (inherited from mall4j). All test cases, defects, reports, and lesson HTML are original work under the same license.
