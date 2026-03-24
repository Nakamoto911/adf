# PSY (2015) Multiple Bubbles — Reference Card

## Data
- **Series**: S&P 500 real price–dividend ratio (price/dividend)
- **Source**: Robert Shiller's website (real S&P 500 price index & real dividend)
- **Period**: Jan 1871 – Dec 2010
- **Frequency**: Monthly
- **Observations**: T = 1,680

## Model Spec

### Null hypothesis
y_t = dT^{-η} + θ y_{t-1} + ε_t,  ε_t ~ iid(0, σ²),  θ = 1

Paper focuses on η > 1/2 (drift negligible relative to stochastic trend). Empirical: d = η = 1.

### ADF regression (rolling window from r₁ to r₂)
Δy_t = α̂_{r₁,r₂} + β̂_{r₁,r₂} y_{t-1} + Σᵢ₌₁ᵏ ψ̂ⁱ_{r₁,r₂} Δy_{t-i} + ε̂_t

Window size (fraction): r_w = r₂ − r₁. Obs in window: T_w = ⌊T r_w⌋.

### Test statistics

| Statistic | Definition |
|-----------|-----------|
| ADF^{r₂}_{r₁} | t-ratio of β̂ from regression on [r₁, r₂] |
| SADF(r₀) | sup_{r₂∈[r₀,1]} ADF^{r₂}_0  (PWY test) |
| GSADF(r₀) | sup_{r₂∈[r₀,1], r₁∈[0,r₂−r₀]} ADF^{r₂}_{r₁} |
| BSADF_{r₂}(r₀) | sup_{r₁∈[0,r₂−r₀]} ADF^{r₂}_{r₁}  (backward SADF — used for date-stamping) |

### Minimum window size rule
r₀ = 0.01 + 1.8/√T

For T = 1,680: r₀ ≈ 0.054 → smallest window ≈ 90 obs.

## Pipeline
1. Compute price–dividend ratio series y_t = P_t / D_t (both real).
2. Set r₀ via rule above.
3. **GSADF test** (ex post): double recursion over r₁ ∈ [0, r₂−r₀], r₂ ∈ [r₀, 1]. Report sup ADF stat.
4. **Date-stamping** (ex ante / real-time): for each r₂ from r₀ to 1, compute BSADF_{r₂}(r₀). Compare to 95% critical value sequence scv^{β_T}_{r₂}.
5. **Bubble origination**: r̂_e = inf{r₂ ∈ [r₀,1] : BSADF_{r₂}(r₀) > scv^{β_T}_{r₂}}
6. **Bubble termination**: r̂_f = inf{r₂ ∈ [r̂_e + δ log(T)/T, 1] : BSADF_{r₂}(r₀) < scv^{β_T}_{r₂}}
7. After termination, repeat from step 5 to find subsequent bubbles.

### Minimum bubble duration
δ log(T) observations, where δ is frequency-dependent. For monthly data with T = 1,680: log(1680) ≈ 7.4.

## Hyperparameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Lag order k | 0 | Fixed; paper recommends small fixed lag for size control |
| Significance level β_T | 0.05 | Fixed at 5% in empirical application |
| r₀ | 0.01 + 1.8/√T | ≈ 0.054 for T = 1,680; gives 90-obs minimum window |
| Critical values | Finite-sample Monte Carlo | 2,000 replications, T = 1,680 |
| Min bubble duration | δ log(T) | Frequency-dependent δ |

## Critical Values (from paper)

### Asymptotic (Table 1, r₀ ≈ 0.055)
| | 90% | 95% | 99% |
|---|---|---|---|
| SADF | 1.23 | 1.51 | 2.06 |
| GSADF | 2.08 | 2.30 | 2.74 |

### Finite sample T = 1,680 (Table 8)
| | 90% | 95% | 99% |
|---|---|---|---|
| SADF | 1.30 | 1.59 | 2.14 |
| GSADF | 2.17 | 2.34 | 2.74 |

## Results

### Summary test statistics (Table 8)
| Test | Statistic | Subsample yielding sup |
|------|-----------|----------------------|
| SADF | 3.30 | 1871M01–2000M07 |
| GSADF | 4.21 | 1976M04–1999M06 |

Both reject at 1%.

