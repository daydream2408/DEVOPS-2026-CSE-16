import "@testing-library/jest-dom";

// jsdom doesn't implement ResizeObserver, but recharts' ResponsiveContainer needs it
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};
