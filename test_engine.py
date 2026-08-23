import numpy as np
from simulation import run_simulation_details, black_scholes_analytical, calculate_greeks

def test_european_convergence():
    print("Testing European Option Price Convergence...")
    S0 = 100.0
    K = 100.0
    vol = 0.20
    rate = 0.05
    days = 365
    T = days / 365.0
    sims = 20000
    steps = 100
    
    # 1. Analytical price
    bs = black_scholes_analytical(S0, K, T, rate, vol, "call")
    print(f"  Black-Scholes Price: ${bs['price']:.5f}")
    
    # 2. Monte Carlo price
    sim_res = run_simulation_details(
        S0=S0, K=K, vol=vol, rate=rate, T=T, steps=steps, sims=sims,
        option_type="call", style="european", seed=42
    )
    mc_price = sim_res["price"]
    std_err = sim_res["std_err"]
    print(f"  Monte Carlo Price:  ${mc_price:.5f} (Std Err: ±{std_err:.5f})")
    
    # Check if BS price is within 3 standard errors of MC price (99.7% confidence interval)
    diff = abs(mc_price - bs["price"])
    within_bounds = diff <= 3.0 * std_err
    print(f"  Difference: {diff:.5f} | 3*StdErr: {3*std_err:.5f}")
    assert within_bounds, "Monte Carlo price did not converge to Black-Scholes price within 3 standard errors!"
    print("  [PASS] European option price converged successfully.\n")

def test_barrier_options():
    print("Testing Barrier Option Payoffs...")
    S0 = 100.0
    K = 100.0
    vol = 0.20
    rate = 0.05
    days = 90
    T = days / 365.0
    sims = 1000
    steps = 50
    
    # Up-and-out call option: if spot rises above 120, payoff should knock out to 0
    # Let's verify that the barrier option price is strictly less than the European option price
    euro_res = run_simulation_details(
        S0=S0, K=K, vol=vol, rate=rate, T=T, steps=steps, sims=sims,
        option_type="call", style="european", seed=100
    )
    
    barrier_res = run_simulation_details(
        S0=S0, K=K, vol=vol, rate=rate, T=T, steps=steps, sims=sims,
        option_type="call", style="barrier", barrier=110.0, barrier_type="up-and-out", seed=100
    )
    
    print(f"  European Call Price:  ${euro_res['price']:.5f}")
    print(f"  Up-and-Out Call Price (Barrier=110): ${barrier_res['price']:.5f}")
    
    assert barrier_res["price"] < euro_res["price"], "Barrier price should be cheaper than European price due to knock-out probability!"
    print("  [PASS] Barrier knock-out logic functioning correctly.\n")

def test_greeks_stability():
    print("Testing Monte Carlo Greeks via Finite Difference...")
    S0 = 100.0
    K = 100.0
    vol = 0.20
    rate = 0.05
    days = 180
    T = days / 365.0
    steps = 100
    sims = 20000
    
    # BS Greeks
    bs = black_scholes_analytical(S0, K, T, rate, vol, "call")
    print(f"  BS Delta: {bs['delta']:.5f} | BS Gamma: {bs['gamma']:.5f} | BS Vega (per 1%): {(bs['vega']/100):.5f}")
    
    # MC Greeks (runs using the same seed to preserve CRN)
    sim_res = run_simulation_details(
        S0=S0, K=K, vol=vol, rate=rate, T=T, steps=steps, sims=sims,
        option_type="call", style="european", seed=123
    )
    mc_greeks = calculate_greeks(
        S0=S0, K=K, vol=vol, rate=rate, T=T, steps=steps, Z=sim_res["Z"],
        option_type="call", style="european"
    )
    print(f"  MC Delta: {mc_greeks['delta']:.5f} | MC Gamma: {mc_greeks['gamma']:.5f} | MC Vega (per 1%): {(mc_greeks['vega']/100):.5f}")
    
    # Assert Delta is within a reasonable tolerance
    assert abs(mc_greeks["delta"] - bs["delta"]) < 0.02, "MC Delta is too far from analytical value!"
    assert abs(mc_greeks["gamma"] - bs["gamma"]) < 0.01, "MC Gamma is too far from analytical value!"
    assert abs((mc_greeks["vega"]/100) - (bs["vega"]/100)) < 0.02, "MC Vega is too far from analytical value!"
    print("  [PASS] Finite-difference Greeks are stable and close to analytical benchmarks.\n")

if __name__ == "__main__":
    print("=== RUNNING MONTE CARLO QUANT TEST SUITE ===\n")
    test_european_convergence()
    test_barrier_options()
    test_greeks_stability()
    print("All tests passed successfully!")
