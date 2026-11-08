# Spec — ClaimProof (working name)

**Status: validation only. Do not write product code until interview results are in.**

## One-liner
Verified capture and risk scoring for damage and shortage claims that retailers send to mid-size
distributors, replacing "email us a photo" with evidence that's authenticated and matched to the shipment.

## Why this gap
- Detecting fake photos is becoming a commodity feature (insurers build their own; ecommerce
  returns tools and Shopify apps already exist). Don't compete on detection accuracy.
- Mid-size distributors ($5M–$100M revenue) selling to many small accounts handle claims by email;
  account managers often issue credits before validating shipment evidence.
- Enterprise deduction tools target manufacturers vs. big-box retailers, not this segment.

## Target customer
Distributors and wholesalers selling damage-prone or high-value goods (electronics, glass/ceramics,
furniture, lighting, beverage, building products, medical supplies) to many independent accounts.
Buyer: controller/CFO. User: AR / customer service. Ally: warehouse/ops.

## Riskiest assumptions (test in interviews)
1. Unverified credits are a meaningful dollar amount per year.
2. Distributors' customers will accept a capture link (likely the deal-breaker).
3. Someone owns the problem and has budget.

## MVP (only after validation passes)
1. **Claim intake link:** customer enters order/invoice number.
2. **Verified capture page:** camera-only browser capture (no gallery upload), server timestamp,
   optional geolocation, random challenge code in frame, required shots (label, carton, damage, wide).
   Note: virtual-camera spoofing remains possible; this raises the cost of fraud, it doesn't eliminate it.
3. **Checks:** licensed AI-image/manipulation detection API; perceptual-hash duplicate detection across all
   past claims and accounts; Claude vision match of item/label vs. invoice SKU; claimed vs. shipped quantity;
   account claim-rate vs. peers.
4. **Reviewer queue:** risk score with plain-language reasons; approve / request more / deny;
   export credit memo line or carrier claim packet (PDF).

Stack: Next.js on Vercel, Supabase (db, auth, photo storage), Claude API, third-party detection API.

## Pricing hypotheses
Per claim ($3–8) or monthly tiers by claim volume, anchored to credits avoided.
Example to test (not real data): $250k/year in credits, 8% reduction → $20k saved → supports $500–800/month.

## Risks
Customer friction (mitigate: require link only above a $ threshold or for high-claim accounts);
false positives damaging relationships; detection decay as generators improve; long finance sales cycles.
