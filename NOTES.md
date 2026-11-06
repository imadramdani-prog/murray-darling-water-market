# Research notes

## Question
How well do storage and weather fundamentals explain water allocation prices
in the southern Murray-Darling Basin, and has this relationship changed since 2016?
If it has, what might explain the shift?

## Scope
- Market: water allocations (spot), southern Murray-Darling Basin
- Period: 2000 to present
- Out of scope for now: entitlements, northern basin

## Data
Source: ABARES, Murray-Darling Basin Water Market Catchment Dataset 2021
(Supply tables), CC BY 4.0. https://doi.org/10.25814/wvk8-5n34

- Panel data: one row per region per financial year (2001 = 2000-01)
- Southern regions kept (9): NSW Lower Darling, NSW Murray Above,
  NSW Murray Below, NSW Murrumbidgee, SA Murray, VIC Goulburn-Broken,
  VIC Loddon-Campaspe, VIC Murray Above, VIC Murray Below

Key variables:
- P: average allocation price, $/ML, real 2019-20 dollars (target)
- R: annual rainfall, mm (August to May)
- a_High, a_Low: allocation %, high and low reliability
- C_High, C_Low: carryover from previous year, ML
- D_High, D_Low: share of entitlements recovered for the environment
- T_Irrig: net allocation trade into the region, ML

Data issues:
- No dam storage variable: allocation % is used as the supply measure
- C_High is negative in some NSW years (small values): to document
- Environmental columns (F_Env, G_Env, C_Env) are mostly empty: not used
- Entitlement volumes (E_*) are fixed at 2020-21 levels: not a time-varying driver

## Roadmap

Version 1 (2001-2021, ABARES data)
- Panel regression with region fixed effects
- Structural break test at 2016 (Chow test)
- Out-of-sample test: train on 2001-2016, predict 2017-2021
- Effective allocation = allocation x (1 - environmental share)
- Compare results with ABARES estimates (related work)

Version 2 (main new contribution)
- Extend the data beyond 2021 to the present
- Test whether the post-2016 price premium persists in later years
- Interactive dashboard with a scenario simulator
- Price scenarios for next season (dry, average, wet)