"""CLI for grading CS assignments."""
import os
import zipfile
import csv
from pathlib import Path
import logging
from tqdm import tqdm
import typer
from typing import Optional, List, Dict, Any, NamedTuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue
import sys
import time  # For simulating work in progress bar

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = typer.Typer(help="Grade CS assignments with detailed feedback.")

@dataclass
class SubmissionFile:
    """Represents a single file in a submission."""
    filename: str
    content: str

@dataclass
class Submission:
    """Represents a complete submission with metadata."""
    student_name: str
    files: List[SubmissionFile]
    original_path: Path

@dataclass
class GradingResult:
    """Represents the raw result of grading a submission."""
    student_name: str
    final_score: int
    max_points: int
    code_quality: str
    requirements_assessment: List[Dict[str, Any]]
    point_deductions: List[Dict[str, Any]]
    extra_credit: Dict[str, Any]
    overall_assessment: str
    improvement_suggestions: List[str]

@dataclass
class FormattedResult:
    """Represents a grading result formatted for output."""
    student_name: str
    final_score: str
    code_quality: str
    requirements_analysis: str
    point_deductions: str
    extra_credit: str
    overall_assessment: str
    areas_for_improvement: str

class ThreadSafeWriter:
    """Thread-safe file writer using a lock."""
    
    def __init__(self):
        self._lock = threading.Lock()
    
    def write_safely(self, file_path: Path, mode: str, write_func):
        """Execute a write function with thread safety."""
        with self._lock:
            with open(file_path, mode) as f:
                return write_func(f)

class SubmissionProcessor:
    """Handles discovering and processing submission files."""
    
    def __init__(self):
        self._file_lock = threading.Lock()
    
    @staticmethod
    def extract_student_name(filename: str) -> str:
        """Extract student's name from filename."""
        return Path(filename).stem.replace('_', ' ')
    
    def process_java_file(self, file_path: Path) -> List[SubmissionFile]:
        """Process a single Java file with thread safety."""
        with self._file_lock:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return [SubmissionFile(filename=file_path.name, content=content)]
    
    def process_zip_file(self, file_path: Path) -> List[SubmissionFile]:
        """Process a zip file containing Java files with thread safety."""
        files = []
        with self._file_lock:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    if file_info.filename.endswith('.java'):
                        with zip_ref.open(file_info) as f:
                            content = f.read().decode('utf-8')
                            files.append(SubmissionFile(
                                filename=file_info.filename,
                                content=content
                            ))
        return files
    
    def find_submissions(self, directory: Path) -> List[Submission]:
        """Find all valid submissions in directory."""
        submissions = []
        for file_path in directory.glob('*'):
            if not (file_path.suffix in ['.java', '.zip']):
                continue
                
            student_name = self.extract_student_name(file_path.name)
            
            try:
                if file_path.suffix == '.zip':
                    files = self.process_zip_file(file_path)
                else:
                    files = self.process_java_file(file_path)
                
                submissions.append(Submission(
                    student_name=student_name,
                    files=files,
                    original_path=file_path
                ))
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
        
        return submissions

class ResultFormatter:
    """Handles formatting grading results for output."""
    
    @staticmethod
    def format_requirements(requirements: List[Dict[str, Any]]) -> str:
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
    
    @classmethod
    def format_result(cls, result: GradingResult) -> FormattedResult:
        """Format a grading result for output."""
        # Format point deductions
        deductions_text = "\n".join(
            f"- {d['reason']} (-{d['points']} points)" 
            for d in result.point_deductions
        ) if result.point_deductions else "No points deducted"
        
        # Format extra credit
        extra_credit_text = (
            f"+{result.extra_credit['points']} points: {result.extra_credit['reason']}"
            if result.extra_credit['awarded']
            else "No extra credit awarded"
        )
        
        return FormattedResult(
            student_name=result.student_name,
            final_score=f"{result.final_score}/{result.max_points}",
            code_quality=result.code_quality,
            requirements_analysis=cls.format_requirements(result.requirements_assessment),
            point_deductions=deductions_text,
            extra_credit=extra_credit_text,
            overall_assessment=result.overall_assessment,
            areas_for_improvement="\n- " + "\n- ".join(result.improvement_suggestions)
        )

class ResultWriter:
    """Handles writing formatted results to CSV."""
    
    def __init__(self):
        self._writer = ThreadSafeWriter()
    
    def write_results(self, results: List[FormattedResult], output_path: Path) -> None:
        """Write formatted results to CSV file with thread safety."""
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
        
        rows = [
            {
                'Student Name': r.student_name,
                'Final Score': r.final_score,
                'Code Quality Assessment': r.code_quality,
                'Requirements Analysis': r.requirements_analysis,
                'Point Deductions': r.point_deductions,
                'Extra Credit': r.extra_credit,
                'Overall Assessment': r.overall_assessment,
                'Areas for Improvement': r.areas_for_improvement
            }
            for r in results
        ]
        
        def write_csv(f):
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        self._writer.write_safely(output_path, 'w', write_csv)
        logger.info(f"Results written to {output_path}")

