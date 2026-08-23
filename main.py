import json
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import yfinance as yf
import numpy as np

from simulation import (
    run_simulation_details,
    calculate_greeks,
    black_scholes_analytical,
    simulate_gbm_paths_with_Z,
    calculate_payoffs
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("options-simulator")

app = FastAPI(title="Options Pricing & Risk Simulator API")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SimulationRequest(BaseModel):
    ticker: Optional[str] = None
    spot: float = Field(..., gt=0)
    strike: float = Field(..., gt=0)
    vol: float = Field(..., gt=0)
    rate: float = Field(..., ge=0)
    days: int = Field(..., gt=0)
    sims: int = Field(..., ge=100, le=100000)
    steps: int = Field(252, gt=0)
    option_type: str = Field("call")
    style: str = Field("european")
    barrier: Optional[float] = Field(None)
    barrier_type: Optional[str] = Field(None)

@app.get("/ticker-info")
def get_ticker_info(ticker: str):
    """
    Fetches the current spot price and estimates the 30-day historical volatility
    for a given ticker using Yahoo Finance.
    """
    symbol = ticker.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="Ticker symbol cannot be empty")
        
    try:
        logger.info(f"Fetching data for ticker: {symbol}")
        yf_ticker = yf.Ticker(symbol)
        
        # Fetch 3 months of history for a robust volatility estimation
        hist = yf_ticker.history(period="3mo")
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No data found for ticker {symbol}")
            
        spot = float(hist['Close'].iloc[-1])
        
        # Calculate historical volatility (standard deviation of daily log returns, annualized)
        close_prices = hist['Close']
        log_returns = np.log(close_prices / close_prices.shift(1)).dropna()
        
        if len(log_returns) > 1:
            # Assuming 252 trading days in a year
            vol = float(np.std(log_returns, ddof=1) * np.sqrt(252))
        else:
            vol = 0.25 # Fallback default 25% volatility
            
        return {
            "ticker": symbol,
            "spot": round(spot, 2),
            "volatility": round(vol, 4)
        }
    except Exception as e:
        logger.error(f"Error fetching ticker {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch ticker data: {str(e)}")

@app.post("/simulate")
def simulate_option(req: SimulationRequest):
    """
    Synchronous HTTP endpoint for option simulation.
    """
    T = req.days / 365.0
    
    try:
        # Run simulation
        sim_res = run_simulation_details(
            S0=req.spot,
            K=req.strike,
            vol=req.vol,
            rate=req.rate,
            T=T,
            steps=req.steps,
            sims=req.sims,
            option_type=req.option_type,
            style=req.style,
            barrier=req.barrier,
            barrier_type=req.barrier_type,
            seed=42 # Fixed seed for consistency
        )
        
        # Run Greeks calculations using the Z from simulation
        greeks = calculate_greeks(
            S0=req.spot,
            K=req.strike,
            vol=req.vol,
            rate=req.rate,
            T=T,
            steps=req.steps,
            Z=sim_res["Z"],
            option_type=req.option_type,
            style=req.style,
            barrier=req.barrier,
            barrier_type=req.barrier_type
        )
        
        # Black-Scholes analytical benchmarks for European style
        bs_benchmark = None
        if req.style.lower() == "european":
            bs_benchmark = black_scholes_analytical(
                S0=req.spot,
                K=req.strike,
                T=T,
                r=req.rate,
                sigma=req.vol,
                option_type=req.option_type
            )
            
        return {
            "price": sim_res["price"],
            "std_err": sim_res["std_err"],
            "sample_paths": sim_res["sample_paths"],
            "payoff_distribution": sim_res["payoff_distribution"],
            "convergence": sim_res["convergence"],
            "greeks": greeks,
            "bs_benchmark": bs_benchmark
        }
    except Exception as e:
        logger.error(f"Simulation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")