### PSY date-stamped bubble episodes (Figure 7, 95% BSADF cv)
| Episode | Start | End |
|---------|-------|-----|
| Post long-depression | 1879M10 | 1880M04 |
| 1917 crash (downturn) | 1917M08 | 1918M04 |
| Great crash | 1928M11 | 1929M10 |
| Postwar boom | 1955M01 | 1956M04 |
| Black Monday | 1986M06 | 1987M09 |
| Dot-com bubble | 1995M11 | 2001M08 |
| Subprime (downturn) | 2009M02 | 2009M04 |

### PWY (SADF) date-stamped episodes (Figure 8)
Only 2 episodes: post long-depression (1879M10–1880M04), dot-com (1997M07–2001M08).

### Sequential PWY (Figure 9)
Same 2 episodes as PWY.

### CUSUM (Figure 10)
3 episodes: post long-depression (1879M10–1880M04), great crash (1929M07–1929M09), dot-com (1997M02–2002M05).

## Simulation DGP Specs

### Evans collapsing bubble (Eqs 23–26)
- D_t = μ + D_{t-1} + ε_{D,t},  ε_{D,t} ~ N(0, σ²_D)
- P^f_t = μρ/(1−ρ)² + ρ/(1−ρ) · D_t
- B_{t+1} = ρ⁻¹ B_t ε_{B,t+1}  if B_t < b
- B_{t+1} = [ζ + (πρ)⁻¹ θ_{t+1}(B_t − ρζ)] ε_{B,t+1}  if B_t ≥ b
- ε_{B,t} = exp(y_t − τ²/2),  y_t ~ N(0, τ²);  θ_t ~ Bernoulli(π)
- P_t = P^f_t + κ B_t

| Param | Value |
|-------|-------|
| μ | 0.0024 |
| σ²_D | 0.0010 |
| D₀ | 1.0 |
| ρ | 0.985 (varied 0.975–0.999) |
| b | 1 |
| B₀ | 0.50 |
| π | 0.85 (varied 0.99–0.25) |
| ζ | 0.50 |
| τ | 0.05 |
| κ | 20 |

### Mildly explosive DGP (Eqs 9, 12)
- y₀ = 100, σ = 6.79, c = 1, α = 0.6, T = 100
- δ_T = 1 + c T^{−α}
- Single bubble: τ_e = ⌊0.4T⌋, duration = ⌊0.15T⌋
- Two bubbles: τ_{1e} = ⌊0.2T⌋, τ_{2e} = ⌊0.6T⌋, durations ⌊0.20T⌋ and ⌊0.10T⌋

### GARCH size check (Eqs 20–22)
- d = η = 1, y₀ = 376.8, ω = 30.69, α = 0, β = 0.61
- MLE from S&P 500 P/D ratio Jan 2004–Dec 2007

## Key Consistency Results (Section 3.2)

- **PWY**: consistent for 1st bubble; fails to detect 2nd bubble when 1st has longer duration. If 1st shorter, detects 2nd but with delayed origination: r̂_{2e} →^p r_{2e} + r_{1f} − r_{1e}.
- **PSY (BSADF)**: consistent for both bubbles under rate condition 1/scv^{β_T} + scv^{β_T}/T^{1−α/2} → 0.
- **Seq PWY**: consistent for both bubbles (with re-initialization).
- Rate condition requires cv → ∞ but slower than T^{1−α/2}. log(T) rate suffices.
- Condition r₀ ≤ r_{1e} needed to identify first bubble. For multiple bubbles: r₀ < r_{2e} − r_{1f}.

## Undisclosed
- Exact δ value used for minimum bubble duration in empirical application (frequency-dependent, not specified for monthly)
- Whether P/D ratio is level or log in empirical application (text suggests level; log discussed in footnote 6)
- Detrending method for CUSUM: regression on constant + linear trend — but exact specification of detrended series for the other tests not detailed
- How to handle the BSADF critical value sequence scv^{β_T}_{r₂}: paper says Monte Carlo with 2,000 reps but doesn't specify if these are sample-size-specific for each r₂ or based on full-sample quantiles
- ADF lag order selection for critical value simulation (presumably k = 0 to match empirical spec)
- Exact CUSUM training sample handling and re-initialization after collapse detection