class Grader:
    """Coordinates the grading process."""
    
    def __init__(self, guidelines: str, max_points: int):
        self.guidelines = guidelines
        self.max_points = max_points
    
    def grade_submission(self, submission: Submission) -> GradingResult:
        """Grade a single submission."""
        try:
            from grader import grade_assignment
            
            # Convert submission files to format expected by grader
            files = [(f.filename, f.content) for f in submission.files]
            
            # Grade the submission
            result = grade_assignment(
                files=files,
                guidelines=self.guidelines,
                student_comment="",
                max_points=self.max_points
            )
            
            return GradingResult(
                student_name=submission.student_name,
                final_score=result['final_score'],
                max_points=self.max_points,
                code_quality=result['code_quality'],
                requirements_assessment=result['requirements_assessment'],
                point_deductions=result['point_deductions'],
                extra_credit=result['extra_credit'],
                overall_assessment=result['overall_assessment'],
                improvement_suggestions=result['improvement_suggestions']
            )
            
        except Exception as e:
            logger.error(f"Error grading submission for {submission.student_name}: {str(e)}")
            return GradingResult(
                student_name=submission.student_name,
                final_score=0,
                max_points=self.max_points,
                code_quality="Error during grading",
                requirements_assessment=[],
                point_deductions=[],
                extra_credit={'awarded': False, 'points': 0, 'reason': ''},
                overall_assessment="Failed to grade submission",
                improvement_suggestions=["Please resubmit or contact instructor"]
            )

@app.command()
def grade(
    submissions_dir: str = typer.Argument(..., help="Directory containing student submissions (.java or .zip files)"),
    guidelines_path: str = typer.Argument(..., help="Path to the assignment requirements file"),
    max_points: Optional[int] = typer.Option(100, help="Maximum points possible for the assignment"),
    threads: Optional[int] = typer.Option(1, help="Number of threads to use for parallel grading"),
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
    # Validate inputs
    submissions_path = Path(submissions_dir)
    if not submissions_path.is_dir():
        typer.echo(f"Error: {submissions_dir} is not a valid directory")
        raise typer.Exit(1)
    
    guidelines_path = Path(guidelines_path)
    if not guidelines_path.is_file():
        typer.echo(f"Error: {guidelines_path} is not a valid file")
        raise typer.Exit(1)
    
    if max_points <= 0:
        typer.echo("Error: max_points must be positive")
        raise typer.Exit(1)
        
    if threads <= 0:
        typer.echo("Error: threads must be positive")
        raise typer.Exit(1)
    
    # Set default output path if not provided
    output_path = Path(output) if output else submissions_path.parent / 'grading_results.csv'
    
    # Read guidelines
    with open(guidelines_path, 'r', encoding='utf-8') as f:
        guidelines = f.read()
    
    # Find all submissions
    typer.echo("Finding submissions...")
    submission_processor = SubmissionProcessor()
    submissions = submission_processor.find_submissions(submissions_path)
    
    if not submissions:
        typer.echo("No valid submissions found.")
        raise typer.Exit(1)
    
    # Create grader and result writer
    grader = Grader(guidelines, max_points)
    writer = ResultWriter()
    
    # Create result queue for thread safety
    result_queue = Queue()
    
    # Create progress bar
    progress_bar = tqdm(total=len(submissions), desc="Grading")
    progress_lock = threading.Lock()
    
    def process_submission(submission: Submission):
        """Process a single submission with progress tracking."""
        try:
            result = grader.grade_submission(submission)
            formatted_result = ResultFormatter.format_result(result)
            result_queue.put(formatted_result)
        except Exception as e:
            logger.error(f"Error processing {submission.student_name}: {str(e)}")
        finally:
            with progress_lock:
                progress_bar.update(1)
    
    # Grade submissions using thread pool
    typer.echo(f"Grading submissions using {threads} threads...")
    
    with ThreadPoolExecutor(max_workers=threads) as executor:
        # Submit all grading tasks
        futures = [
            executor.submit(process_submission, submission)
            for submission in submissions
        ]
        
        # Wait for all tasks to complete
        for future in futures:
            future.result()  # This ensures we catch any exceptions
    
    # Close progress bar
    progress_bar.close()
    
    # Collect all results from queue
    results = []
    while not result_queue.empty():
        results.append(result_queue.get())
    
    # Sort results by student name for consistency
    results.sort(key=lambda x: x.student_name)
    
    # Write results
    typer.echo("Writing results...")
    writer.write_results(results, output_path)
    typer.echo(f"Grading completed! Results saved to: {output_path}")

if __name__ == "__main__":
    app()
