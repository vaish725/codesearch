# ReliefConnect

*NeuriX · George Hacks × United Nations — Reboot the Earth 2026 · Track 2, Problem Statement 3*

## Inspiration

We kept coming back to a single, uncomfortable fact: 821 million people go to bed food insecure every night — and that's on a *normal* day. When disaster strikes, the systems meant to help them collapse first. Aid gets delayed by 72 hours or more. Up to 40% of supplies are lost to poor coordination. People walk to distribution centers and find nothing.

The problem isn't generosity — donors and organizations step up. The problem is coordination. There's no shared picture of where food is, how much exists, or who needs it most. We wanted to build that picture.

> "The gap between who gets fed and who doesn't follows existing lines of poverty." — That line drove everything we designed.

## What we built

ReliefConnect is a real-time food coordination platform that connects four roles into one intelligent system: receivers, donors, shelter staff, and warehouse administrators. It's designed to activate *before* disaster strikes and stay operational through the crisis.

| Metric | Value |
|---|---|
| Sites coordinated per disaster zone | 12 (3 warehouses + 9 shelters) |
| Food items tracked | 15 (cultural + nutritional intelligence) |
| Deployment time for a new zone | 24 hours |

Key features we shipped:

- **Live stock intelligence** — Red/Yellow/Green availability levels per food category, updated in real time via Supabase Realtime across all dashboards simultaneously, no page refresh needed.
- **2-hour pickup reservations** — Receivers book a slot; expired reservations automatically revert inventory so nothing is locked and wasted.
- **Proximity-based routing** — Routes receivers to the nearest warehouse with stock, prioritizing highest-need locations first.
- **SMS broadcast via Twilio** — Instant alerts when shelters activate, requiring no internet connection on the receiver's end.
- **Household-size-aware allocation** — Larger families receive proportionally more, with equity baked directly into the algorithm.
- **Community donation incentives** — A points and redemption system rewards local donors, not just large NGOs and institutional actors.
- **Disaster countdown banner** — Always-visible countdown on every screen for every role, so urgency is never hidden from anyone in the system.

## How we built it

**Tech stack:** Next.js · React · TypeScript · Supabase · Supabase Realtime · Twilio · Tailwind CSS · Netlify · Vite

We built four purpose-built interfaces — one per role — all powered by the same Supabase backend. Supabase Realtime was central: every stock change, reservation, or shelter activation propagates instantly across every connected dashboard. No polling, no refresh.

Twilio handles SMS broadcasting so that receivers in low-connectivity environments can still get notified when a nearby shelter activates. We used a points ledger in Supabase to track donor credits, with scarcity-weighted rewards — donating a high-need item earns more than donating a surplus one.

The allocation algorithm reads household size from the receiver's profile and scales food quantities accordingly before generating a reservation. The expiry reversion logic runs as a Supabase Edge Function on a cron schedule, releasing any slot that hasn't been picked up within its 2-hour window.

## Challenges we faced

The hardest design challenge was building for *speed under pressure* across wildly different users — a warehouse manager at a laptop and a displaced family member on a 2G connection share the same underlying system. Every interaction had to be operable in a few taps with no tutorial.

We also wrestled with the tension between real-time accuracy and resilience. Supabase Realtime is excellent in connected environments, but we needed a fallback story for degraded networks. The SMS layer via Twilio addressed the most critical notification path, but offline-first inventory editing remains a planned improvement.

Modeling equity was surprisingly difficult. Simple per-person allocation seems fair but ignores family structure entirely. We landed on a household-size multiplier, but there's much more nuance to explore — dietary restrictions, medical needs, cultural food preferences — which is why we built 15 food items from the start rather than a flat "food" bucket.

## What we learned

- Coordination infrastructure is just as important as supply. You can have warehouses full of food and still fail to feed people if no one knows where to go.
- Local actors — community organizations, neighborhood markets, individual donors — are an underutilized resource in most relief frameworks. The points system exists specifically to bring them in.
- Designing for crisis is designing for the worst version of your user's context: low battery, high stress, poor connectivity, unfamiliar language. Constraints force clarity.
- Real-time sync across multiple user roles is technically achievable at hackathon pace, but requires careful schema design upfront — especially around reservation state machines.

## What's next

ReliefConnect is open source. The roadmap includes offline-first PWA support, deeper NGO pipeline integration, support for Global South deployments, and a predictive restocking layer to pre-position supplies before an event hits, with every event metrics being calculated synchronously.

We built this in 24 hours. Hunger doesn't wait for coordination - and neither did we.
