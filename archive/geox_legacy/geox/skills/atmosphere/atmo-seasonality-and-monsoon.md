---
id: geox.atmosphere.seasonality-and-monsoon
title: Seasonality and Monsoon
domain: atmosphere
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: low
  human_confirmation: false
substrates: [orbital, environment-field]
scales: [region, nation, maritime]
horizons: [medium, long]
inputs: [climatology, sea-surface-temperature, wind-regime, historical-onset]
outputs: [seasonal-outlook, monsoon-window, haze-probability, operational-calendar]
depends_on: [geox.atmosphere.weather-state]
legal_domain: public
status: draft
runtime:
  cache_ttl_sec: 86400
  read_only: true
---

# atmo-seasonality-and-monsoon

Seasonal drift, monsoon windows, haze, rain regime, and operational calendar effects.

## Contract

**Inputs:** climatology, sea-surface-temperature, wind-regime, historical-onset
**Outputs:** seasonal-outlook, monsoon-window, haze-probability, operational-calendar

## Behavior

Compute seasonal atmospheric patterns and long-horizon outlooks. Identify monsoon onset, haze seasons, and operational constraints.

## Edges

← atmo-weather-state