@app.websocket("/simulate-ws")
async def simulate_option_ws(websocket: WebSocket):
    """
    WebSocket endpoint that streams simulation progress and convergence
    before sending the final output.
    """
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        # Wait for the client parameters
        data = await websocket.receive_text()
        params = json.loads(data)
        
        # Extract parameters
        spot = float(params["spot"])
        strike = float(params["strike"])
        vol = float(params["vol"])
        rate = float(params["rate"])
        days = int(params["days"])
        sims = int(params["sims"])
        steps = int(params.get("steps", 252))
        option_type = str(params.get("option_type", "call"))
        style = str(params.get("style", "european"))
        barrier = float(params["barrier"]) if params.get("barrier") is not None else None
        barrier_type = str(params["barrier_type"]) if params.get("barrier_type") else None
        
        T = days / 365.0
        
        # Generate all random steps Z at once so we can stream chunks and compute Greeks accurately
        # Fixed seed for reproducibility
        np.random.seed(42)
        Z = np.random.standard_normal((sims, steps))
        
        # Stream calculations in chunks (e.g., 10 chunks)
        num_chunks = min(10, sims)
        chunk_size = sims // num_chunks
        
        accumulated_payoffs = []
        discount_factor = np.exp(-rate * T)
        
        for chunk_idx in range(num_chunks):
            start_idx = chunk_idx * chunk_size
            # Adjust end index for the last chunk to catch rounding issues
            end_idx = sims if chunk_idx == num_chunks - 1 else (chunk_idx + 1) * chunk_size
            
            chunk_Z = Z[start_idx:end_idx]
            chunk_paths = simulate_gbm_paths_with_Z(spot, rate, vol, T, steps, chunk_Z)
            chunk_payoffs = calculate_payoffs(chunk_paths, strike, option_type, style, barrier, barrier_type)
            
            # Apply discounting
            discounted_chunk_payoffs = chunk_payoffs * discount_factor
            accumulated_payoffs.extend(discounted_chunk_payoffs.tolist())
            
            # Send progress update
            running_mean = float(np.mean(accumulated_payoffs))
            running_std_err = float(np.std(accumulated_payoffs) / np.sqrt(len(accumulated_payoffs)))
            progress = int(((chunk_idx + 1) / num_chunks) * 100)
            
            await websocket.send_json({
                "type": "progress",
                "progress": progress,
                "current_price": running_mean,
                "current_std_err": running_std_err
            })
            
            # Brief pause to simulate compute time / let the UI animate nicely
            # (Remove or reduce in production, but great for visualization)
            import asyncio
            await asyncio.sleep(0.1)
            
        # Complete full simulation calculations
        # Generate full paths for sample & payoff distribution
        full_paths = simulate_gbm_paths_with_Z(spot, rate, vol, T, steps, Z)
        full_payoffs = calculate_payoffs(full_paths, strike, option_type, style, barrier, barrier_type)
        discounted_full_payoffs = full_payoffs * discount_factor
        
        price = float(np.mean(discounted_full_payoffs))
        std_err = float(np.std(discounted_full_payoffs) / np.sqrt(sims))
        
        # Take 50 paths for UI plot
        sample_indices = np.random.choice(sims, min(50, sims), replace=False)
        sample_paths = full_paths[sample_indices].tolist()
        
        # Payoff distribution
        counts, bin_edges = np.histogram(discounted_full_payoffs, bins=30)
        payoff_distribution = [
            {"binStart": float(bin_edges[i]), "binEnd": float(bin_edges[i+1]), "count": int(counts[i])}
            for i in range(len(counts))
        ]
        
        # Convergence
        running_avg_points = []
        c_chunk = max(1, sims // 100)
        for i in range(c_chunk, sims + 1, c_chunk):
            running_avg_points.append({
                "sims": i,
                "price": float(np.mean(discounted_full_payoffs[:i]))
            })
            
        # Greeks via finite difference (Common Random Numbers)
        greeks = calculate_greeks(
            S0=spot,
            K=strike,
            vol=vol,
            rate=rate,
            T=T,
            steps=steps,
            Z=Z,
            option_type=option_type,
            style=style,
            barrier=barrier,
            barrier_type=barrier_type
        )
        
        # Black-Scholes analytical benchmark for European style
        bs_benchmark = None
        if style.lower() == "european":
            bs_benchmark = black_scholes_analytical(
                S0=spot,
                K=strike,
                T=T,
                r=rate,
                sigma=vol,
                option_type=option_type
            )
            
        # Send final completed results
        await websocket.send_json({
            "type": "complete",
            "results": {
                "price": price,
                "std_err": std_err,
                "sample_paths": sample_paths,
                "payoff_distribution": payoff_distribution,
                "convergence": running_avg_points,
                "greeks": greeks,
                "bs_benchmark": bs_benchmark
            }
        })
        
    except WebSocketDisconnect:
        logger.info("Client disconnected from WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
    finally:
        await websocket.close()
