#!/usr/bin/env python3
"""
Test script for the evaluation engine.
Reads all HTML files in outputs/generated_screens/ and evaluates each one.
"""

import os
from evaluator.composite_scorer import evaluate, print_score_report, save_score_report

def main():
    screens_dir = "outputs/generated_screens"
    if not os.path.exists(screens_dir):
        print(f"Error: {screens_dir} not found. Please generate screens first.")
        return

    html_files = [f for f in os.listdir(screens_dir) if f.endswith('.html')]
    if not html_files:
        print(f"No HTML files found in {screens_dir}.")
        return

    for html_file in html_files:
        html_path = os.path.join(screens_dir, html_file)
        screen_name = html_file.replace('.html', '')

        print(f"\n=== Evaluating {screen_name} ===")

        with open(html_path, 'r', encoding='utf-8') as f:
            html_string = f.read()

        report = evaluate(html_string, iteration_number=1)
        print_score_report(report)

        # Save individual report
        report_path = f"outputs/{screen_name}_score_report.json"
        save_score_report(report, report_path)
        print(f"Report saved to {report_path}")

if __name__ == "__main__":
    main()