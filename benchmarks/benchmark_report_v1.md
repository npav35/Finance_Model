# Performance Benchmark Report
**Date:** 2025-12-29
**Version:** v1

> [!NOTE]
> Prerequisites:
> 1. Ensure the MCP server is running (default: `http://127.0.0.1:3000/mcp`).
> 2. Ensure Ollama is installed and the model is pulled

## Single End-to-End Execution Metrics

## first pass 

| Event Name | Duration (s) | Metadata |
| :--- | :--- | :--- |
| Tool: get_option_data | 0.6579 | |
| Tool: calculate_delta | 0.1693 | |
| Tool: calculate_gamma | 0.1667 | |
| Tool: calculate_theta | 0.1695 | |
| Tool: calculate_vega | 0.1663 | |
| Tool: calculate_rho | 0.1699 | |
| **Total Agent Execution** | **12.1710** | |

## Async implementation for get_option_data

| Event Name | Duration (s) | Metadata |
| :--- | :--- | :--- |
| Tool: get_option_data | 0.7807 | |
| Tool: calculate_delta | 0.1679 | |
| Tool: calculate_gamma | 0.1667 | |
| Tool: calculate_theta | 0.1746 | |
| Tool: calculate_vega | 0.1681 | |
| Tool: calculate_rho | 0.1682 | |
| **Total Agent Execution** | **8.4329** | |
