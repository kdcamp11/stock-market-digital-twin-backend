"""
Example: Use the StockAgent to answer a plain-language question about a stock.
"""
from agent import StockAgent

if __name__ == "__main__":
    agent = StockAgent()
    questions = [
        "Should I buy AAPL now?",
        "Is it time to sell TSLA?",
        "What about MSFT?",
        "Give me a trade decision for all stocks."
    ]
    for q in questions:
        print(f"\nQuestion: {q}")
        result = agent.decide(q)
        print("Result:", result)
