# Atlas CRM Rollout Leadership Update
Audience: Executive Leadership Team
Date: July 6, 2026

## Summary
The Atlas CRM rollout was paused on July 2, 2026 after duplicate account creation affected 38 customers during the planned July 1, 2026 cutover. The customer-facing issue was fixed on July 3, 2026 at 2:20 PM ET, and duplicate records were fully removed by July 4, 2026 at 9:00 AM ET. We need leadership approval for a temporary freeze on non-critical CRM releases through July 15, 2026 while the team completes rollout safeguards.

## Key Changes
- **Status:** The rollout remains paused after the duplicate account issue, even though customer-facing behavior was restored and cleanup is complete.
- **Root Cause:** A retry job replayed idempotency tokens after a queue failover, which created the duplicate account records.
- **Schedule:** The self-serve territory management launch moved from July 8, 2026 to July 15, 2026 while the team adds a replay guard and extends rollout validation.

## Impact and Risks
- **Impact:** 38 customers were affected by duplicate account creation, but there was no data loss and no security incident.
- **Risk/Decision:** Restarting without tighter controls would increase repeat-incident risk, so approval is needed to freeze non-critical CRM releases through July 15, 2026 while mitigation work is completed.

## Next Steps
1. Add the replay guard before restarting the rollout and expand the canary window from 15 minutes to 60 minutes.
2. Return to leadership with a restart recommendation after the freeze decision and mitigation checks are complete.
