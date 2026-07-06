# DevPortal SSO Migration — Raw Notes

Dumped from the planning thread, not in any particular order. Pull whatever's
actually needed.

- System affected: DevPortal (internal engineering portal).
- Background: DevPortal has run its own separate login system since 2019.
- What's changing: login is moving to the company's Okta-based SSO.
- Why: required to close a finding from the Q3 security compliance audit.
- Required action: every employee with a DevPortal account must re-link their
  account to Okta SSO.
- Deadline: August 14, 2026, 5:00 PM ET.
- Consequence of missing the deadline: accounts that aren't re-linked by then
  get locked out of DevPortal until IT manually restores access, which takes
  1-2 business days.
- How to complete the action: go to
  https://wiki.example-corp.internal/devportal-sso-migration and click
  "Relink Account." Takes about two minutes.
- Where to ask questions: #devportal-support on Slack —
  https://example-corp.slack.com/channels/devportal-support
- Unrelated, lower-priority note: DevPortal's dashboard also picked up a new
  dark mode theme this week, on by default, togglable in Settings. Not related
  to the SSO change.
- Rollout owner / team to sign off as: Platform Engineering.
