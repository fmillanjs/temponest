#!/usr/bin/env python3
"""
SaaS Financial Calculator
Calculate revenue, profitability, and valuation for your SaaS idea
"""

import sys
from datetime import datetime
from typing import Dict, List

class SaaSCalculator:
    def __init__(
        self,
        product_name: str,
        pricing_tiers: Dict[str, float],  # {'starter': 29, 'pro': 99, 'business': 299}
        tier_distribution: Dict[str, float],  # {'starter': 0.6, 'pro': 0.3, 'business': 0.1}
        monthly_growth_rate: float = 0.20,  # 20% monthly growth
        churn_rate: float = 0.05,  # 5% monthly churn
        build_cost: float = 5000,  # Cost to build MVP
        monthly_costs: float = 500  # Server, tools, etc.
    ):
        self.product_name = product_name
        self.pricing_tiers = pricing_tiers
        self.tier_distribution = tier_distribution
        self.monthly_growth_rate = monthly_growth_rate
        self.churn_rate = churn_rate
        self.build_cost = build_cost
        self.monthly_costs = monthly_costs

        # Calculate average revenue per customer
        self.arpc = sum(
            price * dist
            for price, dist in zip(pricing_tiers.values(), tier_distribution.values())
        )

    def project_month(self, month: int, prev_customers: int = 0) -> Dict:
        """Project metrics for a specific month"""

        # Growth phases
        if month == 1:  # Launch month
            new_customers = 15
        elif month == 2:
            new_customers = 30
        elif month == 3:
            new_customers = 50
        else:
            # Apply growth rate after initial ramp
            new_customers = int(prev_customers * self.monthly_growth_rate)

        # Calculate churn
        churned = int(prev_customers * self.churn_rate)

        # Net customers
        total_customers = prev_customers + new_customers - churned

        # Revenue
        mrr = total_customers * self.arpc

        # Costs scale with customers (very roughly)
        costs = self.monthly_costs + (total_customers * 0.5)  # $0.50 per customer in infrastructure

        # Profit
        profit = mrr - costs

        return {
            'month': month,
            'new_customers': new_customers,
            'churned': churned,
            'total_customers': total_customers,
            'mrr': mrr,
            'costs': costs,
            'profit': profit,
            'cumulative_profit': 0  # Will be calculated
        }

    def project_timeline(self, months: int = 24) -> List[Dict]:
        """Project revenue and costs over time"""
        projections = []
        customers = 0
        cumulative_profit = -self.build_cost  # Start with build cost

        for month in range(1, months + 1):
            projection = self.project_month(month, customers)
            customers = projection['total_customers']
            cumulative_profit += projection['profit']
            projection['cumulative_profit'] = cumulative_profit
            projections.append(projection)

        return projections

    def calculate_valuation(self, arr: float) -> Dict[str, float]:
        """Calculate company valuation at different multiples"""
        return {
            'conservative_3x': arr * 3,
            'moderate_5x': arr * 5,
            'strong_8x': arr * 8,
            'exceptional_10x': arr * 10
        }

    def print_summary(self, months: int = 24):
        """Print comprehensive financial summary"""
        projections = self.project_timeline(months)

        month_12 = projections[11] if len(projections) >= 12 else projections[-1]
        month_24 = projections[-1]

        print(f"\n{'='*60}")
        print(f"  SaaS Financial Projection: {self.product_name}")
        print(f"{'='*60}\n")

        print("💰 PRICING:")
        for tier, price in self.pricing_tiers.items():
            pct = self.tier_distribution.get(tier, 0) * 100
            print(f"  {tier.title()}: ${price:.0f}/mo ({pct:.0f}% of customers)")
        print(f"  Average: ${self.arpc:.2f}/customer/month\n")

        print("📊 MONTH 12 PROJECTION:")
        print(f"  Customers: {month_12['total_customers']:,}")
        print(f"  MRR: ${month_12['mrr']:,.0f}")
        print(f"  ARR: ${month_12['mrr']*12:,.0f}")
        print(f"  Monthly Profit: ${month_12['profit']:,.0f}")
        print(f"  Cumulative Profit: ${month_12['cumulative_profit']:,.0f}\n")

        print("📈 MONTH 24 PROJECTION:")
        print(f"  Customers: {month_24['total_customers']:,}")
        print(f"  MRR: ${month_24['mrr']:,.0f}")
        print(f"  ARR: ${month_24['mrr']*12:,.0f}")
        print(f"  Monthly Profit: ${month_24['profit']:,.0f}")
        print(f"  Cumulative Profit: ${month_24['cumulative_profit']:,.0f}\n")

        # Valuation
        arr_24 = month_24['mrr'] * 12
        valuations = self.calculate_valuation(arr_24)

        print("💵 COMPANY VALUATION (Month 24):")
        for scenario, value in valuations.items():
            print(f"  {scenario}: ${value:,.0f}")

        # Total returns
        print(f"\n🎯 TOTAL RETURNS (24 months):")
        print(f"  Profit earned: ${month_24['cumulative_profit']:,.0f}")
        print(f"  + Exit (moderate 5x): ${valuations['moderate_5x']:,.0f}")
        print(f"  = Total: ${month_24['cumulative_profit'] + valuations['moderate_5x']:,.0f}\n")

        # ROI
        total_invested = self.build_cost + (self.monthly_costs * 24)
        roi = ((month_24['cumulative_profit'] + valuations['moderate_5x']) / total_invested) * 100

        print(f"💎 ROI:")
        print(f"  Investment: ${total_invested:,.0f}")
        print(f"  Return: {roi:,.0f}%\n")

        # Time investment (estimated)
        print(f"⏱️  TIME INVESTMENT:")
        print(f"  Build (8 weeks): ~100 hours")
        print(f"  Year 1 (maintenance): ~400 hours")
        print(f"  Year 2 (maintenance): ~500 hours")
        print(f"  Total: ~1000 hours")
        total_return = month_24['cumulative_profit'] + valuations['moderate_5x']
        hourly_rate = total_return / 1000
        print(f"  Effective rate: ${hourly_rate:,.0f}/hour\n")

        print(f"{'='*60}\n")

    def print_monthly_breakdown(self, months: int = 12):
        """Print month-by-month breakdown"""
        projections = self.project_timeline(months)

        print(f"\n{'Month':<6} {'Customers':<12} {'MRR':<12} {'Profit':<12} {'Cumulative':<12}")
        print("-" * 60)

        for p in projections:
            print(
                f"{p['month']:<6} "
                f"{p['total_customers']:<12} "
                f"${p['mrr']:<11,.0f} "
                f"${p['profit']:<11,.0f} "
                f"${p['cumulative_profit']:<11,.0f}"
            )

        print()


