"""Batch grader for CS assignments."""
import os
import zipfile
import csv
from pathlib import Path
import logging
from tqdm import tqdm
import typer
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = typer.Typer(help="Batch grade CS assignments with detailed feedback.")

def extract_student_name(filename):
    """Extract student's name from filename."""
    base_name = Path(filename).stem
    return base_name.replace('_', ' ')

def process_java_file(file_path):
    """Process a single Java file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return [(Path(file_path).name, content)]

def process_zip_file(file_path):
    """Process a zip file containing Java files."""
    files = []
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        for file_info in zip_ref.infolist():
            if file_info.filename.endswith('.java'):
                with zip_ref.open(file_info) as f:
                    content = f.read().decode('utf-8')
                    files.append((file_info.filename, content))
    return files

def format_requirements(requirements):
    """Format requirements assessment into a readable string."""
    met_reqs = [req for req in requirements if req['met']]
    unmet_reqs = [req for req in requirements if not req['met']]
    
    result = []
    if met_reqs:
        result.append("Requirements met:\n- " + "\n- ".join(
            f"{req['requirement']}" for req in met_reqs
        ))
    if unmet_reqs:
        result.append("Requirements not met:\n- " + "\n- ".join(
            f"{req['requirement']}: {req['explanation']}" for req in unmet_reqs
        ))
    return "\n\n".join(result)

def grade_submissions(submissions_dir: str, guidelines_path: str, max_points: int):
    """Grade all submissions in the given directory."""
    # Read guidelines
    with open(guidelines_path, 'r', encoding='utf-8') as f:
        guidelines = f.read()
    
    results = []
    
    # Get list of valid files
    valid_files = [f for f in os.listdir(submissions_dir) 
                  if f.endswith(('.java', '.zip'))]
    
    if not valid_files:
        logger.warning("No .java or .zip files found in the selected directory.")
        return []
    
    # Process all files with tqdm progress bar
    for filename in tqdm(valid_files, desc="Grading submissions"):
        file_path = os.path.join(submissions_dir, filename)
        student_name = extract_student_name(filename)
        logger.info(f"Processing submission for {student_name}")
        
        try:
            # Process file based on type
            if filename.endswith('.zip'):
                files = process_zip_file(file_path)
            else:
                files = process_java_file(file_path)
            
            # Grade the submission
            from grader import grade_assignment
            grade_result = grade_assignment(
                files=files,
                guidelines=guidelines,
                student_comment="",  # No student comments in batch processing
                max_points=max_points
            )
            
            # Format point deductions into readable text
            deductions_text = "\n".join(
                f"- {d['reason']} (-{d['points']} points)" 
                for d in grade_result['point_deductions']
            )
            
            # Format extra credit explanation
            extra_credit_text = (
                f"+{grade_result['extra_credit']['points']} points: {grade_result['extra_credit']['reason']}"
                if grade_result['extra_credit']['awarded']
                else "No extra credit awarded"
            )
            
            # Add student info to result with detailed feedback
            result = {
                'Student Name': student_name,
                'Final Score': f"{grade_result['final_score']}/{max_points}",
                'Code Quality Assessment': grade_result['code_quality'],
                'Requirements Analysis': format_requirements(grade_result['requirements_assessment']),
                'Point Deductions': deductions_text if grade_result['point_deductions'] else "No points deducted",
                'Extra Credit': extra_credit_text,
                'Overall Assessment': grade_result['overall_assessment'],
                'Areas for Improvement': "\n- " + "\n- ".join(grade_result['improvement_suggestions'])
            }
            
            results.append(result)
            logger.info(f"Completed grading for {student_name}")
            
        except Exception as e:
            logger.error(f"Error processing submission for {student_name}: {str(e)}")
            results.append({
                'Student Name': student_name,
                'Final Score': f"0/{max_points}",
                'Code Quality Assessment': "Error during grading",
                'Requirements Analysis': "Error during grading",
                'Point Deductions': "Error during grading",
                'Extra Credit': "N/A",
                'Overall Assessment': "Failed to grade submission",
                'Areas for Improvement': "Please resubmit or contact instructor"
            })
    
    return results

def write_results_to_csv(results, output_path):
    """Write grading results to CSV file."""
    if not results:
        logger.warning("No results to write to CSV")
        return
        
    fieldnames = [
        'Student Name',
        'Final Score',
        'Code Quality Assessment',
        'Requirements Analysis',
        'Point Deductions',
        'Extra Credit',
        'Overall Assessment',
        'Areas for Improvement'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Results written to {output_path}")

@app.command()
def grade(
    submissions_dir: str = typer.Argument(..., help="Directory containing student submissions (.java or .zip files)"),
    guidelines_path: str = typer.Argument(..., help="Path to the assignment requirements file"),
    max_points: Optional[int] = typer.Option(100, help="Maximum points possible for the assignment"),
    output: Optional[str] = typer.Option(
        None,
        help="Output CSV file path. If not provided, will save as grading_results.csv in the submissions directory"
    )
):
    """
    Grade all Java assignments in a directory and generate a detailed feedback CSV.
    
    The CSV will include qualitative feedback about:
    - Requirements met and unmet
    - Code quality assessment
    - Specific point deductions with explanations
    - Areas for improvement
    """
    if not os.path.isdir(submissions_dir):
        typer.echo(f"Error: {submissions_dir} is not a valid directory")
        raise typer.Exit(1)
    
    if not os.path.isfile(guidelines_path):
        typer.echo(f"Error: {guidelines_path} is not a valid file")
        raise typer.Exit(1)
    
    if max_points <= 0:
        typer.echo("Error: max_points must be positive")
        raise typer.Exit(1)
    
    # Set default output path if not provided
    if output is None:
        output = os.path.join(os.path.dirname(submissions_dir), 'grading_results.csv')
    
    typer.echo(f"Starting grading process...")
    results = grade_submissions(submissions_dir, guidelines_path, max_points)
    
    if results:
        write_results_to_csv(results, output)
        typer.echo(f"Grading completed! Results saved to: {output}")
    else:
        typer.echo("No submissions were processed.")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
