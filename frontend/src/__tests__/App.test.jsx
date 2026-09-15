import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import App from "../App.jsx";

beforeEach(() => {
  global.fetch = vi.fn();
});

describe("App", () => {
  it("renders the main heading", () => {
    render(<App />);
    expect(
      screen.getByText(/Monte Carlo Options Pricing/i)
    ).toBeInTheDocument();
  });

  it("renders the Run Simulation button", () => {
    render(<App />);
    expect(
      screen.getByRole("button", { name: /Run Simulation/i })
    ).toBeInTheDocument();
  });

  it("calls the /simulate endpoint on submit and shows price", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        price: 0.71,
        std_err: 0.01,
        greeks: { delta: 0.2, gamma: 0.05, vega: 8.3 },
        bs_benchmark: { price: 0.73, delta: 0.21, gamma: 0.05, vega: 8.4 },
        convergence: [{ sims: 100, price: 0.7 }],
        sample_paths: [[100, 101, 102]],
        payoff_distribution: [{ binStart: 0, binEnd: 1, count: 5 }],
      }),
    });

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: /Run Simulation/i }));

    await waitFor(() => {
      expect(screen.getByText("$0.7100")).toBeInTheDocument();
    });

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/simulate"),
      expect.objectContaining({ method: "POST" })
    );
  });

  it("shows an error message when the API call fails", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: "Simulation error" }),
    });

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: /Run Simulation/i }));

    await waitFor(() => {
      expect(screen.getByText(/Simulation error/i)).toBeInTheDocument();
    });
  });
});
