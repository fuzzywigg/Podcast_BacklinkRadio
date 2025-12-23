# Model Context Protocol (MCP) Unsigned Transaction Flow – 2025 Best Practice

Fully non-custodial, open standard (MCP v1.2 – Apache 2.0).

## Why MCP?
- **Agent never touches private keys.**
- User signs with WalletConnect / embedded wallet / hardware.
- Works with any EVM chain + Solana (via plugins).

## Exact Flow

1.  **Agent Action**: Agent decides to execute an on-chain action (e.g., "Refund User").
2.  **Construction**: Agent builds the raw transaction object using `Viem` or `ethers` (encodeFunctionData).
3.  **Encapsulation**: Agent serializes tx + chainId + metadata into an MCP envelope:
    ```json
    {
      "mcpVersion": "1.2",
      "chainId": 8453,
      "unsignedTx": {
        "from": "0xUserAddress...",
        "to": "0xContract...",
        "data": "0x1234...",
        "value": "0x0",
        "gas": "0x52080",
        "maxFeePerGas": "0x19bf35e00",
        "maxPriorityFeePerGas": "0x77359400",
        "nonce": 42
      },
      "intent": "Swap 100 USDC -> ETH on Base via Uniswap v3",
      "agentId": "swarm-executor-07"
    }
    ```
4.  **Delivery**: Agent returns ONLY the envelope + human-readable summary to the orchestrator/frontend.
5.  **User Signing**: Frontend/App presents the envelope to the user's wallet (WalletConnect v2, RainbowKit, Coinbase Smart Wallet).
6.  **Broadcast**: User reviews & signs. The wallet returns the *signed* raw tx.
7.  **Execution**: Orchestrator broadcasts via public RPC (Alchemy, Infura, or swarm-operated node).
8.  **Verification**: Agent polls for the transaction receipt and confirms success.

## Payment Path Selection (Dynamic)
For user-facing payments, the agent dynamically selects the path with the lowest latency/highest uptime:
1.  **Coinbase Onramp** (iFrame) - Priority 1
2.  **WalletConnect / Web3Modal** (Direct Crypto) - Priority 2
3.  **Stripe** (Fiat Backup) - Priority 3 (Last Resort)

*Note: If a provider fails (e.g., 502 error), the agent fails over to the next option within 30 seconds.*
