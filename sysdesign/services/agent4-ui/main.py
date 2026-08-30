# ui_usability_agent/main.py

import json
import os
import argparse
import shutil
from generator.ui_generator import generate_ui
from input_normalizer import normalize_input
from screen_planner import plan_screens, screens_to_requirements, save_screen_plan
from evaluator.composite_scorer import evaluate, print_score_report, save_score_report

def run_planning_phase():
    """
    Loads requirements, normalizes them, and generates the screen plan.
    Also cleans up old generated screens.
    """
    print("Starting screen planning phase...")

    # 1. Clean up old generated screens to avoid confusion
    output_dir = os.path.join(os.path.dirname(__file__), "outputs", "generated_screens")
    if os.path.exists(output_dir):
        print(f"[main] Cleaning up old screens in {output_dir}...")
        try:
            shutil.rmtree(output_dir)
        except PermissionError:
            print(f"[main] Warning: Could not clean up {output_dir} (directory may be in use). Continuing anyway.")

    # 2. Load raw requirements
    requirements_path = os.path.join(os.path.dirname(__file__), "samples", "sample_requirements.json")
    print(f"\n[main] Loading requirements from: {requirements_path}")
    try:
        with open(requirements_path, "r", encoding="utf-8") as f:
            raw_requirements = json.load(f)
    except FileNotFoundError:
        print(f"\n[main] Error: Requirements file not found at {requirements_path}")
        print("Please ensure the file exists and contains your system requirements.")
        return

    # 3. Normalize the input
    print("[main] Normalizing inputs...")
    normalized_requirements = normalize_input(raw_requirements)

    # 4. Plan all the screens
    print("[main] Planning screens with LLM...")
    screens = plan_screens(normalized_requirements)
    
    if not screens:
        print("\n[main] Halting: No screens were planned. Check screen_planner.py logs for errors.")
        return
        
    save_screen_plan(screens)
    print("\nPlanning complete. You can now generate individual screens using:")
    print("python main.py --generate <screen_number_or_id>")


def run_generation_phase(screen_identifier: str):
    """
    Generates the UI for a single, specified screen by ID or by number.
    """
    print(f"Starting generation for screen: '{screen_identifier}'...")

    # 1. Load the existing screen plan
    plan_path = os.path.join(os.path.dirname(__file__), "outputs", "screen_plan.json")
    print(f"\n[main] Loading screen plan from: {plan_path}")
    try:
        with open(plan_path, "r", encoding="utf-8") as f:
            screens = json.load(f)
    except FileNotFoundError:
        print(f"\n[main] Error: Screen plan not found at {plan_path}")
        print("Please run the planning phase first with: python main.py --plan")
        return

    # 2. Find the specific screen to generate by number or by ID
    target_screen = None
    if screen_identifier.isdigit():
        try:
            screen_index = int(screen_identifier) - 1
            if 0 <= screen_index < len(screens):
                target_screen = screens[screen_index]
            else:
                print(f"\n[main] Error: Invalid screen number '{screen_identifier}'. Please choose a number between 1 and {len(screens)}.")
                return
        except (ValueError, IndexError):
            pass # Fallback to searching by ID
            
    if not target_screen:
        target_screen = next((s for s in screens if s.get("screen_id") == screen_identifier), None)

    if not target_screen:
        print(f"\n[main] Error: Screen '{screen_identifier}' not found in the screen plan.")
        print("Available screens (use number or ID):")
        for i, s in enumerate(screens, 1):
            print(f"  {i}. {s.get('screen_id')}")
        return

    # 3. Load the base requirements to get full context
    requirements_path = os.path.join(os.path.dirname(__file__), "samples", "sample_requirements.json")
    with open(requirements_path, "r", encoding="utf-8") as f:
        raw_requirements = json.load(f)
    normalized_requirements = normalize_input(raw_requirements)

    # 4. Prepare the requirements for just this one screen
    per_screen_reqs = screens_to_requirements([target_screen], normalized_requirements)
    
    if not per_screen_reqs:
        print("\n[main] Error: Could not prepare requirements for the selected screen.")
        return
        
    screen_req = per_screen_reqs[0]
    screen_id = screen_req.get("screen_id", "unknown_screen")
    screen_name = screen_req.get("screen_name", "Unknown Screen")
    screen_type = screen_req.get("screen_type", "unknown")

    # 5. Generate the UI
    print(f"\n[main] Generating UI for '{screen_name}' ({screen_id}) of type '{screen_type}'...")
    generated_html = generate_ui(screen_req, screen_type)

    # 6. Save the generated HTML
    output_dir = os.path.join(os.path.dirname(__file__), "outputs", "generated_screens")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{screen_id}.html")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(generated_html)

    print("\nGeneration complete!")
    print(f"Generated file: {output_path}")


def run_evaluation_phase():
    """
    Evaluates all generated screens in outputs/generated_screens/.
    """
    screens_dir = os.path.join(os.path.dirname(__file__), "outputs", "generated_screens")
    reports_dir = os.path.join(os.path.dirname(__file__), "outputs", "score_reports")
    # Clean up old reports
    if os.path.exists(reports_dir):
        print(f"[main] Cleaning up old reports in {reports_dir}...")
        try:
            shutil.rmtree(reports_dir)
        except PermissionError:
            print(f"[main] Warning: Could not clean up {reports_dir} (directory may be in use). Continuing anyway.")
    os.makedirs(reports_dir, exist_ok=True)

    if not os.path.exists(screens_dir):
        print(f"Error: {screens_dir} not found. Please generate screens first.")
        return

    html_files = [f for f in os.listdir(screens_dir) if f.endswith('.html')]
    if not html_files:
        print(f"No HTML files found in {screens_dir}.")
        return

    print(f"Evaluating {len(html_files)} screens...")

    for html_file in html_files:
        html_path = os.path.join(screens_dir, html_file)
        screen_name = html_file.replace('.html', '')

        print(f"\n=== Evaluating {screen_name} ===")

        with open(html_path, 'r', encoding='utf-8') as f:
            html_string = f.read()

        report = evaluate(html_string, iteration_number=1)
        print_score_report(report)

        # Save individual report
        report_path = os.path.join(reports_dir, f"{screen_name}_score_report.json")
        save_score_report(report, report_path)
        print(f"Report saved to {report_path}")


def main():
    """
    Main entry point to handle command-line arguments for planning, generation, and evaluation.
    """
    parser = argparse.ArgumentParser(description="UI Generation, Planning, and Evaluation Tool")
    parser.add_argument(
        '--plan',
        action='store_true',
        help="Run the screen planning phase. Creates outputs/screen_plan.json."
    )
    parser.add_argument(
        '--generate',
        type=str,
        metavar='SCREEN_ID',
        help="Run the generation phase for a specific screen ID from the plan."
    )
    parser.add_argument(
        '--evaluate',
        action='store_true',
        help="Run the evaluation phase on all generated screens in outputs/generated_screens/."
    )

    args = parser.parse_args()

    if args.plan:
        run_planning_phase()
    elif args.generate:
        run_generation_phase(args.generate)
    elif args.evaluate:
        run_evaluation_phase()
    else:
        parser.print_help()
        print("\nExample Usage:")
        print("1. Plan all screens: python main.py --plan")
        print("2. Generate a single screen: python main.py --generate login")
        print("3. Evaluate all generated screens: python main.py --evaluate")


if __name__ == "__main__":
    main()





