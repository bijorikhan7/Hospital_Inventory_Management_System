/// <reference types="vitest/globals" />
import { render, screen } from "@testing-library/react";
import { Badge } from "../components/Badge";

describe("Badge", () => {
  it("renders status text", () => {
    render(<Badge value="ASSIGNED" />);
    expect(screen.getByText("ASSIGNED")).toBeInTheDocument();
  });
});
