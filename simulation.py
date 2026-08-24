import numpy as np
from scipy.stats import norm

def simulate_gbm_paths_with_Z(S0, r, sigma, T, steps, Z):
    """
    Simulates Geometric Brownian Motion paths using a pre-generated set of random normals Z.
    Z has shape (sims, steps)
    """
    sims = Z.shape[0]
    dt = T / steps
    # S_t = S_0 * exp( (r - 0.5 * sigma^2) * dt + sigma * sqrt(dt) * Z_t )
    drift = (r - 0.5 * (sigma ** 2)) * dt
    diffusion = sigma * np.sqrt(dt) * Z
    increments = np.exp(drift + diffusion)
    
    paths = np.empty((sims, steps + 1))
    paths[:, 0] = S0
    paths[:, 1:] = S0 * np.cumprod(increments, axis=1)
    return paths

def calculate_payoffs(paths, K, option_type="call", style="european", barrier=None, barrier_type=None):
    """
    Calculates option payoffs for each path.
    """
    option_type = option_type.lower()
    style = style.lower()
    
    # European or path-dependent terminal values
    if style == "european":
        terminal_prices = paths[:, -1]
        if option_type == "call":
            payoffs = np.maximum(terminal_prices - K, 0)
        else:
            payoffs = np.maximum(K - terminal_prices, 0)
            
    elif style == "asian":
        # Arithmetic average of paths (including starting price)
        avg_prices = np.mean(paths, axis=1)
        if option_type == "call":
            payoffs = np.maximum(avg_prices - K, 0)
        else:
            payoffs = np.maximum(K - avg_prices, 0)
            
    elif style == "barrier":
        if barrier is None or barrier_type is None:
            raise ValueError("Barrier level and type must be specified for barrier options")
        
        terminal_prices = paths[:, -1]
        barrier_type = barrier_type.lower()
        
        # Calculate European payoffs
        if option_type == "call":
            base_payoffs = np.maximum(terminal_prices - K, 0)
        else:
            base_payoffs = np.maximum(K - terminal_prices, 0)
            
        # Determine path breaching of barrier
        # paths shape: (sims, steps + 1)
        if barrier_type == "up-and-out":
            # Breached if any price is >= barrier
            breached = np.any(paths >= barrier, axis=1)
            payoffs = np.where(breached, 0.0, base_payoffs)
        elif barrier_type == "down-and-out":
            # Breached if any price is <= barrier
            breached = np.any(paths <= barrier, axis=1)
            payoffs = np.where(breached, 0.0, base_payoffs)
        elif barrier_type == "up-and-in":
            # Active if any price is >= barrier
            active = np.any(paths >= barrier, axis=1)
            payoffs = np.where(active, base_payoffs, 0.0)
        elif barrier_type == "down-and-in":
            # Active if any price is <= barrier
            active = np.any(paths <= barrier, axis=1)
            payoffs = np.where(active, base_payoffs, 0.0)
        else:
            raise ValueError(f"Unknown barrier type: {barrier_type}")
            
    else:
        raise ValueError(f"Unknown option style: {style}")
        
    return payoffs

def run_simulation_details(S0, K, vol, rate, T, steps, sims, option_type, style, barrier=None, barrier_type=None, seed=None):
    """
    Runs the base simulation, returns:
    - price
    - standard error
    - payoff distribution
    - sample of 50 paths
    - running average price (for convergence)
    - Z matrix used (for reuse in Greeks calculation)
    """
    if seed is not None:
        np.random.seed(seed)
        
    Z = np.random.standard_normal((sims, steps))
    paths = simulate_gbm_paths_with_Z(S0, rate, vol, T, steps, Z)
    payoffs = calculate_payoffs(paths, K, option_type, style, barrier, barrier_type)
    
    # Discount payoffs to present value
    discount_factor = np.exp(-rate * T)
    discounted_payoffs = payoffs * discount_factor
    
    price = np.mean(discounted_payoffs)
    std_err = np.std(discounted_payoffs) / np.sqrt(sims)
    
    # 50 sample paths for visualization
    sample_indices = np.random.choice(sims, min(50, sims), replace=False)
    sample_paths = paths[sample_indices].tolist()
    
    # Payoff distribution (histogram data)
    counts, bin_edges = np.histogram(discounted_payoffs, bins=30)
    payoff_distribution = [
        {"binStart": float(bin_edges[i]), "binEnd": float(bin_edges[i+1]), "count": int(counts[i])}
        for i in range(len(counts))
    ]
    
    # Convergence data (running average)
    # To avoid huge arrays on frontend, send 100 points along the simulation count
    running_avg_points = []
    chunk_size = max(1, sims // 100)
    for i in range(chunk_size, sims + 1, chunk_size):
        running_avg_points.append({
            "sims": i,
            "price": float(np.mean(discounted_payoffs[:i]))
        })
        
    return {
        "price": float(price),
        "std_err": float(std_err),
        "sample_paths": sample_paths,
        "payoff_distribution": payoff_distribution,
        "convergence": running_avg_points,
        "Z": Z
    }

def calculate_greeks(S0, K, vol, rate, T, steps, Z, option_type, style, barrier=None, barrier_type=None):
    """
    Calculates Delta, Gamma, Vega using Common Random Numbers (reusing Z)
    """
    # Perturbations
    dS = 0.01 * S0
    dvol = 0.01
    
    # Helper to price option with a specific S0, vol, and reused Z
    def price_with_params(temp_S0, temp_vol):
        temp_paths = simulate_gbm_paths_with_Z(temp_S0, rate, temp_vol, T, steps, Z)
        temp_payoffs = calculate_payoffs(temp_paths, K, option_type, style, barrier, barrier_type)
        return float(np.mean(temp_payoffs * np.exp(-rate * T)))
        
    # Spot variations for Delta & Gamma
    V_base = price_with_params(S0, vol)
    V_up = price_with_params(S0 + dS, vol)
    V_down = price_with_params(S0 - dS, vol)
    
    # Vol variations for Vega
    V_vol_up = price_with_params(S0, vol + dvol)
    V_vol_down = price_with_params(S0, vol - dvol)
    
    # Central difference calculations
    delta = (V_up - V_down) / (2 * dS)
    gamma = (V_up - 2 * V_base + V_down) / (dS ** 2)
    vega = (V_vol_up - V_vol_down) / (2 * dvol)
    
    return {
        "delta": float(delta),
        "gamma": float(gamma),
        "vega": float(vega)
    }

def black_scholes_analytical(S0, K, T, r, sigma, option_type="call"):
    """
    Analytical Black-Scholes price and Greeks for European option.
    """
    option_type = option_type.lower()
    
    if T <= 0 or sigma <= 0 or S0 <= 0 or K <= 0:
        return {"price": 0.0, "delta": 0.0, "gamma": 0.0, "vega": 0.0}
        
    d1 = (np.log(S0 / K) + (r + 0.5 * (sigma ** 2)) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    n_d1 = norm.cdf(d1)
    n_d2 = norm.cdf(d2)
    pdf_d1 = norm.pdf(d1)
    
    if option_type == "call":
        price = S0 * n_d1 - K * np.exp(-r * T) * n_d2
        delta = n_d1
    else:
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S0 * norm.cdf(-d1)
        delta = n_d1 - 1.0
        
    gamma = pdf_d1 / (S0 * sigma * np.sqrt(T))
    vega = S0 * np.sqrt(T) * pdf_d1
    
    return {
        "price": float(price),
        "delta": float(delta),
        "gamma": float(gamma),
        "vega": float(vega)
    }
