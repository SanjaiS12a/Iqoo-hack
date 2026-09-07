import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "./App";

describe("ClassMind application shell", () => {
  it("offers direct student and teacher demo entry points", () => {
    localStorage.clear();
    render(
      <QueryClientProvider client={new QueryClient()}>
        <App />
      </QueryClientProvider>,
    );

    expect(screen.getByRole("heading", { name: /every learner understood/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /enter as student/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /enter as teacher/i })).toBeInTheDocument();
  });
});