# Pre-defined scenarios
SCENARIOS = {
    'formbuilder': {
        'product_name': 'FormFlow (Form Builder)',
        'pricing_tiers': {'starter': 19, 'pro': 49, 'business': 99},
        'tier_distribution': {'starter': 0.6, 'pro': 0.3, 'business': 0.1},
        'monthly_growth_rate': 0.18,
        'churn_rate': 0.06,
        'build_cost': 5000,
        'monthly_costs': 300
    },
    'analytics': {
        'product_name': 'SimpleAnalytics (Web Analytics)',
        'pricing_tiers': {'starter': 29, 'pro': 79, 'business': 199},
        'tier_distribution': {'starter': 0.5, 'pro': 0.35, 'business': 0.15},
        'monthly_growth_rate': 0.15,
        'churn_rate': 0.05,
        'build_cost': 8000,
        'monthly_costs': 500
    },
    'crm': {
        'product_name': 'MicroCRM (Simple CRM)',
        'pricing_tiers': {'starter': 15, 'pro': 39, 'business': 89},
        'tier_distribution': {'starter': 0.7, 'pro': 0.25, 'business': 0.05},
        'monthly_growth_rate': 0.22,
        'churn_rate': 0.08,
        'build_cost': 6000,
        'monthly_costs': 400
    },
    'scheduler': {
        'product_name': 'QuickSchedule (Appointment Booking)',
        'pricing_tiers': {'starter': 25, 'pro': 59, 'business': 129},
        'tier_distribution': {'starter': 0.55, 'pro': 0.35, 'business': 0.1},
        'monthly_growth_rate': 0.20,
        'churn_rate': 0.06,
        'build_cost': 5000,
        'monthly_costs': 350
    },
    'emailbuilder': {
        'product_name': 'EmailCraft (Email Template Builder)',
        'pricing_tiers': {'starter': 19, 'pro': 49, 'business': 99},
        'tier_distribution': {'starter': 0.6, 'pro': 0.3, 'business': 0.1},
        'monthly_growth_rate': 0.16,
        'churn_rate': 0.07,
        'build_cost': 4500,
        'monthly_costs': 250
    }
}


def main():
    if len(sys.argv) > 1:
        scenario = sys.argv[1].lower()
        if scenario not in SCENARIOS:
            print(f"Unknown scenario: {scenario}")
            print(f"Available: {', '.join(SCENARIOS.keys())}")
            sys.exit(1)

        calc = SaaSCalculator(**SCENARIOS[scenario])
    else:
        # Interactive mode
        print("\n🚀 SaaS Financial Calculator\n")
        print("Available scenarios:")
        for i, (key, scenario) in enumerate(SCENARIOS.items(), 1):
            print(f"  {i}. {key} - {scenario['product_name']}")
        print("  c. Custom")

        choice = input("\nSelect scenario (number or 'c'): ").strip()

        if choice.lower() == 'c':
            # Custom scenario
            product_name = input("Product name: ")
            starter = float(input("Starter price ($/mo): "))
            pro = float(input("Pro price ($/mo): "))
            business = float(input("Business price ($/mo): "))

            calc = SaaSCalculator(
                product_name=product_name,
                pricing_tiers={'starter': starter, 'pro': pro, 'business': business},
                tier_distribution={'starter': 0.6, 'pro': 0.3, 'business': 0.1}
            )
        else:
            try:
                idx = int(choice) - 1
                scenario_name = list(SCENARIOS.keys())[idx]
                calc = SaaSCalculator(**SCENARIOS[scenario_name])
            except (ValueError, IndexError):
                print("Invalid choice")
                sys.exit(1)

    # Print projections
    calc.print_summary(24)

    # Ask if want monthly breakdown
    if '--monthly' in sys.argv or input("\nShow monthly breakdown? (y/n): ").lower() == 'y':
        calc.print_monthly_breakdown(24)


if __name__ == '__main__':
    main()
